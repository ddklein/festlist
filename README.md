# 🎵 FestList

**Transform festival flyers into Spotify playlists with AI**

FestList is a web application that uses AI-powered image analysis to extract artist names from festival flyers and automatically create Spotify playlists. Simply upload a festival poster, let our AI identify the artists, and generate a playlist to discover the music before the event!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-19.1.1-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

## ✨ Features

- 🖼️ **AI-Powered Image Analysis** - Upload festival flyers and let Google Gemini Vision AI extract artist names
- 🎯 **Smart Artist Detection** - Advanced AI identifies artists with confidence scoring
- 🎵 **Automatic Playlist Creation** - Generate Spotify playlists with top tracks from detected artists
- ✏️ **Manual Editing** - Review, add, or remove artists before creating your playlist
- 🎨 **Modern UI** - Clean, responsive interface built with React and Material-UI
- 🔒 **Secure Authentication** - OAuth 2.0 integration with Spotify
- ⚡ **Fast Processing** - Optimized backend with rate limiting and caching

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Tesseract OCR** (for local development without Docker)
- **Google Cloud Account** (for Gemini AI API)
- **Spotify Developer Account** (for playlist creation)

### Installation

#### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/festlist.git
   cd festlist
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

3. **Configure your `.env` file** (see [Configuration](#configuration) section)

4. **Start the application**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

#### Option 2: Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/festlist.git
   cd festlist
   ```

2. **Install Tesseract OCR**
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

3. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   # Edit both .env files with your credentials
   ```

6. **Start the backend**
   ```bash
   cd backend
   python start_server.py
   ```

7. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm start
   ```

## ⚙️ Configuration

### Backend Configuration (`.env`)

Create a `.env` file in the project root with the following variables:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_GEMINI_API_KEY=your-gemini-api-key

# Spotify Configuration
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
SPOTIFY_REDIRECT_URI=http://localhost:3000/callback

# Application Configuration
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# OCR Configuration
OCR_ENGINE=tesseract  # or google_vision
TESSERACT_PATH=/usr/bin/tesseract

# Development
DEBUG=true
LOG_LEVEL=INFO
```

### Frontend Configuration (`frontend/.env`)

```bash
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8000

# Development settings
HOST=localhost
PORT=3000
BROWSER=none
```

### Getting API Credentials

#### Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` as `GOOGLE_GEMINI_API_KEY`

#### Spotify API
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:3000/callback` to Redirect URIs
4. Copy Client ID and Client Secret to your `.env`

#### Google Cloud (Optional - for Vision API)
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Vision API
3. Create a service account and download the JSON key
4. Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your JSON key

## 📖 Usage

1. **Connect Spotify** - Authenticate with your Spotify account
2. **Upload Flyer** - Drag and drop or select a festival flyer image (JPEG, PNG, TIFF, BMP)
3. **Review Artists** - AI extracts artist names; review and edit the list
4. **Create Playlist** - Customize playlist settings and generate your Spotify playlist
5. **Enjoy** - Listen to your new playlist on Spotify!

## 🏗️ Architecture

```
festlist/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic (OCR, AI, Spotify)
│   │   ├── utils/       # Utilities and middleware
│   │   └── main.py      # FastAPI application
│   ├── tests/           # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── services/    # API clients
│   │   └── utils/       # Utilities
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml   # Docker orchestration
└── .env.example         # Environment template
```

### Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- Google Gemini AI - Vision and text AI models
- Tesseract OCR - Text extraction from images
- Spotipy - Spotify API client
- Firebase/Firestore - User data and rate limiting
- Redis - Caching and session management
- Structlog - Structured logging

**Frontend:**
- React 19 - UI framework
- TypeScript - Type safety
- Material-UI - Component library
- Axios - HTTP client
- React Dropzone - File upload

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📦 Deployment

### Production Build

#### Frontend
```bash
cd frontend
npm run build
```

The build artifacts will be in `frontend/build/`.

#### Backend
The backend is production-ready with:
- Structured logging
- Rate limiting
- Security headers
- Error handling
- Request validation

### Deployment Options

#### Docker Compose (Production)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Cloud Platforms
- **Vercel/Netlify** - Frontend (React build)
- **Google Cloud Run** - Backend (containerized)
- **AWS ECS/Fargate** - Full stack
- **Heroku** - Full stack

### Environment Variables for Production
Update your `.env` with production URLs:
```bash
BACKEND_URL=https://api.yourdom ain.com
FRONTEND_URL=https://yourdom ain.com
SPOTIFY_REDIRECT_URI=https://yourdom ain.com/callback
DEBUG=false
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Follow code style**
   - Python: Black formatter, Flake8 linter
   - TypeScript: ESLint, Prettier
5. **Write tests** for new features
6. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
7. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**

### Code Style

**Python:**
```bash
# Format code
black backend/

# Lint code
flake8 backend/
```

**TypeScript:**
```bash
# Lint code
cd frontend
npm run lint
```

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove)
- Reference issues when applicable

### Pull Request Guidelines
- Provide a clear description of changes
- Include screenshots for UI changes
- Ensure all tests pass
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) for powerful vision and text AI
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for music integration
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python framework
- [Material-UI](https://mui.com/) for beautiful React components

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/festlist/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/festlist/discussions)
- **Email**: team@festlist.com

## 🗺️ Roadmap

- [ ] Support for Apple Music and Amazon Music
- [ ] Multi-language support for international festivals
- [ ] Mobile app (iOS/Android)
- [ ] Collaborative playlists
- [ ] Festival discovery and recommendations
- [ ] Social sharing features
- [ ] Advanced playlist customization

---

**Made with ❤️ by the FestList Team**

