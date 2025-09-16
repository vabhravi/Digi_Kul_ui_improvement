from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime
from config import Config
from utils.database import DatabaseManager
from utils.compression import compress_audio, compress_image, compress_pdf, get_file_type
from utils.auth import token_required, generate_token

# Initialize the database
db = DatabaseManager()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)