# 🎓 DigiKul - Low Bandwidth E-Learning Platform

A comprehensive e-learning platform designed specifically for rural areas with limited internet connectivity. DigiKul provides audio-first live classes, offline content delivery, and device-to-device sharing capabilities optimized for 2G/3G networks.

## 🌟 Key Features

### 🎤 Audio-First Live Classes
- **WebRTC Integration**: Real-time communication with adaptive quality
- **Audio Priority**: Prioritizes audio streams over video for low bandwidth
- **Adaptive Bitrate**: Automatically adjusts quality based on network conditions
- **Push-to-Talk**: Bandwidth optimization for student interactions

### 📱 Mobile-First Design
- **Responsive Interface**: Works seamlessly on smartphones and tablets
- **Offline Mode**: Download materials for offline access
- **Progressive Web App**: Can be installed on mobile devices
- **Touch-Optimized**: Intuitive touch controls for all interactions

### 🌐 Low Bandwidth Optimization
- **Smart Compression**: Automatic compression of audio, images, and documents
- **Quality Monitoring**: Real-time bandwidth and quality monitoring
- **Fallback Mechanisms**: Graceful degradation when connectivity is poor
- **Efficient Signaling**: Minimal overhead WebSocket communication

### 📚 Asynchronous Learning
- **Content Download**: Download complete lecture packages
- **Offline Quizzes**: Interactive assessments that work offline
- **Local Storage**: Cached materials for offline access
- **Sync on Connect**: Automatic synchronization when online

### 🤝 Device-to-Device Sharing
- **Local Network Sharing**: Share content via Wi-Fi Direct
- **QR Code Integration**: Easy session joining via QR codes
- **Peer-to-Peer**: Direct device communication without internet
- **Content Distribution**: Efficient content sharing among nearby devices

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DigiKul_TeachersPortal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the platform**
   - Open your browser and go to `http://localhost:5000`
   - Teacher Portal: `http://localhost:5000/teacher`
   - Student Portal: `http://localhost:5000/student`

## 📖 API Documentation

### Authentication Endpoints
- `POST /api/register` - Teacher registration
- `POST /api/login` - Teacher login
- `POST /api/students/register` - Student registration

### Lecture Management
- `POST /api/lectures` - Create new lecture
- `GET /api/lectures` - Get teacher's lectures
- `GET /api/lectures/public` - Get public lectures for students

### Live Sessions
- `POST /api/live_session/start` - Start live session
- `POST /api/live_session/<session_id>/stop` - Stop live session
- `POST /api/live_session/<session_id>/join` - Join live session

### Content Management
- `POST /api/upload_material` - Upload teaching material
- `GET /api/lecture/<lecture_id>/materials` - Get lecture materials
- `GET /api/download/<material_id>` - Download material (compressed)

### Mobile App Endpoints
- `POST /api/mobile/register_student` - Mobile student registration
- `GET /api/mobile/lectures/available` - Get available lectures
- `GET /api/mobile/lecture/<lecture_id>/materials` - Get materials for mobile
- `POST /api/mobile/session/join` - Join session from mobile

### Device Sharing
- `POST /api/sharing/create_session` - Create sharing session
- `POST /api/sharing/<session_id>/join` - Join sharing session
- `GET /api/sharing/<session_id>/materials` - Get shared materials

## 🔧 Configuration

### Environment Variables
```env
# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Application Settings
SECRET_KEY=your_secret_key
MAX_CONTENT_LENGTH=10485760

# WebRTC Configuration
SOCKETIO_CORS_ALLOWED_ORIGINS=*
SOCKETIO_ASYNC_MODE=threading
```

### Compression Settings
```python
# Audio compression
AUDIO_BITRATE = '48k'  # Adjust for bandwidth

# Image compression
IMAGE_QUALITY = 30  # Lower = more compression

# PDF compression
PDF_COMPRESSION_LEVEL = 3  # 1-9, higher = more compression
```

## 📱 Mobile App Integration

### Android API Usage
The platform provides RESTful APIs specifically designed for mobile app integration:

```javascript
// Register student
const response = await fetch('/api/mobile/register_student', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        name: 'John Doe',
        email: 'john@example.com',
        institution: 'Rural College'
    })
});

// Get available lectures
const lectures = await fetch('/api/mobile/lectures/available');

// Join live session
const session = await fetch('/api/mobile/session/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: 'session_123',
        student_id: 'student_456',
        student_name: 'John Doe'
    })
});
```

### WebRTC Integration
For mobile apps, integrate WebRTC using the signaling server:

```javascript
// Connect to signaling server
const socket = io('http://your-server:5000');

// Join session
socket.emit('join_session', {
    session_id: 'session_123',
    user_id: 'student_456',
    user_type: 'student',
    user_name: 'John Doe'
});

// Handle WebRTC offers/answers
socket.on('webrtc_offer', async (data) => {
    // Handle WebRTC offer
});
```

## 🌍 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Use a reverse proxy** (Nginx):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /socket.io/ {
           proxy_pass http://127.0.0.1:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

3. **Environment setup**:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your_production_secret_key
   ```

## 📊 Performance Optimization

### For Low Bandwidth Networks
1. **Audio-First Approach**: Prioritize audio over video
2. **Adaptive Quality**: Monitor bandwidth and adjust accordingly
3. **Compression**: Use efficient compression algorithms
4. **Caching**: Implement aggressive caching strategies
5. **Offline Mode**: Allow full offline functionality

### Network Requirements
- **Minimum**: 100 Kbps for audio-only
- **Recommended**: 500 Kbps for audio + low-quality video
- **Optimal**: 1 Mbps for full functionality

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **File Validation**: Strict file type and size validation
- **CORS Protection**: Configurable CORS settings
- **Input Sanitization**: Protection against injection attacks

## 🧪 Testing

### Run Tests
```bash
python test_backend.py
```

### Test Coverage
- Authentication flows
- File upload and compression
- WebRTC signaling
- Database operations
- API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

## 🎯 Roadmap

- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Advanced offline synchronization
- [ ] Integration with learning management systems
- [ ] Mobile app development (iOS/Android)
- [ ] Advanced AI-powered content recommendations

## 🙏 Acknowledgments

- WebRTC community for real-time communication
- Flask and SocketIO for the backend framework
- Open source contributors
- Rural education advocates

---

**Built with ❤️ for rural education**