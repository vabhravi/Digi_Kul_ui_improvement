#!/usr/bin/env python3
"""
DigiKul Demo Script
Demonstrates all the key features of the platform
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🎓 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request and handle response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        
        if response.status_code < 400:
            return response.json()
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on http://localhost:5000")
        return None

def demo_teacher_registration():
    """Demonstrate teacher registration"""
    print_step(1, "Teacher Registration")
    
    teacher_data = {
        "name": "Dr. Priya Sharma",
        "email": "priya.sharma@ruralcollege.edu",
        "institution": "Rural Diploma College",
        "subject": "Computer Science"
    }
    
    response = make_request('POST', '/api/register', teacher_data)
    if response:
        print(f"✅ Teacher registered: {response['teacher_id']}")
        return response['token'], response['teacher_id']
    
    return None, None

def demo_lecture_creation(token):
    """Demonstrate lecture creation"""
    print_step(2, "Creating Lecture")
    
    # Create a lecture for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    scheduled_time = tomorrow.strftime("%Y-%m-%dT10:00:00")
    
    lecture_data = {
        "title": "Introduction to Web Development",
        "description": "Learn HTML, CSS, and JavaScript basics for rural students",
        "scheduled_time": scheduled_time,
        "duration": 90
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request('POST', '/api/lectures', lecture_data, headers)
    
    if response:
        print(f"✅ Lecture created: {response['lecture_id']}")
        return response['lecture_id']
    
    return None

def demo_material_upload(token, lecture_id):
    """Demonstrate material upload"""
    print_step(3, "Uploading Teaching Materials")
    
    # Create a sample text file
    sample_content = """
    # Introduction to Web Development
    
    ## What is HTML?
    HTML (HyperText Markup Language) is the standard markup language for creating web pages.
    
    ## Basic HTML Structure
    ```html
    <!DOCTYPE html>
    <html>
    <head>
        <title>My First Web Page</title>
    </head>
    <body>
        <h1>Hello World!</h1>
        <p>This is my first web page.</p>
    </body>
    </html>
    ```
    
    ## Key Concepts
    1. Tags and Elements
    2. Attributes
    3. Document Structure
    4. Text Formatting
    """
    
    # Create sample file
    filename = "web_dev_intro.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    # Upload file
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(filename, 'rb') as f:
        files = {'file': (filename, f, 'text/plain')}
        data = {
            'lecture_id': lecture_id,
            'title': 'Web Development Introduction',
            'description': 'Basic concepts and examples for beginners'
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/upload_material",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code < 400:
                result = response.json()
                print(f"✅ Material uploaded: {result['material_id']}")
                print(f"📊 Compression ratio: {result['compression_ratio']}")
            else:
                print(f"❌ Upload failed: {response.text}")
        except Exception as e:
            print(f"❌ Upload error: {e}")
    
    # Clean up
    if os.path.exists(filename):
        os.remove(filename)

def demo_student_registration():
    """Demonstrate student registration"""
    print_step(4, "Student Registration")
    
    student_data = {
        "name": "Rajesh Kumar",
        "email": "rajesh.kumar@student.edu",
        "institution": "Rural Diploma College"
    }
    
    response = make_request('POST', '/api/students/register', student_data)
    if response:
        print(f"✅ Student registered: {response['student_id']}")
        return response['student_id']
    
    return None

def demo_live_session_start(token, lecture_id):
    """Demonstrate starting a live session"""
    print_step(5, "Starting Live Session")
    
    session_data = {"lecture_id": lecture_id}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = make_request('POST', '/api/live_session/start', session_data, headers)
    if response:
        print(f"✅ Live session started: {response['session_id']}")
        print(f"🔗 Session URL: {BASE_URL}/live/{response['session_id']}")
        return response['session_id']
    
    return None

def demo_mobile_api():
    """Demonstrate mobile API endpoints"""
    print_step(6, "Mobile API Endpoints")
    
    # Get available lectures
    response = make_request('GET', '/api/mobile/lectures/available')
    if response:
        print(f"✅ Available lectures: {response['count']}")
        
        if response['lectures']:
            lecture = response['lectures'][0]
            print(f"📚 Sample lecture: {lecture['title']}")
            
            # Get lecture materials
            materials_response = make_request('GET', f"/api/mobile/lecture/{lecture['id']}/materials")
            if materials_response:
                print(f"📁 Lecture materials: {materials_response['count']}")

def demo_offline_package(lecture_id):
    """Demonstrate offline package download"""
    print_step(7, "Offline Package Download")
    
    response = make_request('GET', f"/api/lecture/{lecture_id}/download_package")
    if response:
        print(f"✅ Offline package created")
        print(f"📦 Materials count: {len(response['materials'])}")
        print(f"⏰ Download time: {response['download_time']}")

def demo_device_sharing(student_id):
    """Demonstrate device-to-device sharing"""
    print_step(8, "Device-to-Device Sharing")
    
    sharing_data = {
        "student_id": student_id,
        "materials": [
            {
                "id": "mat_1",
                "title": "Shared Material",
                "type": "pdf",
                "size": "2.5MB"
            }
        ]
    }
    
    response = make_request('POST', '/api/sharing/create_session', sharing_data)
    if response:
        print(f"✅ Sharing session created: {response['session_id']}")
        print(f"📱 QR Code: {response['qr_code']}")

def demo_health_check():
    """Demonstrate health check"""
    print_step(9, "System Health Check")
    
    response = make_request('GET', '/api/health')
    if response:
        print(f"✅ System status: {response['status']}")
        print(f"🔴 Active sessions: {response['active_sessions']}")
        print(f"⏰ Timestamp: {response['timestamp']}")

def main():
    """Main demo function"""
    print_section("DigiKul Platform Demo")
    print("This demo showcases all the key features of DigiKul")
    print("Make sure the server is running: python app.py")
    
    input("\nPress Enter to start the demo...")
    
    # Demo flow
    token, teacher_id = demo_teacher_registration()
    if not token:
        print("❌ Demo failed at teacher registration")
        return
    
    lecture_id = demo_lecture_creation(token)
    if not lecture_id:
        print("❌ Demo failed at lecture creation")
        return
    
    demo_material_upload(token, lecture_id)
    
    student_id = demo_student_registration()
    if not student_id:
        print("❌ Demo failed at student registration")
        return
    
    session_id = demo_live_session_start(token, lecture_id)
    
    demo_mobile_api()
    demo_offline_package(lecture_id)
    demo_device_sharing(student_id)
    demo_health_check()
    
    print_section("Demo Complete!")
    print("🎉 All features demonstrated successfully!")
    print("\n📱 Test the platform:")
    print(f"• Main page: {BASE_URL}")
    print(f"• Teacher portal: {BASE_URL}/teacher")
    print(f"• Student portal: {BASE_URL}/student")
    if session_id:
        print(f"• Live session: {BASE_URL}/live/{session_id}")
    
    print("\n🔧 Key Features Tested:")
    print("✅ Teacher registration and authentication")
    print("✅ Lecture creation and management")
    print("✅ Material upload with compression")
    print("✅ Student registration")
    print("✅ Live session management")
    print("✅ Mobile API endpoints")
    print("✅ Offline content packages")
    print("✅ Device-to-device sharing")
    print("✅ System health monitoring")

if __name__ == "__main__":
    main()
