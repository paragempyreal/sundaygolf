# Fulfil ShipHero Mediator

A comprehensive system for synchronizing product data between Fulfil and ShipHero platforms, featuring both a Python backend and a React TypeScript frontend for configuration management.

## 🏗️ Architecture

This project consists of two main components:

- **Backend**: Python Flask application handling data synchronization
- **Frontend**: React TypeScript application for configuration management

### Node.js Version Details

This project has been tested and developed with:

- **Current System Node.js**: v18.15.0 ✅
- **Project Requirements**: Node.js 14+ ✅
- **Compatibility**: Fully compatible with React 18, TypeScript 4.9, and all dependencies
- **Status**: No version conflicts - ready for development

**Note**: Node.js 18.15.0 is a Long Term Support (LTS) version, providing excellent stability and compatibility for production use.

### Python Version Details (Backend)

The backend API has been tested and developed with:

- **Current System Python**: v3.12.3 ✅
- **Project Requirements**: Python 3.8+ ✅
- **Compatibility**: Fully compatible with Flask, SQLAlchemy, and all dependencies
- **Status**: No version conflicts - ready for development

**Note**: Python 3.12.3 is the latest stable version, providing excellent performance and modern language features for the backend API.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database
- Fulfil API credentials
- ShipHero API credentials

### Automated Setup (Recommended)

Run the setup script from the project root:

```bash
./setup.sh
```

This script will:

- Verify your environment
- Create virtual environments
- Install all dependencies
- Set up environment files
- Provide next steps

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp env.example .env
# Edit .env with your credentials
```

4. Initialize the database:

```bash
python init_database.py
```

5. Start the backend:

```bash
python -m flask run
```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm start
```

The frontend will be available at `http://localhost:3000`

**Default credentials**: `admin` / `admin123`

## 🔧 Configuration

### Backend Configuration

The backend now uses **database-based configuration** instead of environment variables for better security and management:

**Required Environment Variables:**

- `DATABASE_URL`: PostgreSQL connection string

**Database-Stored Configuration:**

- Fulfil API credentials (subdomain, API key)
- ShipHero API credentials (refresh token, OAuth URL, API base URL)
- System settings (poll interval, secret keys)

**Benefits:**

- 🔒 **Secure**: Credentials stored encrypted in database
- 🎛️ **Manageable**: Frontend interface for configuration
- 🔄 **Dynamic**: Changes take effect without restart
- 📊 **Auditable**: Track configuration changes

### Frontend Configuration

The frontend provides a user-friendly interface for managing these configurations:

- **Dashboard**: System overview and connection status
- **Configuration Panel**: Manage API credentials and system settings
- **Connection Testing**: Verify API connections before saving

## 📁 Project Structure

```
fulfil-shiphero-mediator/
├── backend/                 # Python Flask backend
│   ├── mediator/           # Main application code
│   │   ├── controllers/    # API endpoints and routes
│   │   ├── services/       # Business logic and API clients
│   │   ├── models/         # Database models
│   │   └── configs/        # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   └── README.md          # Backend documentation
├── frontend/               # React TypeScript frontend
│   ├── src/               # Source code
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service layer
│   │   └── contexts/      # React contexts
│   ├── package.json       # Node.js dependencies
│   └── README.md          # Frontend documentation
└── README.md              # This file
```

## 🔐 Authentication

The system uses JWT tokens for authentication:

- **Backend**: JWT-based authentication with database user management
- **Frontend**: Secure login with token storage and automatic validation
- **Default Admin**: `admin` / `admin123` (created automatically)
- **User Management**: Admin users can create and manage user accounts

## 🔄 Data Synchronization

The backend automatically synchronizes product data:

1. **Polling**: Regularly checks Fulfil for new/updated products
2. **Processing**: Transforms data to ShipHero format
3. **Syncing**: Pushes updates to ShipHero via API
4. **Tracking**: Logs all sync operations and errors

## 🎨 Frontend Features

- **Responsive Design**: Mobile-friendly interface
- **Real-time Status**: Live connection monitoring
- **Configuration Management**: Easy credential management
- **Connection Testing**: Verify API connectivity
- **Toast Notifications**: User feedback and error handling

## 🚀 Development vs Production

### Development

**Backend:**

```bash
cd backend
source venv/bin/activate  # or source env/bin/activate
python -m flask --app app run # or venv/bin/python -m flask --app app run
```

**Frontend:**

```bash
cd frontend
npm start
```

### Production

**Backend:**

- Use a production WSGI server (Gunicorn, uWSGI)
- Set up proper environment variables
- Configure database connections
- Implement proper user authentication

**Frontend:**

- Build the application: `npm run build`
- Serve static files from a web server
- Configure environment variables
- Set up HTTPS

## 🛠️ Development

### Backend Development

- Use virtual environments
- Follow PEP 8 style guidelines
- Add proper error handling
- Write tests for new features

### Frontend Development

- Use TypeScript for type safety
- Follow React best practices
- Maintain consistent styling with Tailwind CSS
- Test on multiple screen sizes

## 📊 Monitoring

The system provides monitoring capabilities:

- **Sync Status**: Track synchronization operations
- **Error Logging**: Monitor and debug issues
- **Connection Health**: Verify API connectivity
- **Performance Metrics**: Monitor sync performance

## 🔒 Security

- JWT token authentication
- API key encryption
- CORS configuration
- Input validation
- Secure credential storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is part of the Fulfil ShipHero Mediator system.

## 🆘 Support

For issues and questions:

1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information
4. Contact the development team

## 🔄 Updates

Stay updated with the latest changes:

- Monitor the repository for updates
- Review changelog and release notes
- Test updates in development environment
- Plan production deployments carefully
