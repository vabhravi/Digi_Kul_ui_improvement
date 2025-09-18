import sqlite3
import uuid
import json
from datetime import datetime

class DatabaseManager:
    _instance = None
    _conn = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._init_db()
        return cls._instance
    
    @classmethod
    def _init_db(cls):
        """Initialize the SQLite database with required tables"""
        cls._conn = sqlite3.connect(':memory:', check_same_thread=False)
        cls._conn.row_factory = sqlite3.Row
        
        # Create tables
        cursor = cls._conn.cursor()
        
        # Teachers table
        cursor.execute('''
            CREATE TABLE teachers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                institution TEXT NOT NULL,
                subject TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Lectures table
        cursor.execute('''
            CREATE TABLE lectures (
                id TEXT PRIMARY KEY,
                teacher_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                scheduled_time TEXT,
                duration INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        ''')
        
        # Materials table
        cursor.execute('''
            CREATE TABLE materials (
                id TEXT PRIMARY KEY,
                lecture_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                file_path TEXT NOT NULL,
                compressed_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                FOREIGN KEY (lecture_id) REFERENCES lectures (id)
            )
        ''')
        
        # Quizzes table
        cursor.execute('''
            CREATE TABLE quizzes (
                id TEXT PRIMARY KEY,
                lecture_id TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lecture_id) REFERENCES lectures (id)
            )
        ''')
        
        # Polls table
        cursor.execute('''
            CREATE TABLE polls (
                id TEXT PRIMARY KEY,
                lecture_id TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                created_at TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (lecture_id) REFERENCES lectures (id)
            )
        ''')
        
        # Discussions table
        cursor.execute('''
            CREATE TABLE discussions (
                id TEXT PRIMARY KEY,
                lecture_id TEXT NOT NULL,
                teacher_id TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (lecture_id) REFERENCES lectures (id),
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        ''')
        
        # Students table
        cursor.execute('''
            CREATE TABLE students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                institution TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Student responses table (for quizzes and polls)
        cursor.execute('''
            CREATE TABLE student_responses (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                quiz_id TEXT,
                poll_id TEXT,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
                FOREIGN KEY (poll_id) REFERENCES polls (id)
            )
        ''')
        
        cls._conn.commit()
    
    @classmethod
    def _execute_query(cls, query, params=()):
        """Execute a query and return the results"""
        cursor = cls._conn.cursor()
        cursor.execute(query, params)
        cls._conn.commit()
        return cursor
    
    @classmethod
    def create_teacher(cls, name, email, institution, subject):
        """Register a new teacher in the database"""
        teacher_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        query = '''
            INSERT INTO teachers (id, name, email, institution, subject, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (teacher_id, name, email, institution, subject, created_at))
        
        return teacher_id, {"data": {"id": teacher_id}}
    
    @classmethod
    def create_lecture(cls, teacher_id, title, description, scheduled_time, duration):
        """Create a new lecture in the database"""
        lecture_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        query = '''
            INSERT INTO lectures (id, teacher_id, title, description, scheduled_time, duration, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (lecture_id, teacher_id, title, description, scheduled_time, duration, created_at))
        
        return lecture_id, {"data": {"id": lecture_id}}
    
    @classmethod
    def add_material(cls, lecture_id, title, description, file_path, compressed_path, file_size, file_type):
        """Add teaching material to the database"""
        material_id = str(uuid.uuid4())
        upload_date = datetime.now().isoformat()
        
        query = '''
            INSERT INTO materials (id, lecture_id, title, description, file_path, compressed_path, file_size, file_type, upload_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (material_id, lecture_id, title, description, file_path, compressed_path, file_size, file_type, upload_date))
        
        return material_id, {"data": {"id": material_id}}
    
    @classmethod
    def create_quiz(cls, lecture_id, question, options, correct_answer):
        """Create a quiz for a lecture"""
        quiz_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Convert options list to JSON string
        options_json = json.dumps(options)
        
        query = '''
            INSERT INTO quizzes (id, lecture_id, question, options, correct_answer, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (quiz_id, lecture_id, question, options_json, correct_answer, created_at))
        
        return quiz_id, {"data": {"id": quiz_id}}
    
    @classmethod
    def create_poll(cls, lecture_id, question, options):
        """Create a poll for a lecture"""
        poll_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Convert options list to JSON string
        options_json = json.dumps(options)
        
        query = '''
            INSERT INTO polls (id, lecture_id, question, options, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (poll_id, lecture_id, question, options_json, created_at, True))
        
        return poll_id, {"data": {"id": poll_id}}
    
    @classmethod
    def add_discussion_message(cls, lecture_id, teacher_id, message):
        """Add a message to the discussion board"""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        query = '''
            INSERT INTO discussions (id, lecture_id, teacher_id, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (message_id, lecture_id, teacher_id, message, timestamp))
        
        return message_id, {"data": {"id": message_id}}
    
    @classmethod
    def get_teacher_lectures(cls, teacher_id):
        """Get all lectures for a teacher"""
        query = 'SELECT * FROM lectures WHERE teacher_id = ? ORDER BY created_at DESC'
        cursor = cls._execute_query(query, (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_lecture_materials(cls, lecture_id):
        """Get all materials for a lecture"""
        query = 'SELECT * FROM materials WHERE lecture_id = ? ORDER BY upload_date DESC'
        cursor = cls._execute_query(query, (lecture_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_material_details(cls, material_id):
        """Get details for a specific material"""
        query = 'SELECT * FROM materials WHERE id = ?'
        cursor = cls._execute_query(query, (material_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @classmethod
    def get_teacher_by_email(cls, email):
        """Get teacher by email (for login)"""
        query = 'SELECT * FROM teachers WHERE email = ?'
        cursor = cls._execute_query(query, (email,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    @classmethod
    def get_all_lectures(cls):
        """Get all lectures (for public access)"""
        query = '''
            SELECT l.*, t.name as teacher_name, t.institution 
            FROM lectures l 
            JOIN teachers t ON l.teacher_id = t.id 
            ORDER BY l.created_at DESC
        '''
        cursor = cls._execute_query(query)
        return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def create_student(cls, name, email, institution):
        """Register a new student"""
        student_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        query = '''
            INSERT INTO students (id, name, email, institution, created_at)
            VALUES (?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (student_id, name, email, institution, created_at))
        
        return student_id, {"data": {"id": student_id}}
    
    @classmethod
    def submit_quiz_response(cls, student_id, quiz_id, response):
        """Submit a quiz response"""
        response_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        query = '''
            INSERT INTO student_responses (id, student_id, quiz_id, response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (response_id, student_id, quiz_id, response, timestamp))
        
        return response_id, {"data": {"id": response_id}}
    
    @classmethod
    def submit_poll_response(cls, student_id, poll_id, response):
        """Submit a poll response"""
        response_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        query = '''
            INSERT INTO student_responses (id, student_id, poll_id, response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        '''
        cls._execute_query(query, (response_id, student_id, poll_id, response, timestamp))
        
        return response_id, {"data": {"id": response_id}}