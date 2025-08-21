#!/bin/bash

# Fulfil ShipHero Mediator - Complete Setup Script

echo "🚀 Setting up Fulfil ShipHero Mediator Project..."
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "✅ Project structure verified"
echo ""

# Backend Setup
echo "🔧 Setting up Backend..."
cd backend

# Check Python installation
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Python found: $($PYTHON_CMD --version)"

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d "env" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi

echo "✅ Virtual environment activated"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✅ Python dependencies installed"

# Initialize database
echo "🗄️  Initializing database..."
python init_database.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize database"
    exit 1
fi
echo "✅ Database initialized"

# Check for environment file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file from env.example"
        echo "   Please review and update the .env file with your credentials"
    else
        echo "❌ env.example file not found. Please create a .env file manually."
    fi
fi

cd ..
echo "✅ Backend setup completed"
echo ""

# Frontend Setup
echo "🎨 Setting up Frontend..."
cd frontend

# Check Node.js installation
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) and npm $(npm -v) are installed"

# Check for environment file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file from env.example"
        echo "   Please review and update the .env file with your configuration"
    else
        echo "❌ env.example file not found. Please create a .env file manually."
    fi
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi
echo "✅ Node.js dependencies installed"

cd ..
echo "✅ Frontend setup completed"
echo ""

# Final instructions
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your environment files:"
echo "   - Backend: backend/.env"
echo "   - Frontend: frontend/.env"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate  # or source env/bin/activate"
echo "   python -m flask run"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "4. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend: http://localhost:5000"
echo "   - Login: admin / admin123"
echo ""
echo "📚 For more information, see the README.md files in each directory"
echo ""
echo "🚀 Development Commands:"
echo "   Frontend: npm start (dev) | npm run build (production)"
echo "   Backend: python -m flask run (dev) | gunicorn (production)"
echo ""
echo "📖 For production deployment, see the README.md files"
echo ""
echo "Happy coding! 🚀"
