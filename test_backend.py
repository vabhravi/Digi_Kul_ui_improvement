import requests
import json
import os

BASE_URL = "http://localhost:5000/api"

def test_authentication():
    """Test teacher registration and login"""
    print("Testing authentication...")
    
    # Register a teacher
    register_data = {
        "name": "Test Teacher",
        "email": "test@example.com",
        "institution": "Test College",
        "subject": "Computer Science"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    print(f"Register response: {response.status_code}, {response.json()}")
    
    # Login
    login_data = {
        "email": "test@example.com"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"Login response: {response.status_code}, {response.json()}")
    
    return response.json().get('token')

def test_lecture_management(token):
    """Test lecture creation and retrieval"""
    print("Testing lecture management...")
    
    # Create a lecture
    lecture_data = {
        "title": "Test Lecture",
        "description": "This is a test lecture",
        "scheduled_time": "2023-12-15T10:00:00",
        "duration": 45
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/lectures", json=lecture_data, headers=headers)
    print(f"Create lecture response: {response.status_code}, {response.json()}")
    
    # Get lectures
    response = requests.get(f"{BASE_URL}/lectures", headers=headers)
    print(f"Get lectures response: {response.status_code}, {response.json()}")
    
    return response.json()[0]['id'] if response.json() else None

def test_content_upload(token, lecture_id):
    """Test content upload functionality"""
    print("Testing content upload...")
    
    # Create a simple text file to upload
    with open('test_file.txt', 'w') as f:
        f.write("This is a test file content for the virtual classroom.")
    
    # Upload the file
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        'file': open('test_file.txt', 'rb')
    }
    data = {
        'lecture_id': lecture_id,
        'title': 'Test File',
        'description': 'A test file for upload functionality'
    }
    
    response = requests.post(f"{BASE_URL}/upload_material", files=files, data=data, headers=headers)
    print(f"Upload material response: {response.status_code}, {response.json()}")
    
    # Clean up
    files['file'].close()
    os.remove('test_file.txt')
    
    return response.json().get('material_id')

def test_interactive_elements(token, lecture_id):
    """Test quizzes, polls, and discussions"""
    print("Testing interactive elements...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a quiz
    quiz_data = {
        "lecture_id": lecture_id,
        "question": "What is Python?",
        "options": ["A programming language", "A snake", "A movie", "All of the above"],
        "correct_answer": "A programming language"
    }
    
    response = requests.post(f"{BASE_URL}/quiz", json=quiz_data, headers=headers)
    print(f"Create quiz response: {response.status_code}, {response.json()}")
    
    # Create a poll
    poll_data = {
        "lecture_id": lecture_id,
        "question": "Which topic interests you most?",
        "options": ["Web Development", "Data Science", "Machine Learning", "Cybersecurity"]
    }
    
    response = requests.post(f"{BASE_URL}/poll", json=poll_data, headers=headers)
    print(f"Create poll response: {response.status_code}, {response.json()}")
    
    # Add a discussion message
    discussion_data = {
        "lecture_id": lecture_id,
        "message": "This is a test discussion message."
    }
    
    response = requests.post(f"{BASE_URL}/discussion", json=discussion_data, headers=headers)
    print(f"Add discussion response: {response.status_code}, {response.json()}")

def test_content_delivery(token, lecture_id, material_id):
    """Test content retrieval and download"""
    print("Testing content delivery...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get lecture materials
    response = requests.get(f"{BASE_URL}/lecture/{lecture_id}/materials", headers=headers)
    print(f"Get materials response: {response.status_code}, {response.json()}")
    
    # Download a material
    if material_id:
        response = requests.get(f"{BASE_URL}/download/{material_id}", headers=headers)
        print(f"Download material response: {response.status_code}")
        print(f"Content length: {len(response.content)} bytes")

if __name__ == "__main__":
    # Run all tests
    token = test_authentication()
    
    if token:
        lecture_id = test_lecture_management(token)
        
        if lecture_id:
            material_id = test_content_upload(token, lecture_id)
            test_interactive_elements(token, lecture_id)
            test_content_delivery(token, lecture_id, material_id)
    else:
        print("Authentication failed, cannot run other tests")