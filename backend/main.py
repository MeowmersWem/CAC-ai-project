from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List
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
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel 

load_dotenv()

# ---- Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("api") 

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
       
        service_account_path = os.path.join(os.path.dirname(__file__), "serviceAccountKey.json")

       
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            print("✅ Using service account key")
        else:
          
            cred = credentials.ApplicationDefault()
            print("✅ Using application default credentials")
        
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        raise

db = firestore.client()
app = FastAPI(title="Classroom API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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

class UserProfile(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    university: Optional[str] = None
    state: Optional[str] = None
    role: Optional[str] = None  # "student" | "instructor"

class ProfileUpdateRequest(BaseModel):
    university: Optional[str] = None
    state: Optional[str] = None
    role: Optional[str] = None

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
    file_types: List[str] = []  


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
    file_sources: List[str]  
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


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and verify Firebase ID token from Authorization header"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        token = authorization.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Invalid authentication token: {str(e)}"
        )
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
    
 
    system_message = conversation_history[0].copy()
    if class_context:
        system_message["content"] += f"\n\nClass Context: {class_context}"
    

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
     
        class_doc = db.collection("classes").document(class_id).get()
        if not class_doc.exists:
            return ""
        
        class_data = class_doc.to_dict()
        class_name = class_data.get("name", "")
        
    
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
           
            if any(f["type"] == "image" for f in files_content):
                last_message["content"] = [
                    {"type": "text", "text": last_message["content"]}
                ] + files_content
            else:
          
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
        "temperature": 0.3  
    }
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        ai_response = result["choices"][0]["message"]["content"].strip()
        
        
        try:
            summary_data = json.loads(ai_response)
            return summary_data
        except json.JSONDecodeError as e:
            
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


@app.get("/__routes")
def __routes():
    return {"routes": [getattr(r, "path", str(r)) for r in app.routes]}
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
        
        # Create user profile
        user_data = {
            "email": request.email,
            "full_name": request.full_name,
            "university": request.university,
            "state": None,
            "role": None,
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
    try:
        # Get user by email
        user = auth.get_user_by_email(request.email)
        
        # Create custom token
        custom_token = auth.create_custom_token(user.uid)
        
        # Get user profile
        user_doc = db.collection("users").document(user.uid).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}
        
        return {
            "user_id": user.uid,
            "email": user.email,
            "full_name": user_data.get("full_name", ""),
            "custom_token": custom_token.decode('utf-8'),  # Renamed from 'token' to be explicit
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {str(e)}")

@app.post("/api/v1/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Google OAuth authentication"""
    try:
        decoded_token = auth.verify_id_token(request.id_token)
        uid = decoded_token['uid']
        
       
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
  
    try:
        auth.revoke_refresh_tokens(current_user['uid'])
        return {"message": "Successfully signed out"}
    except Exception as e:
        return {"message": "Signed out (token revocation failed)"}

# -------------------------------
# USER PROFILE ENDPOINTS
# -------------------------------

@app.get("/api/v1/users/me", response_model=UserProfile)
async def get_me(
    email: Optional[str] = Query(None),
    current_user: dict = Depends(mock_get_current_user)  # or get_current_user if you’ve switched
):
    """
    If ?email= is provided, look up by email.
    Otherwise return the current signed-in user's profile.
    """
    logger.info("GET /api/v1/users/me | email=%s | uid=%s", email, (current_user or {}).get("uid"))

    try:
        # ---- Lookup by email (query param) ----
        if email:
            email_norm = email.strip().lower()
            logger.info("Looking up user by email: %s", email_norm)

            q = (db.collection("users")
                   .where("email", "==", email_norm)
                   .limit(1)
                   .stream())
            snap = next(q, None)

            if not snap:
                logger.warning("User not found for email: %s", email_norm)
                raise HTTPException(status_code=404, detail="User not found")

            data = snap.to_dict() or {}
            logger.info("Found user by email: %s (uid=%s)", email_norm, snap.id)

            return UserProfile(
                user_id=snap.id,
                email=data.get("email", email_norm),
                full_name=data.get("full_name", ""),
                university=data.get("university"),
                state=data.get("state"),
                role=data.get("role"),
            )

        # ---- Current user (by UID) ----
        uid = (current_user or {}).get("uid")
        logger.info("Looking up user by UID: %s", uid)

        if not uid:
            logger.error("Unauthenticated request (no uid).")
            raise HTTPException(status_code=401, detail="Unauthenticated")

        doc = db.collection("users").document(uid).get()

        if not doc.exists:
            logger.warning("User not found for uid: %s", uid)
            raise HTTPException(status_code=404, detail="User not found")

        data = doc.to_dict() or {}
        logger.info("Found user by uid: %s", uid)

        return UserProfile(
            user_id=uid,
            email=(data.get("email") or "").lower(),
            full_name=data.get("full_name", ""),
            university=data.get("university"),
            state=data.get("state"),
            role=data.get("role"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to load profile: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to load profile: {str(e)}")
    
@app.put("/api/v1/users/me")
async def update_me(
    payload: ProfileUpdateRequest, 
    email: Optional[str] = Query(None),  # Add Query here for consistency
    current_user: dict = Depends(mock_get_current_user)
):
    """Update current user's profile."""
    print(f"🔵 Update profile called with email: {email}")
    print(f"🔵 Payload: {payload.model_dump()}")
    
    try:
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        if email:
            email_norm = email.strip().lower()
            print(f"🔵 Looking up user by email: {email_norm}")
            
            
            user_docs = list(db.collection("users").where("email", "==", email_norm).limit(1).stream())
            
            if not user_docs: 
                print(f"🔴 User not found for email: {email_norm}")
                raise HTTPException(status_code=404, detail="User not found")
            
            user_doc = user_docs[0]
            print(f"🟢 Found user with ID: {user_doc.id}")
            
            # Use set with merge=True instead of update
            db.collection("users").document(user_doc.id).set(update_data, merge=True)
            print(f"🟢 Profile updated successfully")
        else:
            uid = current_user.get('uid')
            print(f"🔵 Using current_user uid: {uid}")
            db.collection("users").document(uid).set(update_data, merge=True)

        return {"message": "Profile updated"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"🔴 Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
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
    current_user: dict = Depends(get_current_user)
):
    """Chat with AI Study Buddy"""
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
            raise HTTPException(status_code=503, detail="AI service not configured")
        
        
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
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
        
       
        conversation_history.append({"role": "user", "content": request.message})
        
       
        class_context = ""
        if request.class_context:
            class_context = get_class_context(request.class_context, db)
        
      
        ai_response = get_ai_response(conversation_history, OPENAI_API_KEY, class_context)
        
      
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
):
    """Chat with AI Study Buddy in context of specific class"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        
        request.class_context = class_id
        return await chat_with_study_buddy(request, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Class study buddy error: {str(e)}")


@app.post("/api/v1/classes/{class_id}/posts/{post_id}/ai-help")
async def get_ai_help_for_post(
    class_id: str,
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get AI study buddy help for a specific post"""
    try:
        # Verify user is member of class
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        
        post_doc = (db.collection("classes").document(class_id)
                   .collection("posts").document(post_id).get())
        if not post_doc.exists:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_data = post_doc.to_dict()
        
       
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
class CreateClassRequest(BaseModel):
    name: str
    visibility: Optional[str] = "private"  # private|public
    join_mode: Optional[str] = "code"      # code|open

# --- Assignments & Roster models ---
class CreateAssignmentRequest(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None  # ISO8601 string

class SetGradeRequest(BaseModel):
    assignment_id: str
    grade: float


@app.post("/api/v1/classes")
async def create_class(request: CreateClassRequest, email: Optional[str] = None, current_user: dict = Depends(mock_get_current_user)):
    """Create a class and add the creator as instructor.
    In dev, allow ?email=... to resolve the creating user by Firebase Auth.
    """
    try:
        # Resolve creator uid
        if email:
            user_record = auth.get_user_by_email(email)
            creator_uid = user_record.uid
        else:
            creator_uid = current_user.get('uid')

        class_ref = db.collection("classes").document()
        class_id = class_ref.id
        code = generate_class_code()
        class_doc = {
            "name": request.name,
            "code": code,
            "createdBy": creator_uid,
            "createdAt": datetime.datetime.utcnow(),
            "joinMode": request.join_mode,
            "visibility": request.visibility,
        }
        class_ref.set(class_doc)

        
        member_doc = {
            "classId": class_id,
            "userId": creator_uid,
            "role": "instructor",
            "joinedAt": datetime.datetime.utcnow()
        }
        db.collection("classMembers").document(f"{class_id}_{creator_uid}").set(member_doc)

        return {
            "class_id": class_id,
            "name": request.name,
            "code": code,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create class: {str(e)}")
@app.get("/api/v1/classes")
async def get_user_classes(current_user: dict = Depends(get_current_user)):
    """Get user's enrolled classes"""
    try:
        
        memberships = db.collection("classMembers").where("userId", "==", current_user['uid']).stream()
        
        classes = []
        for membership in memberships:
            member_data = membership.to_dict()
            class_id = member_data.get("classId")
            
          
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
async def join_class_by_code(request: JoinClassRequest, email: Optional[str] = None, current_user: dict = Depends(mock_get_current_user)):
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
        
       
        if email:
            try:
                user_record = auth.get_user_by_email(email)
                uid = user_record.uid
            except Exception:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            uid = current_user['uid']
        
        # Check if already a member
        member_doc = db.collection("classMembers").document(f"{class_id}_{uid}").get()
        if member_doc.exists:
            return {"message": "Already a member of this class", "class_id": class_id}
        
        
        member_data = {
            "classId": class_id,
            "userId": uid,
            "role": "student",
            "joinedAt": datetime.datetime.utcnow()
        }
        db.collection("classMembers").document(f"{class_id}_{uid}").set(member_data)
        
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
                           current_user: dict = Depends(get_current_user)):
    """Get class details and posts"""
    try:
        
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
        
        class_doc = db.collection("classes").document(class_id).get()
        if not class_doc.exists:
            raise HTTPException(status_code=404, detail="Class not found")
        
        class_data = class_doc.to_dict()
        
       
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
                     current_user: dict = Depends(get_current_user)):
    """Create new post in class"""
    try:
        
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        
      
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

@app.post("/api/v1/classes/{class_id}/assignments")
async def create_assignment(class_id: str, request: CreateAssignmentRequest, current_user: dict = Depends(get_current_user)):
    """Create an assignment (instructors only)."""
    try:
        
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        role = member_doc.to_dict().get("role")
        if role != "instructor":
            raise HTTPException(status_code=403, detail="Only instructors can create assignments")

        # Create assignment under class
        asg_ref = (db.collection("classes").document(class_id)
                   .collection("assignments").document())

        assignment_data = {
            "title": request.title,
            "description": request.description or "",
            "dueDate": request.due_date,
            "createdAt": datetime.datetime.utcnow(),
            "createdBy": current_user['uid'],
        }
        asg_ref.set(assignment_data)

        return {"message": "Assignment created", "assignment_id": asg_ref.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")

@app.get("/api/v1/classes/{class_id}/assignments")
async def list_assignments(class_id: str, current_user: dict = Depends(get_current_user)):
    """List assignments for a class (students and instructors)."""
    try:
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")

        q = (db.collection("classes").document(class_id)
             .collection("assignments")
             .order_by("createdAt", direction=firestore.Query.DESCENDING))
        results = []
        for doc in q.stream():
            d = doc.to_dict()
            results.append({
                "assignment_id": doc.id,
                "title": d.get("title"),
                "description": d.get("description", ""),
                "due_date": serialize_datetime(d.get("dueDate")) if isinstance(d.get("dueDate"), datetime.datetime) else d.get("dueDate"),
                "created_at": serialize_datetime(d.get("createdAt")),
            })
        return {"assignments": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list assignments: {str(e)}")

@app.get("/api/v1/classes/{class_id}/roster")
async def get_class_roster(class_id: str, current_user: dict = Depends(get_current_user)):
    """Get class roster. Students see classmates; instructors see all students and their roles."""
    try:
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        caller_role = member_doc.to_dict().get("role")

        members = db.collection("classMembers").where("classId", "==", class_id).stream()
        roster = []
        for m in members:
            mdata = m.to_dict()
            user_doc = db.collection("users").document(mdata.get("userId")).get()
            u = user_doc.to_dict() if user_doc.exists else {}
            roster.append({
                "user_id": mdata.get("userId"),
                "full_name": u.get("full_name", "Unknown"),
                "role": mdata.get("role", "student"),
                "joined_at": serialize_datetime(mdata.get("joinedAt")),
            })

        # Students: only show students (and optionally instructors if desired). Keep simple: return all members.
        return {"roster": roster, "viewer_role": caller_role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get roster: {str(e)}")

@app.post("/api/v1/classes/{class_id}/grades/set")
async def set_student_grade(class_id: str, request: SetGradeRequest, student_id: str, current_user: dict = Depends(get_current_user)):
    """Set a grade for a student on an assignment (instructors only)."""
    try:
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists or member_doc.to_dict().get("role") != "instructor":
            raise HTTPException(status_code=403, detail="Only instructors can set grades")
        # Ensure student is in class
        stu_doc = db.collection("classMembers").document(f"{class_id}_{student_id}").get()
        if not stu_doc.exists:
            raise HTTPException(status_code=404, detail="Student not in this class")

        grade_ref = (db.collection("classes").document(class_id)
                     .collection("grades").document(f"{request.assignment_id}_{student_id}"))
        grade_ref.set({
            "assignmentId": request.assignment_id,
            "studentId": student_id,
            "grade": request.grade,
            "updatedAt": datetime.datetime.utcnow(),
            "updatedBy": current_user['uid'],
        })
        return {"message": "Grade saved"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set grade: {str(e)}")

@app.get("/api/v1/classes/{class_id}/grades/student/{student_id}")
async def get_student_grades(class_id: str, student_id: str, current_user: dict = Depends(get_current_user)):
    """Get all grades for a student in a class. Students can view their own; instructors can view any."""
    try:
        caller_member = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not caller_member.exists:
            raise HTTPException(status_code=403, detail="Not a member of this class")
        caller_role = caller_member.to_dict().get("role")
        if current_user['uid'] != student_id and caller_role != "instructor":
            raise HTTPException(status_code=403, detail="Not allowed")

        q = db.collection("classes").document(class_id).collection("grades").where("studentId", "==", student_id)
        grades = []
        total = 0.0
        count = 0
        for gdoc in q.stream():
            g = gdoc.to_dict()
            grades.append({
                "assignment_id": g.get("assignmentId"),
                "grade": g.get("grade"),
                "updated_at": serialize_datetime(g.get("updatedAt")),
            })
            if isinstance(g.get("grade"), (int, float)):
                total += float(g.get("grade"))
                count += 1
        final_grade = (total / count) if count else None
        return {"grades": grades, "final_grade": final_grade}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get student grades: {str(e)}")

@app.get("/api/v1/classes/{class_id}/grades/assignment/{assignment_id}")
async def get_assignment_grades(class_id: str, assignment_id: str, current_user: dict = Depends(get_current_user)):
    """List all student grades for an assignment (instructors only)."""
    try:
        member_doc = db.collection("classMembers").document(f"{class_id}_{current_user['uid']}").get()
        if not member_doc.exists or member_doc.to_dict().get("role") != "instructor":
            raise HTTPException(status_code=403, detail="Only instructors can view assignment grades")

        q = (db.collection("classes").document(class_id)
             .collection("grades").where("assignmentId", "==", assignment_id))
        results = []
        for gdoc in q.stream():
            g = gdoc.to_dict()
            user_doc = db.collection("users").document(g.get("studentId", "")).get()
            u = user_doc.to_dict() if user_doc.exists else {}
            results.append({
                "student_id": g.get("studentId"),
                "student_name": u.get("full_name", "Unknown"),
                "grade": g.get("grade"),
                "updated_at": serialize_datetime(g.get("updatedAt")),
            })
        return {"grades": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assignment grades: {str(e)}")


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
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

