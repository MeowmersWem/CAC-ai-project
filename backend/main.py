
from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
import firebase_admin
from firebase_admin import credentials, firestore, auth
import random
import string
import datetime
import json
import os
import requests
from typing import Dict, List
import uuid
from dotenv import load_dotenv
from fastapi import UploadFile
import base64
import PyPDF2
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Use Application Default Credentials in Cloud Run
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            print("✅ Using Application Default Credentials")
        else:
            # Local development
            if os.path.exists("serviceAccountKey.json"):
                cred = credentials.Certificate("serviceAccountKey.json")
                firebase_admin.initialize_app(cred)
                print("✅ Using service account key")
        
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        raise

db = firestore.client()
app = FastAPI(title="Classroom API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# -------------------------------
# Pydantic Models
# -------------------------------

# Auth Models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    university: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: str

class AuthResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    token: str

# Class Models
class JoinClassRequest(BaseModel):
    class_code: str

class ClassResponse(BaseModel):
    class_id: str
    name: str
    code: str
    created_by: str
    created_at: str
    join_mode: str
    visibility: str

class CreatePostRequest(BaseModel):
    title: str
    content: str
    post_type: str  # "question", "announcement", "discussion", etc.
    tags: List[str] = []
    files: List[str] = []  # File URLs/paths

class PostResponse(BaseModel):
    post_id: str
    title: str
    content: str
    post_type: str
    tags: List[str]
    author_id: str
    author_name: str
    created_at: str
    files: List[str]

class AIStudyRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    class_context: Optional[str] = None  # Can include class name, recent posts, etc.

class AIStudyResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, str]]
    class_id: Optional[str] = None
    user_id: str
    created_at: str
    last_updated: str

class AIStudyWithFilesRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    class_context: Optional[str] = None
    file_types: List[str] = []  # Track what types of files were uploaded


class NoteSummaryRequest(BaseModel):
    title: Optional[str] = None
    class_id: Optional[str] = None

class NoteSummary(BaseModel):
    summary_id: str
    title: str
    key_concepts: List[str]
    main_points: List[str]
    study_tips: List[str]
    questions_for_review: List[str]
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    estimated_study_time: str  # "30 minutes", "1 hour", etc.
    created_at: str
    file_sources: List[str]  # Original filenames
    class_id: Optional[str] = None
    user_id: str

class SummaryResponse(BaseModel):
    summary: NoteSummary
    raw_content_preview: str  # First 200 chars of original content
    
# -------------------------------
# Auth Dependencies
# -------------------------------
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and verify Firebase ID token from Authorization header"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

# Mock auth for development/testing
async def mock_get_current_user():
    """Mock user for testing - replace with real auth in production"""
    return {
        'uid': 'test_user_id',
        'email': 'test@example.com',
        'name': 'Test User'
    }

# -------------------------------
# Utility Functions
# -------------------------------
def generate_class_code(length: int = 6) -> str:
    """Generate a class join code like 'ABC123'"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def serialize_datetime(obj):
    """Convert datetime objects to ISO string for JSON serialization"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj

def get_ai_response(conversation_history: List[Dict], api_key: str, class_context: str = None) -> str:
    """Get AI response from OpenAI API with classroom context"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Enhance system prompt with class context if available
    system_message = conversation_history[0].copy()
    if class_context:
        system_message["content"] += f"\n\nClass Context: {class_context}"
    
    # Update the conversation with enhanced context
    enhanced_history = [system_message] + conversation_history[1:]
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": enhanced_history,
        "max_tokens": 300,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

def get_class_context(class_id: str, db) -> str:
    """Get recent class context for AI conversations"""
    try:
        # Get class info
        class_doc = db.collection("classes").document(class_id).get()
        if not class_doc.exists:
            return ""
        
        class_data = class_doc.to_dict()
        class_name = class_data.get("name", "")
        
        # Get recent posts for context (last 3 posts)
        recent_posts = (db.collection("classes").document(class_id)
                       .collection("posts")
                       .order_by("createdAt", direction=firestore.Query.DESCENDING)
                       .limit(3)
                       .stream())
        
        context = f"Class: {class_name}\n"
        context += "Recent discussion topics:\n"
        
        for post in recent_posts:
            post_data = post.to_dict()
            context += f"- {post_data.get('title', 'Untitled')}: {post_data.get('post_type', 'discussion')}\n"
        
        return context
    except Exception:
        return ""
    
def get_ai_response_with_files(conversation_history: List[Dict], api_key: str, 
                               files_content: List[Dict] = None, class_context: str = None) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Enhance system prompt for file analysis
    system_message = conversation_history[0].copy()
    if files_content:
        system_message["content"] += "\n\nYou can analyze uploaded files (PDFs and images). When files are provided, analyze their content and help the student understand the material through guiding questions."
    
    if class_context:
        system_message["content"] += f"\n\nClass Context: {class_context}"
    
    enhanced_history = [system_message] + conversation_history[1:]
    
    # Add file content to the last user message if files were provided
    if files_content and enhanced_history:
        last_message = enhanced_history[-1]
        if last_message.get("role") == "user":
            # For OpenAI GPT-4 Vision API
            if any(f["type"] == "image" for f in files_content):
                last_message["content"] = [
                    {"type": "text", "text": last_message["content"]}
                ] + files_content
            else:
                # For text content from PDFs
                text_content = "\n\n".join([f["content"] for f in files_content if f["type"] == "text"])
                last_message["content"] += f"\n\nFile content:\n{text_content}"
    
    data = {
        "model": "gpt-4-vision-preview" if any(f.get("type") == "image" for f in files_content or []) else "gpt-3.5-turbo",
        "messages": enhanced_history,
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

# File processing functions
def extract_pdf_text(pdf_file: UploadFile) -> str:
    pdf_reader = PyPDF2.PdfReader(pdf_file.file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def process_image(image_file: UploadFile) -> str:
    image_bytes = image_file.file.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/{image_file.filename.split('.')[-1]};base64,{base64_image}"    

def get_structured_summary(file_content: str, api_key: str, user_title: str = None) -> dict:
    """Get structured JSON summary from OpenAI"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    user_message = f"Analyze and summarize this content:\n\n{file_content[:3000]}"  # Limit content length
    if user_title:
        user_message = f"Title: {user_title}\n\n{user_message}"
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 800,
        "temperature": 0.3  # Lower temperature for more consistent JSON
    }
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        ai_response = result["choices"][0]["message"]["content"].strip()
        
        # Parse JSON response
        try:
            summary_data = json.loads(ai_response)
            return summary_data
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from response if AI added extra text
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
                
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary processing error: {str(e)}")



# -------------------------------
# AUTH ENDPOINTS
# -------------------------------
@app.post("/api/v1/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """Register new user account"""
    try:
        # Create Firebase user
        user_record = auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.full_name
        )
        
        # Create user profile in Firestore
        user_data = {
            "email": request.email,
            "full_name": request.full_name,
            "university": request.university,
            "created_at": datetime.datetime.utcnow(),
            "karma": 0
        }
        db.collection("users").document(user_record.uid).set(user_data)
        
        # Generate custom token for immediate login
        custom_token = auth.create_custom_token(user_record.uid)
        
        return AuthResponse(
            user_id=user_record.uid,
            email=request.email,
            full_name=request.full_name,
            token=custom_token.decode('utf-8')
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Authenticate user login"""
    # Note: Firebase Admin SDK doesn't handle password authentication directly
    # You'll need to use Firebase Auth REST API or handle this on the frontend
    # This is a placeholder implementation
    try:
        # In a real implementation, you'd verify credentials via Firebase Auth REST API
        # or handle this entirely on the frontend
        user = auth.get_user_by_email(request.email)
        custom_token = auth.create_custom_token(user.uid)
        
        # Get user profile
        user_doc = db.collection("users").document(user.uid).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}
        
        return {
            "user_id": user.uid,
            "email": user.email,
            "full_name": user_data.get("full_name", ""),
            "token": custom_token.decode('utf-8')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/v1/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Google OAuth authentication"""
    try:
        decoded_token = auth.verify_id_token(request.id_token)
        uid = decoded_token['uid']
        
        # Check if user exists, create if not
        user_doc = db.collection("users").document(uid).get()
        if not user_doc.exists:
            user_data = {
                "email": decoded_token.get('email', ''),
                "full_name": decoded_token.get('name', ''),
                "university": "",  # User can update this later
                "created_at": datetime.datetime.utcnow(),
                "karma": 0
            }
            db.collection("users").document(uid).set(user_data)
        else:
            user_data = user_doc.to_dict()
        
        return AuthResponse(
            user_id=uid,
            email=decoded_token.get('email', ''),
            full_name=user_data.get('full_name', ''),
            token=request.id_token
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")

@app.post("/api/v1/auth/signout")
async def signout(current_user: dict = Depends(mock_get_current_user)):
    """Sign out current user"""
    # In Firebase, sign out is typically handled on the frontend
    # Backend can revoke tokens if needed
    try:
        auth.revoke_refresh_tokens(current_user['uid'])
        return {"message": "Successfully signed out"}
    except Exception as e:
        return {"message": "Signed out (token revocation failed)"}

# -------------------------------
# AI STUDY BOT ENDPOINTS
# -------------------------------

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
STUDY_BUDDY_SYSTEM_PROMPT = """You are an AI Study Buddy for a classroom discussion platform. Your role is to help students learn by:

1. Asking guiding questions instead of giving direct answers
2. Encouraging critical thinking and exploration
3. Relating topics to the class context when provided
4. Being supportive and encouraging
5. Suggesting study strategies and learning approaches

When a student asks a question:
- Ask a guiding question back to help them think through the problem
- Break down complex topics into smaller, manageable parts
- Encourage them to connect ideas to what they already know
- Suggest resources or study methods when appropriate

Keep responses concise but helpful. Always aim to facilitate learning rather than just providing answers."""

SUMMARY_SYSTEM_PROMPT = """You are an AI that creates structured study summaries. When given document content, you must respond with ONLY a valid JSON object in this exact format:

{
    "key_concepts": ["concept1", "concept2", "concept3"],
    "main_points": ["point1", "point2", "point3"],
    "study_tips": ["tip1", "tip2", "tip3"],
    "questions_for_review": ["question1?", "question2?", "question3?"],
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_study_time": "X minutes|X hours",
    "title": "Auto-generated title for this content"
}

Rules:
- Always return valid JSON only, no other text
- Include 3-7 items in each array
- Make study tips actionable and specific
- Make review questions thought-provoking
- Base difficulty on content complexity
- Estimate realistic study time"""
@app.post("/api/v1/ai-study-buddy", response_model=AIStudyResponse)
async def chat_with_study_buddy(
    request: AIStudyRequest,
    current_user: dict = Depends(mock_get_current_user)
):
    """Chat with AI Study Buddy"""
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
            raise HTTPException(status_code=503, detail="AI service not configured")
        
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get or create conversation history
        conv_doc_ref = db.collection("ai_conversations").document(conversation_id)
        conv_doc = conv_doc_ref.get()
        
        if conv_doc.exists:
            conv_data = conv_doc.to_dict()
            conversation_history = conv_data.get("messages", [])
        else:
            # Initialize new conversation with system prompt
            conversation_history = [
                {"role": "system", "content": STUDY_BUDDY_SYSTEM_PROMPT}
            ]
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": request.message})
        
        # Get class context if provided
        class_context = ""
        if request.class_context:
            class_context = get_class_context(request.class_context, db)
        
        # Get AI response
        ai_response = get_ai_response(conversation_history, OPENAI_API_KEY, class_context)
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Save conversation to Firestore
        conv_data = {
            "conversation_id": conversation_id,
            "messages": conversation_history,
            "class_id": request.class_context,
            "user_id": current_user['uid'],
            "created_at": conv_doc.get("created_at") if conv_doc.exists else datetime.datetime.utcnow(),
            "last_updated": datetime.datetime.utcnow()
        }
        conv_doc_ref.set(conv_data)
        
        return AIStudyResponse(
            response=ai_response,
            conversation_id=conversation_id,
            timestamp=datetime.datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Study buddy error: {str(e)}")

@app.get("/api/v1/ai-study-buddy/conversations")
async def get_study_buddy_conversations(
    current_user: dict = Depends(mock_get_current_user)
):
    """Get user's AI study buddy conversation history"""
    try:
        conversations = (db.collection("ai_conversations")
                        .where("user_id", "==", current_user['uid'])
                        .order_by("last_updated", direction=firestore.Query.DESCENDING)
                        .limit(10)
                        .stream())
        
        conversation_list = []
        for conv in conversations:
            conv_data = conv.to_dict()
            # Get the first user message as preview
            first_message = ""
            for msg in conv_data.get("messages", []):
                if msg.get("role") == "user":
                    first_message = msg.get("content", "")[:100] + "..."
                    break
            
            conversation_list.append({
                "conversation_id": conv_data.get("conversation_id"),
                "preview": first_message,
                "class_id": conv_data.get("class_id"),
                "last_updated": serialize_datetime(conv_data.get("last_updated")),
                "message_count": len([m for m in conv_data.get("messages", []) if m.get("role") != "system"])
            })
        
        return {"conversations": conversation_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.get("/api/v1/ai-study-buddy/conversations/{conversation_id}")
async def get_conversation_details(
    conversation_id: str,
    current_user: dict = Depends(mock_get_current_user)
):
    """Get specific AI study buddy conversation"""
    try:
        conv_doc = db.collection("ai_conversations").document(conversation_id).get()
        if not conv_doc.exists:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv_data = conv_doc.to_dict()
        
        # Verify user owns this conversation
        if conv_data.get("user_id") != current_user['uid']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Format messages for response (exclude system message)
        formatted_messages = []
        for msg in conv_data.get("messages", []):
            if msg.get("role") != "system":
                formatted_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "timestamp": serialize_datetime(conv_data.get("last_updated"))
                })
        
        return {
            "conversation_id": conversation_id,
            "messages": formatted_messages,
            "class_id": conv_data.get("class_id"),
            "created_at": serialize_datetime(conv_data.get("created_at")),
            "last_updated": serialize_datetime(conv_data.get("last_updated"))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@app.post("/api/v1/classes/{class_id}/ai-study-buddy")
async def class_specific_study_buddy(
    class_id: str,
    request: AIStudyRequest,
    current_user: dict = Depends(mock_get_current_user)
):
    """Chat with AI Study Buddy in context of specific class"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        # Set class context and call main study buddy endpoint
        request.class_context = class_id
        return await chat_with_study_buddy(request, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Class study buddy error: {str(e)}")

# Add this endpoint to integrate AI suggestions with posts
@app.post("/api/v1/classes/{class_id}/posts/{post_id}/ai-help")
async def get_ai_help_for_post(
    class_id: str,
    post_id: str,
    current_user: dict = Depends(mock_get_current_user)
):
    """Get AI study buddy help for a specific post"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        # Get post content
        post_doc = (db.collection("classes").document(class_id)
                   .collection("posts").document(post_id).get())
        if not post_doc.exists:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_data = post_doc.to_dict()
        
        # Create AI request based on post content
        ai_request = AIStudyRequest(
            message=f"I'm looking at this post: '{post_data.get('title')}' - {post_data.get('content')[:200]}... Can you help me understand this better?",
            class_context=class_id
        )
        
        return await chat_with_study_buddy(ai_request, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI post help error: {str(e)}")

# -------------------------------
# CLASS ENDPOINTS
# -------------------------------
@app.get("/api/v1/classes")
async def get_user_classes(current_user: dict = Depends(mock_get_current_user)):
    """Get user's enrolled classes"""
    try:
        # Get user's class memberships
        memberships = db.collection("classMembers").where("userId", "==", current_user['uid']).stream()
        
        classes = []
        for membership in memberships:
            member_data = membership.to_dict()
            class_id = member_data.get("classId")
            
            # Get class details
            class_doc = db.collection("classes").document(class_id).get()
            if class_doc.exists:
                class_data = class_doc.to_dict()
                classes.append({
                    "class_id": class_id,
                    "name": class_data.get("name"),
                    "code": class_data.get("code"),
                    "role": member_data.get("role"),
                    "joined_at": serialize_datetime(member_data.get("joinedAt"))
                })
        
        return {"classes": classes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch classes: {str(e)}")

@app.post("/api/v1/classes/join")
async def join_class_by_code(request: JoinClassRequest, current_user: dict = Depends(mock_get_current_user)):
    """Join class by code"""
    try:
        code = request.class_code.upper()
        
        # Find class by code
        classes_query = db.collection("classes").where("code", "==", code).limit(1)
        classes = list(classes_query.stream())
        
        if not classes:
            raise HTTPException(status_code=404, detail="Invalid class code")
        
        class_doc = classes[0]
        class_id = class_doc.id
        class_data = class_doc.to_dict()
        
        # Check if already a member
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if member_doc.exists:
            return {"message": "Already a member of this class", "class_id": class_id}
        
        # Add as student
        member_data = {
            "classId": class_id,
            "userId": current_user['uid'],
            "role": "student",
            "joinedAt": datetime.datetime.utcnow()
        }
        db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").set(member_data)
        
        return {
            "message": "Successfully joined class",
            "class_id": class_id,
            "class_name": class_data.get("name")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join class: {str(e)}")

@app.get("/api/v1/classes/{class_id}")
async def get_class_details(class_id: str, limit: int = 20, offset: int = 0, 
                           current_user: dict = Depends(mock_get_current_user)):
    """Get class details and posts"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        # Get class details
        class_doc = db.collection("classes").document(class_id).get()
        if not class_doc.exists:
            raise HTTPException(status_code=404, detail="Class not found")
        
        class_data = class_doc.to_dict()
        
        # Get posts with pagination
        posts_query = (db.collection("classes").document(class_id)
                      .collection("posts")
                      .order_by("createdAt", direction=firestore.Query.DESCENDING)
                      .limit(limit)
                      .offset(offset))
        
        posts = []
        for post_doc in posts_query.stream():
            post_data = post_doc.to_dict()
            
            # Get author info
            author_doc = db.collection("users").document(post_data.get("authorId", "")).get()
            author_data = author_doc.to_dict() if author_doc.exists else {}
            
            posts.append({
                "post_id": post_doc.id,
                "title": post_data.get("title", ""),
                "content": post_data.get("content", ""),
                "post_type": post_data.get("post_type", "discussion"),
                "tags": post_data.get("tags", []),
                "author_id": post_data.get("authorId"),
                "author_name": author_data.get("full_name", "Unknown"),
                "created_at": serialize_datetime(post_data.get("createdAt")),
                "files": post_data.get("files", [])
            })
        
        return {
            "class": {
                "class_id": class_id,
                "name": class_data.get("name"),
                "code": class_data.get("code"),
                "created_by": class_data.get("createdBy"),
                "created_at": serialize_datetime(class_data.get("createdAt")),
                "join_mode": class_data.get("joinMode"),
                "visibility": class_data.get("visibility")
            },
            "posts": posts,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(posts) == limit
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get class details: {str(e)}")

@app.post("/api/v1/classes/{class_id}/posts")
async def create_post(class_id: str, request: CreatePostRequest, 
                     current_user: dict = Depends(mock_get_current_user)):
    """Create new post in class"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        # Create post
        post_ref = (db.collection("classes").document(class_id)
                   .collection("posts").document())
        
        post_data = {
            "title": request.title,
            "content": request.content,
            "post_type": request.post_type,
            "tags": request.tags,
            "files": request.files,
            "authorId": current_user['uid'],
            "createdAt": datetime.datetime.utcnow(),
            "isPublic": True
        }
        post_ref.set(post_data)
        
        return {
            "message": "Post created successfully",
            "post_id": post_ref.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")

@app.get("/api/v1/posts/{post_id}")
async def get_post_details(post_id: str, current_user: dict = Depends(mock_get_current_user)):
    """Get specific post details"""
    try:
        # This is a simplified implementation - you'd need to find the post across classes
        # or store class_id with the post_id in the request
        
        # For now, return a placeholder response
        return {
            "error": "This endpoint needs class_id context to locate the post",
            "suggestion": "Use /api/v1/classes/{class_id} to get posts within a class context"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get post: {str(e)}")
    

@app.post("/api/v1/ai-study-buddy/with-files")
async def chat_with_study_buddy_files(
    message: str = "",
    conversation_id: Optional[str] = None,
    class_context: Optional[str] = None,
    files: List[UploadFile] = File(default=[]),
    current_user: dict = Depends(mock_get_current_user)
):
    """Chat with AI Study Buddy including file analysis"""
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
            raise HTTPException(status_code=503, detail="AI service not configured")
        
        # Process uploaded files
        files_content = []
        file_types = []
        
        for file in files:
            if file.filename.lower().endswith('.pdf'):
                pdf_text = extract_pdf_text(file)
                files_content.append({
                    "type": "text",
                    "content": f"PDF content from {file.filename}:\n{pdf_text[:2000]}"  # Limit length
                })
                file_types.append("pdf")
                
            elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                base64_image = process_image(file)
                files_content.append({
                    "type": "image_url",
                    "image_url": {"url": base64_image}
                })
                file_types.append("image")
        
        # Generate or use existing conversation ID
        conversation_id = conversation_id or str(uuid.uuid4())
        
        # Get or create conversation history
        conv_doc_ref = db.collection("ai_conversations").document(conversation_id)
        conv_doc = conv_doc_ref.get()
        
        if conv_doc.exists:
            conv_data = conv_doc.to_dict()
            conversation_history = conv_data.get("messages", [])
        else:
            conversation_history = [
                {"role": "system", "content": STUDY_BUDDY_SYSTEM_PROMPT}
            ]
        
        # Create user message
        user_message = message if message else "Can you help me understand these files?"
        conversation_history.append({"role": "user", "content": user_message})
        
        # Get class context if provided
        class_context_text = ""
        if class_context:
            class_context_text = get_class_context(class_context, db)
        
        # Get AI response with files
        ai_response = get_ai_response_with_files(
            conversation_history, 
            OPENAI_API_KEY, 
            files_content,
            class_context_text
        )
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Save conversation to Firestore
        conv_data = {
            "conversation_id": conversation_id,
            "messages": conversation_history,
            "class_id": class_context,
            "user_id": current_user['uid'],
            "created_at": conv_doc.get("created_at") if conv_doc.exists else datetime.datetime.utcnow(),
            "last_updated": datetime.datetime.utcnow(),
            "file_types": file_types
        }
        conv_doc_ref.set(conv_data)
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "processed_files": len(files),
            "file_types": file_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File analysis error: {str(e)}")
    

@app.post("/api/v1/notes/analyze", response_model=SummaryResponse)
async def analyze_notes_to_json(
    files: List[UploadFile] = File(...),
    request: NoteSummaryRequest = Depends(),
    current_user: dict = Depends(mock_get_current_user)
):
    """Analyze uploaded files and return structured JSON summary"""
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
            raise HTTPException(status_code=503, detail="AI service not configured")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # Process files and combine content
        combined_content = ""
        file_sources = []
        
        for file in files:
            file_sources.append(file.filename)
            
            if file.filename.lower().endswith('.pdf'):
                pdf_text = extract_pdf_text(file)
                combined_content += f"\n\n--- Content from {file.filename} ---\n{pdf_text}"
                
            elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # For images, we'll need to use GPT-4 Vision - simplified for now
                combined_content += f"\n\n--- Image file: {file.filename} (image analysis not implemented in JSON mode) ---\n"
            
            elif file.filename.lower().endswith('.txt'):
                text_content = (await file.read()).decode('utf-8')
                combined_content += f"\n\n--- Content from {file.filename} ---\n{text_content}"
        
        if not combined_content.strip():
            raise HTTPException(status_code=400, detail="No readable content found in uploaded files")
        
        # Get structured summary from AI
        summary_data = get_structured_summary(
            combined_content, 
            OPENAI_API_KEY, 
            request.title
        )
        
        # Generate summary ID and create database document
        summary_id = str(uuid.uuid4())
        
        # Use provided title or AI-generated one
        final_title = request.title or summary_data.get("title", "Study Notes")
        
        # Create NoteSummary object
        note_summary = NoteSummary(
            summary_id=summary_id,
            title=final_title,
            key_concepts=summary_data.get("key_concepts", []),
            main_points=summary_data.get("main_points", []),
            study_tips=summary_data.get("study_tips", []),
            questions_for_review=summary_data.get("questions_for_review", []),
            difficulty_level=summary_data.get("difficulty_level", "intermediate"),
            estimated_study_time=summary_data.get("estimated_study_time", "30 minutes"),
            created_at=datetime.datetime.utcnow().isoformat(),
            file_sources=file_sources,
            class_id=request.class_id,
            user_id=current_user['uid']
        )
        
        # Store in Firestore
        summary_doc = {
            "summary_id": summary_id,
            "title": final_title,
            "key_concepts": summary_data.get("key_concepts", []),
            "main_points": summary_data.get("main_points", []),
            "study_tips": summary_data.get("study_tips", []),
            "questions_for_review": summary_data.get("questions_for_review", []),
            "difficulty_level": summary_data.get("difficulty_level", "intermediate"),
            "estimated_study_time": summary_data.get("estimated_study_time", "30 minutes"),
            "created_at": datetime.datetime.utcnow(),
            "file_sources": file_sources,
            "class_id": request.class_id,
            "user_id": current_user['uid'],
            "raw_content": combined_content[:1000]  # Store preview of original content
        }
        
        db.collection("note_summaries").document(summary_id).set(summary_doc)
        
        return SummaryResponse(
            summary=note_summary,
            raw_content_preview=combined_content[:200] + "..." if len(combined_content) > 200 else combined_content
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Note analysis failed: {str(e)}")

# Get user's summaries
@app.get("/api/v1/summaries")
async def get_user_summaries(
    class_id: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(mock_get_current_user)
):
    """Get user's note summaries"""
    try:
        query = db.collection("note_summaries").where("user_id", "==", current_user['uid'])
        
        if class_id:
            query = query.where("class_id", "==", class_id)
        
        summaries = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        summary_list = []
        for summary_doc in summaries:
            summary_data = summary_doc.to_dict()
            summary_list.append({
                "summary_id": summary_data.get("summary_id"),
                "title": summary_data.get("title"),
                "difficulty_level": summary_data.get("difficulty_level"),
                "estimated_study_time": summary_data.get("estimated_study_time"),
                "created_at": serialize_datetime(summary_data.get("created_at")),
                "file_sources": summary_data.get("file_sources", []),
                "class_id": summary_data.get("class_id"),
                "concept_count": len(summary_data.get("key_concepts", []))
            })
        
        return {"summaries": summary_list}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summaries: {str(e)}")

# Get specific summary details
@app.get("/api/v1/summaries/{summary_id}", response_model=NoteSummary)
async def get_summary_details(
    summary_id: str,
    current_user: dict = Depends(mock_get_current_user)
):
    """Get detailed summary by ID"""
    try:
        summary_doc = db.collection("note_summaries").document(summary_id).get()
        
        if not summary_doc.exists:
            raise HTTPException(status_code=404, detail="Summary not found")
        
        summary_data = summary_doc.to_dict()
        
        # Verify ownership
        if summary_data.get("user_id") != current_user['uid']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return NoteSummary(
            summary_id=summary_data.get("summary_id"),
            title=summary_data.get("title"),
            key_concepts=summary_data.get("key_concepts", []),
            main_points=summary_data.get("main_points", []),
            study_tips=summary_data.get("study_tips", []),
            questions_for_review=summary_data.get("questions_for_review", []),
            difficulty_level=summary_data.get("difficulty_level", "intermediate"),
            estimated_study_time=summary_data.get("estimated_study_time", "30 minutes"),
            created_at=serialize_datetime(summary_data.get("created_at")),
            file_sources=summary_data.get("file_sources", []),
            class_id=summary_data.get("class_id"),
            user_id=summary_data.get("user_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

# Get summaries for a specific class
@app.get("/api/v1/classes/{class_id}/summaries")
async def get_class_summaries(
    class_id: str,
    current_user: dict = Depends(mock_get_current_user)
):
    """Get all summaries for a specific class"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        return await get_user_summaries(class_id=class_id, current_user=current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get class summaries: {str(e)}")
    
    
# -------------------------------
# Health Check
# -------------------------------
@app.get("/")
async def health_check():
    return {"message": "Classroom API v1.0.0 is running ✅", "timestamp": datetime.datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)