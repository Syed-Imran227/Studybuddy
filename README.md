# PDF Chatbot with AI Integration

A powerful Flask-based web application that allows users to upload PDF documents, extract their content (text and images), and interact with the content through an AI-powered chatbot interface.

## 🚀 Features

### 🔐 User Authentication
- **Secure user management** with MongoDB and bcrypt password hashing
- **Session-based authentication** with protected routes
- **User registration and login** system

### 📄 Advanced PDF Processing
- **Multi-threaded PDF processing** using PyMuPDF for optimal performance
- **Intelligent batch processing** with configurable batch sizes
- **Smart processing strategies**:
  - Normal batch processing for smaller PDFs
  - Quick extraction with sampling for very large PDFs (>200 pages)
- **Automatic image extraction** from PDF pages with lazy loading
- **Support for large files** up to 500MB

### 🤖 AI Integration
- **Local Ollama integration** using the "llava" model for privacy and cost control
- **Automated PDF summarization** with intelligent content filtering
- **Multi-modal capabilities** - processes both text and images
- **Intelligent chatbot interface** for contextual document queries
- **Fallback mechanisms** when AI processing fails

### ⚡ Performance Optimizations
- **Intelligent caching system** to avoid redundant AI calls
- **Concurrent processing** with thread pools for faster execution
- **Real-time progress tracking** with detailed status updates
- **Memory-efficient processing** for large documents
- **Automatic file cleanup** system

### 🎨 Modern Web Interface
- **Responsive design** using Bootstrap 5
- **Drag-and-drop file upload** functionality
- **Real-time progress indicators** with detailed status updates
- **Interactive chat interface** for asking questions about PDF content
- **Clean, modern UI** with custom CSS styling

## 🛠️ Technology Stack

### Backend
- **Flask 3.0.2** - Python web framework
- **PyMuPDF 1.22.5** - Advanced PDF processing
- **Ollama 0.1.6** - Local AI model integration
- **MongoDB** - NoSQL database for user management
- **bcrypt 4.1.2** - Password hashing and security
- **pytesseract 0.3.10** - OCR capabilities (optional)

### Frontend
- **HTML5/CSS3/JavaScript** - Modern web technologies
- **Bootstrap 5.3.0** - Responsive CSS framework
- **Font Awesome 6.0.0** - Icon library
- **Google Fonts (Poppins)** - Typography

### Performance & Optimization
- **Threading** - Multi-threaded processing
- **Concurrent.futures** - Thread pool execution
- **File-based caching** - Intelligent response caching
- **Memory management** - Efficient large file handling

## 📋 Prerequisites

- Python 3.8+
- MongoDB (running on localhost:27017)
- Ollama with LLaVA model installed
- Tesseract OCR (optional, for enhanced text extraction)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pdf-chatbot
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**
   - Install and start MongoDB on localhost:27017
   - The application will automatically create the required database and collections

4. **Install and configure Ollama**
   ```bash
   # Install Ollama (follow instructions for your OS)
   # Pull the LLaVA model
   ollama pull llava
   ```

5. **Optional: Install Tesseract OCR**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

## 🏃‍♂️ Running the Application

1. **Start the Flask application**
   ```bash
   python app.py
   ```

2. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Register a new account or login with existing credentials
   - Upload PDF files and start chatting with your documents!

## 📁 Project Structure

```
pdf-chatbot/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── index.html        # Main application interface
│   ├── login.html        # Login page
│   └── register.html     # Registration page
├── static/               # Static assets
│   ├── style.css         # Custom CSS styling
│   ├── auth.css          # Authentication page styling
│   ├── script.js         # Client-side JavaScript
│   └── images/           # Extracted PDF images
├── uploads/              # Temporary PDF uploads
├── summaries/            # Generated PDF summaries
├── cache/                # Caching directory
│   └── summaries/        # Cached AI responses
└── static/images/        # Extracted images from PDFs
```

## 🔧 Configuration

The application includes several configurable parameters in `app.py`:

```python
MAX_WORKERS = min(8, os.cpu_count() or 4)  # Thread pool size
BATCH_SIZE = 20                            # Pages per batch
MAX_IMAGES_PER_BATCH = 5                   # Images per batch
CHUNK_SIZE = 12000                         # Text chunk size
MAX_CONCURRENT_LLM_CALLS = 2               # Concurrent AI calls
MAX_CONTENT_LENGTH = 500 * 1024 * 1024     # 500MB max file size
```

## 🎯 Usage

### 1. User Authentication
- Register a new account or login with existing credentials
- All routes are protected and require authentication

### 2. PDF Upload
- Drag and drop PDF files or click to browse
- Supports files up to 500MB
- Real-time progress tracking during processing

### 3. Document Processing
- Automatic text and image extraction
- AI-powered summarization with caching
- Intelligent batch processing for large documents

### 4. Interactive Chat
- Ask questions about your uploaded PDF content
- Get contextual responses from the AI model
- View extracted images alongside the conversation

## 🔒 Security Features

- **Secure file uploads** with validation and size limits
- **Password hashing** using bcrypt
- **Session management** with Flask sessions
- **Input validation** and sanitization
- **Protected routes** requiring authentication

## 🚀 Performance Features

- **Multi-threaded processing** for faster PDF handling
- **Intelligent caching** to avoid redundant AI calls
- **Batch processing** for optimal resource utilization
- **Memory-efficient** handling of large documents
- **Automatic cleanup** of temporary files

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running on localhost:27017
   - Check if the service is properly started

2. **Ollama Model Not Found**
   - Install Ollama and pull the LLaVA model: `ollama pull llava`
   - Verify the model is available: `ollama list`

3. **Tesseract OCR Issues**
   - Install Tesseract OCR for your operating system
   - The application will work without OCR, but with limited text extraction capabilities

4. **File Upload Errors**
   - Check file size (max 500MB)
   - Ensure the file is a valid PDF
   - Verify upload directory permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PyMuPDF** for excellent PDF processing capabilities
- **Ollama** for providing local AI model integration
- **Flask** for the robust web framework
- **Bootstrap** for the responsive UI components

## 📞 Support

If you encounter any issues or have questions, please:
1. Check the troubleshooting section above
2. Search existing issues in the repository
3. Create a new issue with detailed information about your problem

---

**Happy PDF Chatting! 🚀📄🤖**
