# Mother of Bots - React Frontend

Modern React frontend for the Mother of Bots Multi-Agent Chat Interface.

## Features

- 🎨 Modern, responsive UI with gradient design
- 💬 Real-time chat interface
- 📎 File upload support (PDF, DOCX, TXT, XLSX)
- 🤖 Full code generation workflow
- ⚙️ Customizable settings
- 🚀 Project deployment monitoring
- 🔗 Integration with Flask API backend

## Tech Stack

- **React 18** - UI framework
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icons
- **CSS3** - Modern styling with animations

## Prerequisites

- Node.js 16+ 
- npm or yarn
- Flask API running on http://localhost:5000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## API Configuration

The app connects to the Flask API at `http://localhost:5000`. 

To change the API URL, update the `API_BASE_URL` constant in `src/App.jsx`:

```javascript
const API_BASE_URL = 'http://your-api-url:port';
```

## Features Overview

### Chat Interface
- Send messages and receive AI-generated responses
- View conversation history
- Real-time processing status updates

### File Upload
- Upload documents to provide context
- Supported formats: PDF, DOCX, DOC, TXT, XLSX, XLS
- View uploaded files and remove them as needed

### Settings
- **Show requirements analysis**: Display detailed requirements analysis in chat
- **Auto-generate code**: Automatically generate code when applicable
- **Deploy generated projects**: Auto-deploy generated applications

### Status Monitoring
- Flask API health check
- Vertex AI connection status
- Deployed services monitoring

## Development

### Project Structure
```
react-frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── App.css          # Application styles
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── package.json         # Dependencies
└── vite.config.js       # Vite configuration
```

### Key Components

- **App.jsx**: Main component containing all chat logic, file handling, and API integration
- **Message rendering**: Supports markdown-like syntax for rich content display
- **File upload**: Drag-and-drop and click-to-upload functionality
- **Status tracking**: Real-time monitoring of processing steps

## Contributing

This is part of the Mother of Bots project. For contributions, please refer to the main project repository.

## License

MIT License

