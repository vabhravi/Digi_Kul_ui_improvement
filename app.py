from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
try:
    from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
except ImportError:
    print("Flask-SocketIO not installed. Install with: pip install flask-socketio")
    SocketIO = None
    emit = join_room = leave_room = rooms = None
from werkzeug.utils import secure_filename
import os
import uuid
import json
import threading
import time
from datetime import datetime
from config import Config
from utils.database import DatabaseManager
from utils.compression import compress_audio, compress_image, compress_pdf, get_file_type
from utils.auth import token_required, generate_token

# Initialize the database
db = DatabaseManager()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins="*")

if SocketIO:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
else:
    socketio = None

# Global session storage for active sessions
active_sessions = {}
session_participants = {}

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
os.makedirs(os.path.join(app.config['COMPRESSED_FOLDER'], 'audio'), exist_ok=True)
os.makedirs(os.path.join(app.config['COMPRESSED_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['COMPRESSED_FOLDER'], 'documents'), exist_ok=True)

@app.route('/api/register', methods=['POST'])
def register_teacher():
    """Register a new teacher"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'email', 'institution', 'subject']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        teacher_id, response = DatabaseManager.create_teacher(
            data['name'], data['email'], data['institution'], data['subject']
        )
        
        # Generate token for immediate login
        token = generate_token(teacher_id)
        
        return jsonify({
            'message': 'Teacher registered successfully',
            'teacher_id': teacher_id,
            'token': token
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_teacher():
    """Login for existing teachers"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        # Get teacher by email
        teacher = DatabaseManager.get_teacher_by_email(data['email'])
        
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404
        
        # In a real implementation, we would verify a password here
        # For this simplified version, we'll just return a token
        
        token = generate_token(teacher['id'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'teacher_id': teacher['id'],
            'teacher_name': teacher['name']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lectures', methods=['POST'])
@token_required
def create_lecture(current_user):
    """Create a new lecture schedule"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['title', 'description', 'scheduled_time', 'duration']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        lecture_id, response = DatabaseManager.create_lecture(
            current_user, data['title'], data['description'], 
            data['scheduled_time'], data['duration']
        )
        
        return jsonify({
            'message': 'Lecture created successfully',
            'lecture_id': lecture_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lectures', methods=['GET'])
@token_required
def get_lectures(current_user):
    """Get all lectures for a teacher"""
    try:
        lectures = DatabaseManager.get_teacher_lectures(current_user)
        return jsonify(lectures), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_material', methods=['POST'])
@token_required
def upload_material(current_user):
    """Upload teaching material with automatic compression"""
    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get form data
        lecture_id = request.form.get('lecture_id')
        title = request.form.get('title', 'Untitled')
        description = request.form.get('description', '')
        
        if not lecture_id:
            return jsonify({'error': 'Lecture ID is required'}), 400
        
        # Secure filename and determine file type
        filename = secure_filename(file.filename)
        file_type = get_file_type(filename)
        
        # Create appropriate directories
        upload_subdir = os.path.join(app.config['UPLOAD_FOLDER'], file_type + 's')
        compressed_subdir = os.path.join(app.config['COMPRESSED_FOLDER'], file_type + 's')
        os.makedirs(upload_subdir, exist_ok=True)
        os.makedirs(compressed_subdir, exist_ok=True)
        
        # Save original file
        original_filename = f"{uuid.uuid4()}_{filename}"
        original_path = os.path.join(upload_subdir, original_filename)
        file.save(original_path)
        
        # Compress based on file type
        compressed_filename = f"compressed_{original_filename}"
        compressed_path = os.path.join(compressed_subdir, compressed_filename)
        
        original_size = os.path.getsize(original_path)
        
        if file_type == 'audio':
            compressed_size = compress_audio(original_path, compressed_path)
        elif file_type == 'image':
            compressed_size = compress_image(original_path, compressed_path)
        elif file_type == 'document':
            if filename.lower().endswith('.pdf'):
                compressed_size = compress_pdf(original_path, compressed_path)
            else:
                # For other document types, just copy for now
                with open(original_path, 'rb') as f_in:
                    with open(compressed_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                compressed_size = original_size
        else:
            # For other file types, just copy
            with open(original_path, 'rb') as f_in:
                with open(compressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            compressed_size = original_size
        
        # Save to database
        material_id, response = DatabaseManager.add_material(
            lecture_id, title, description, original_path, 
            compressed_path, compressed_size, file_type
        )
        
        return jsonify({
            'message': 'File uploaded and compressed successfully',
            'material_id': material_id,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': f"{((original_size - compressed_size) / original_size * 100):.2f}%"
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz', methods=['POST'])
@token_required
def create_quiz(current_user):
    """Create a quiz for a lecture"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['lecture_id', 'question', 'options', 'correct_answer']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        quiz_id, response = DatabaseManager.create_quiz(
            data['lecture_id'], data['question'], 
            data['options'], data['correct_answer']
        )
        
        return jsonify({
            'message': 'Quiz created successfully',
            'quiz_id': quiz_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/poll', methods=['POST'])
@token_required
def create_poll(current_user):
    """Create a poll for a lecture"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['lecture_id', 'question', 'options']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        poll_id, response = DatabaseManager.create_poll(
            data['lecture_id'], data['question'], data['options']
        )
        
        return jsonify({
            'message': 'Poll created successfully',
            'poll_id': poll_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/discussion', methods=['POST'])
@token_required
def add_discussion_message(current_user):
    """Add a message to discussion board"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['lecture_id', 'message']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        message_id, response = DatabaseManager.add_discussion_message(
            data['lecture_id'], current_user, data['message']
        )
        
        return jsonify({
            'message': 'Discussion message added successfully',
            'message_id': message_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lecture/<lecture_id>/materials', methods=['GET'])
@token_required
def get_lecture_materials(current_user, lecture_id):
    """Get all materials for a lecture"""
    try:
        materials = DatabaseManager.get_lecture_materials(lecture_id)
        return jsonify(materials), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<material_id>', methods=['GET'])
@token_required
def download_material(current_user, material_id):
    """Download teaching material (returns compressed version)"""
    try:
        material = DatabaseManager.get_material_details(material_id)
        
        if not material:
            return jsonify({'error': 'Material not found'}), 404
        
        # Check if file exists
        if not os.path.exists(material['compressed_path']):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(material['compressed_path'], as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebRTC Signaling Endpoints
@socketio.on('join_session')
def handle_join_session(data):
    """Handle joining a live session"""
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    user_type = data.get('user_type')  # 'teacher' or 'student'
    user_name = data.get('user_name')
    
    if not all([session_id, user_id, user_type]):
        emit('error', {'message': 'Missing required fields'})
        return
    
    # Join the session room
    join_room(session_id)
    
    # Store participant info
    if session_id not in session_participants:
        session_participants[session_id] = {}
    
    session_participants[session_id][user_id] = {
        'user_type': user_type,
        'user_name': user_name,
        'socket_id': request.sid,
        'joined_at': datetime.now().isoformat()
    }
    
    # Notify others in the session
    emit('user_joined', {
        'user_id': user_id,
        'user_name': user_name,
        'user_type': user_type,
        'participants_count': len(session_participants[session_id])
    }, room=session_id, include_self=False)
    
    # Send current participants to the joining user
    emit('session_info', {
        'session_id': session_id,
        'participants': list(session_participants[session_id].values()),
        'participants_count': len(session_participants[session_id])
    })

@socketio.on('leave_session')
def handle_leave_session(data):
    """Handle leaving a live session"""
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    
    if session_id and user_id:
        leave_room(session_id)
        
        if session_id in session_participants and user_id in session_participants[session_id]:
            del session_participants[session_id][user_id]
            
            # Notify others
            emit('user_left', {
                'user_id': user_id,
                'participants_count': len(session_participants[session_id])
            }, room=session_id)

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer"""
    session_id = data.get('session_id')
    target_user_id = data.get('target_user_id')
    offer = data.get('offer')
    
    if session_id in session_participants and target_user_id in session_participants[session_id]:
        target_socket_id = session_participants[session_id][target_user_id]['socket_id']
        emit('webrtc_offer', {
            'offer': offer,
            'from_user_id': data.get('from_user_id')
        }, room=target_socket_id)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    """Handle WebRTC answer"""
    session_id = data.get('session_id')
    target_user_id = data.get('target_user_id')
    answer = data.get('answer')
    
    if session_id in session_participants and target_user_id in session_participants[session_id]:
        target_socket_id = session_participants[session_id][target_user_id]['socket_id']
        emit('webrtc_answer', {
            'answer': answer,
            'from_user_id': data.get('from_user_id')
        }, room=target_socket_id)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """Handle ICE candidate"""
    session_id = data.get('session_id')
    target_user_id = data.get('target_user_id')
    candidate = data.get('candidate')
    
    if session_id in session_participants and target_user_id in session_participants[session_id]:
        target_socket_id = session_participants[session_id][target_user_id]['socket_id']
        emit('ice_candidate', {
            'candidate': candidate,
            'from_user_id': data.get('from_user_id')
        }, room=target_socket_id)

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages during live sessions"""
    session_id = data.get('session_id')
    message = data.get('message')
    user_id = data.get('user_id')
    user_name = data.get('user_name')
    
    if session_id and message:
        emit('chat_message', {
            'message': message,
            'user_id': user_id,
            'user_name': user_name,
            'timestamp': datetime.now().isoformat()
        }, room=session_id)

@socketio.on('quality_report')
def handle_quality_report(data):
    """Handle connection quality reports for adaptive streaming"""
    session_id = data.get('session_id')
    quality_data = data.get('quality_data')
    
    # Store quality data for analytics
    if session_id not in active_sessions:
        active_sessions[session_id] = {}
    
    if 'quality_reports' not in active_sessions[session_id]:
        active_sessions[session_id]['quality_reports'] = []
    
    active_sessions[session_id]['quality_reports'].append({
        'timestamp': datetime.now().isoformat(),
        'quality_data': quality_data
    })

# Live Session Management APIs
@app.route('/api/live_session/start', methods=['POST'])
@token_required
def start_live_session(current_user):
    """Start a live session for a lecture"""
    try:
        data = request.get_json()
        lecture_id = data.get('lecture_id')
        
        if not lecture_id:
            return jsonify({'error': 'Lecture ID is required'}), 400
        
        # Create session ID
        session_id = f"session_{lecture_id}_{uuid.uuid4().hex[:8]}"
        
        # Initialize session
        active_sessions[session_id] = {
            'lecture_id': lecture_id,
            'teacher_id': current_user,
            'started_at': datetime.now().isoformat(),
            'status': 'active',
            'participants': [],
            'recordings': []
        }
        
        return jsonify({
            'session_id': session_id,
            'message': 'Live session started successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live_session/<session_id>/stop', methods=['POST'])
@token_required
def stop_live_session(current_user, session_id):
    """Stop a live session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        if session['teacher_id'] != current_user:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update session status
        session['status'] = 'ended'
        session['ended_at'] = datetime.now().isoformat()
        
        # Notify all participants
        if socketio:
            socketio.emit('session_ended', {'session_id': session_id}, room=session_id)
        
        return jsonify({'message': 'Session stopped successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live_session/<session_id>/join', methods=['POST'])
def join_live_session(session_id):
    """Join a live session (for students)"""
    try:
        data = request.get_json()
        student_name = data.get('student_name')
        student_id = data.get('student_id', str(uuid.uuid4()))
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        if active_sessions[session_id]['status'] != 'active':
            return jsonify({'error': 'Session is not active'}), 400
        
        return jsonify({
            'session_id': session_id,
            'student_id': student_id,
            'message': 'Successfully joined session'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Student Registration APIs
@app.route('/api/students/register', methods=['POST'])
def register_student():
    """Register a new student"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'email', 'institution']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        student_id = str(uuid.uuid4())
        
        # In a real implementation, you would save this to database
        # For now, we'll just return the student ID
        
        return jsonify({
            'message': 'Student registered successfully',
            'student_id': student_id,
            'name': data['name']
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lectures/public', methods=['GET'])
def get_public_lectures():
    """Get all public lectures for students to join"""
    try:
        # Get all active lectures
        lectures = DatabaseManager.get_all_lectures()
        
        # Filter for upcoming or active lectures
        current_time = datetime.now().isoformat()
        active_lectures = []
        
        for lecture in lectures:
            if lecture['scheduled_time'] >= current_time:
                # Check if there's an active session
                session_active = any(
                    session['lecture_id'] == lecture['id'] and session['status'] == 'active'
                    for session in active_sessions.values()
                )
                lecture['session_active'] = session_active
                active_lectures.append(lecture)
        
        return jsonify(active_lectures), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Android-Compatible API Endpoints
@app.route('/api/mobile/register_student', methods=['POST'])
def mobile_register_student():
    """Mobile app student registration endpoint"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'email', 'institution']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        student_id, response = DatabaseManager.create_student(
            data['name'], data['email'], data['institution']
        )
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'message': 'Student registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mobile/lectures/available', methods=['GET'])
def mobile_get_available_lectures():
    """Mobile app endpoint to get available lectures"""
    try:
        lectures = DatabaseManager.get_all_lectures()
        current_time = datetime.now().isoformat()
        
        available_lectures = []
        for lecture in lectures:
            if lecture['scheduled_time'] >= current_time:
                session_active = any(
                    session['lecture_id'] == lecture['id'] and session['status'] == 'active'
                    for session in active_sessions.values()
                )
                lecture['session_active'] = session_active
                lecture['can_join'] = True
                available_lectures.append(lecture)
        
        return jsonify({
            'success': True,
            'lectures': available_lectures,
            'count': len(available_lectures)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mobile/lecture/<lecture_id>/materials', methods=['GET'])
def mobile_get_lecture_materials(lecture_id):
    """Mobile app endpoint to get lecture materials"""
    try:
        materials = DatabaseManager.get_lecture_materials(lecture_id)
        
        # Add download URLs and file info
        for material in materials:
            material['download_url'] = f"/api/download/{material['id']}"
            material['file_size_mb'] = round(material['file_size'] / (1024 * 1024), 2)
        
        return jsonify({
            'success': True,
            'materials': materials,
            'count': len(materials)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mobile/quiz/<lecture_id>', methods=['GET'])
def mobile_get_lecture_quiz(lecture_id):
    """Mobile app endpoint to get lecture quiz"""
    try:
        # This would be implemented to get quiz questions
        quiz_questions = []  # Placeholder
        
        return jsonify({
            'success': True,
            'quiz': {
                'lecture_id': lecture_id,
                'questions': quiz_questions
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mobile/quiz/submit', methods=['POST'])
def mobile_submit_quiz():
    """Mobile app endpoint to submit quiz answers"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['student_id', 'quiz_id', 'answers']):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Submit each answer
        for answer in data['answers']:
            DatabaseManager.submit_quiz_response(
                data['student_id'], 
                answer['question_id'], 
                answer['response']
            )
        
        return jsonify({
            'success': True,
            'message': 'Quiz submitted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mobile/session/join', methods=['POST'])
def mobile_join_session():
    """Mobile app endpoint to join live session"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['session_id', 'student_id', 'student_name']):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        session_id = data['session_id']
        
        if session_id not in active_sessions:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        if active_sessions[session_id]['status'] != 'active':
            return jsonify({'success': False, 'error': 'Session is not active'}), 400
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'student_id': data['student_id'],
            'message': 'Successfully joined session'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Offline Content APIs
@app.route('/api/lecture/<lecture_id>/download_package', methods=['GET'])
def download_lecture_package(lecture_id):
    """Download complete lecture package for offline use"""
    try:
        # Get all materials for the lecture
        materials = DatabaseManager.get_lecture_materials(lecture_id)
        
        # Create a package info file
        package_info = {
            'lecture_id': lecture_id,
            'download_time': datetime.now().isoformat(),
            'materials': []
        }
        
        for material in materials:
            package_info['materials'].append({
                'id': material['id'],
                'title': material['title'],
                'description': material['description'],
                'file_type': material['file_type'],
                'download_url': f"/api/download/{material['id']}"
            })
        
        return jsonify(package_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Session Recording APIs
@app.route('/api/session/<session_id>/start_recording', methods=['POST'])
@token_required
def start_session_recording(current_user, session_id):
    """Start recording a live session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        if session['teacher_id'] != current_user:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Initialize recording
        session['recording'] = {
            'started_at': datetime.now().isoformat(),
            'status': 'recording',
            'participants': list(session_participants.get(session_id, {}).keys())
        }
        
        # Notify participants
        if socketio:
            socketio.emit('recording_started', {
                'session_id': session_id,
                'started_by': current_user
            }, room=session_id)
        
        return jsonify({
            'message': 'Recording started successfully',
            'recording_id': f"rec_{session_id}_{int(time.time())}"
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>/stop_recording', methods=['POST'])
@token_required
def stop_session_recording(current_user, session_id):
    """Stop recording a live session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        if session['teacher_id'] != current_user:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if 'recording' not in session:
            return jsonify({'error': 'No active recording'}), 400
        
        # Stop recording
        session['recording']['status'] = 'completed'
        session['recording']['ended_at'] = datetime.now().isoformat()
        
        # Notify participants
        if socketio:
            socketio.emit('recording_stopped', {
                'session_id': session_id,
                'stopped_by': current_user
            }, room=session_id)
        
        return jsonify({
            'message': 'Recording stopped successfully',
            'recording': session['recording']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Device-to-Device Sharing APIs
@app.route('/api/sharing/create_session', methods=['POST'])
def create_sharing_session():
    """Create a local sharing session for device-to-device content sharing"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        materials = data.get('materials', [])
        
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        # Create sharing session
        session_id = f"share_{uuid.uuid4().hex[:8]}"
        
        sharing_sessions = getattr(app, 'sharing_sessions', {})
        sharing_sessions[session_id] = {
            'created_by': student_id,
            'materials': materials,
            'created_at': datetime.now().isoformat(),
            'participants': [student_id]
        }
        app.sharing_sessions = sharing_sessions
        
        return jsonify({
            'session_id': session_id,
            'qr_code': f"digikul://share/{session_id}",
            'message': 'Sharing session created'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sharing/<session_id>/join', methods=['POST'])
def join_sharing_session(session_id):
    """Join a local sharing session"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        sharing_sessions = getattr(app, 'sharing_sessions', {})
        
        if session_id not in sharing_sessions:
            return jsonify({'error': 'Sharing session not found'}), 404
        
        session = sharing_sessions[session_id]
        if student_id not in session['participants']:
            session['participants'].append(student_id)
        
        return jsonify({
            'session_id': session_id,
            'materials': session['materials'],
            'participants': session['participants'],
            'message': 'Joined sharing session successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sharing/<session_id>/materials', methods=['GET'])
def get_sharing_session_materials(session_id):
    """Get materials from a sharing session"""
    try:
        sharing_sessions = getattr(app, 'sharing_sessions', {})
        
        if session_id not in sharing_sessions:
            return jsonify({'error': 'Sharing session not found'}), 404
        
        session = sharing_sessions[session_id]
        
        return jsonify({
            'materials': session['materials'],
            'participants_count': len(session['participants'])
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len([s for s in active_sessions.values() if s['status'] == 'active'])
    }), 200

# HTML Templates for Testing
@app.route('/')
def index():
    """Main testing page"""
    return render_template('index.html')

@app.route('/teacher')
def teacher_dashboard():
    """Teacher dashboard"""
    return render_template('teacher.html')

@app.route('/student')
def student_dashboard():
    """Student dashboard"""
    return render_template('student.html')

@app.route('/live/<session_id>')
def live_session(session_id):
    """Live session page"""
    return render_template('live_session.html', session_id=session_id)

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    if socketio:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)