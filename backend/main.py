
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Try service account key first (development)
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            print("✅ Using service account key")
        else:
            # Fallback to application default credentials (production)
            cred = credentials.ApplicationDefault()
            print("✅ Using application default credentials")
        
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

# -------------------------------
# Health Check
# -------------------------------
@app.get("/")
async def health_check():
    return {"message": "Classroom API v1.0.0 is running ✅", "timestamp": datetime.datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)