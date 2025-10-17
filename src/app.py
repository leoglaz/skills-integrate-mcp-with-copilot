"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import json
import uuid
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory session storage (in production, use Redis or database)
active_sessions = {}

# Load teachers from JSON file
def load_teachers():
    try:
        with open(os.path.join(current_dir, "teachers.json"), "r") as f:
            return json.load(f)["teachers"]
    except FileNotFoundError:
        return []

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def is_teacher_authenticated(request: Request):
    """Check if the current request has a valid teacher session"""
    session_id = request.cookies.get("session_id")
    return session_id and session_id in active_sessions

def authenticate_teacher(username: str, password: str):
    """Authenticate teacher credentials"""
    teachers = load_teachers()
    for teacher in teachers:
        if teacher["username"] == username and teacher["password"] == password:
            return True
    return False

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.post("/login")
def login(request: Request, response: Response, username: str, password: str):
    """Login endpoint for teachers"""
    if authenticate_teacher(username, password):
        # Create a new session
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = username
        
        # Set session cookie
        response.set_cookie("session_id", session_id, httponly=True)
        return {"message": "Login successful", "authenticated": True}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
def logout(request: Request, response: Response):
    """Logout endpoint"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully", "authenticated": False}

@app.get("/auth/status")
def auth_status(request: Request):
    """Check authentication status"""
    authenticated = is_teacher_authenticated(request)
    username = None
    if authenticated:
        session_id = request.cookies.get("session_id")
        username = active_sessions.get(session_id)
    
    return {"authenticated": authenticated, "username": username}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(request: Request, activity_name: str, email: str):
    """Sign up a student for an activity - requires teacher authentication"""
    # Check if user is authenticated as a teacher
    if not is_teacher_authenticated(request):
        raise HTTPException(status_code=401, detail="Teacher authentication required")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(request: Request, activity_name: str, email: str):
    """Unregister a student from an activity - requires teacher authentication"""
    # Check if user is authenticated as a teacher
    if not is_teacher_authenticated(request):
        raise HTTPException(status_code=401, detail="Teacher authentication required")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
