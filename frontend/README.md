# Fulfil ShipHero Mediator - Frontend

A React TypeScript frontend application for managing Fulfil and ShipHero API configurations and monitoring system status.

## Features

- **Authentication System**: Secure login with JWT tokens
- **Dashboard**: System overview with connection status and quick actions
- **Configuration Management**:
  - Fulfil API credentials (subdomain, API key)
  - ShipHero API credentials (refresh token, OAuth URL, API base URL)
  - System settings (poll interval)
- **Connection Testing**: Test API connections before saving
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Real-time Updates**: Live connection status monitoring

## Prerequisites

- **Node.js**: v18.15.0+ (LTS version recommended)
- **npm**: 9.5.0+
- **Backend API**: Running on `http://localhost:5000`

## Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment file (optional):

```bash
cp .env.example .env
```

3. Start the development server:

```bash
npm start
```

The application will open at `http://localhost:3000`

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## 🚀 Development vs Production

### Development

```bash
npm start
```

Starts the development server with hot reloading at `http://localhost:3000`

### Production

```bash
npm run build
```

Creates an optimized production build in the `build/` folder. Serve these static files from your web server.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.tsx     # Main layout with navigation
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication state management
├── pages/              # Page components
│   ├── Dashboard.tsx   # System overview dashboard
│   ├── Configuration.tsx # Configuration management
│   └── Login.tsx      # Authentication page
├── services/           # API service layer
│   ├── authService.ts  # Authentication API calls
│   └── configService.ts # Configuration API calls
├── App.tsx            # Main application component
└── index.tsx          # Application entry point
```

## 🔐 Authentication

The application uses JWT tokens for authentication with database-based user management:

**Default Admin Credentials:**

- Username: `admin`
- Password: `admin123`

**Features:**

- Secure JWT token authentication
- Database-stored user accounts
- Admin and regular user roles
- Password hashing with bcrypt
- Automatic token validation

**User Management:**

- Admin users can create new accounts
- Role-based access control
- User status management (active/inactive)
- Secure credential storage

## Configuration Management

### Fulfil Configuration

- **Subdomain**: Your Fulfil instance subdomain
- **API Key**: Your Fulfil API key

### ShipHero Configuration

- **Refresh Token**: Your ShipHero OAuth refresh token
- **OAuth URL**: ShipHero OAuth endpoint (default: `https://public-api.shiphero.com/auth/refresh`)
- **API Base URL**: ShipHero API base URL (default: `https://public-api.shiphero.com`)

### System Configuration

- **Poll Interval**: How often to check for new products (1-60 minutes)

## API Endpoints

The frontend communicates with the backend through these endpoints:

- `POST /auth/login` - User authentication
- `GET /auth/validate` - Token validation
- `GET /config` - Get current configuration
- `PUT /config/fulfil` - Update Fulfil configuration
- `PUT /config/shiphero` - Update ShipHero configuration
- `PUT /config/system` - Update system configuration
- `POST /config/fulfil/test` - Test Fulfil connection
- `POST /config/shiphero/test` - Test ShipHero connection

## Styling

The application uses Tailwind CSS for styling with a custom color scheme:

- Primary colors: Blue variants
- Status colors: Green (success), Red (error), Yellow (warning)
- Neutral colors: Gray scale

## Development

### Adding New Features

1. Create new components in `src/components/`
2. Add new pages in `src/pages/`
3. Create new services in `src/services/`
4. Update routing in `App.tsx`

### State Management

- Use React Context for global state (authentication)
- Use local state for component-specific data
- Use services for API communication

### Error Handling

- Toast notifications for user feedback
- Try-catch blocks in async operations
- User-friendly error messages

## Production Build

1. Build the application:

```bash
npm run build
```

2. The build artifacts will be in the `build/` folder

3. Serve the static files from your web server

## Security Considerations

- JWT tokens are stored in localStorage (consider httpOnly cookies for production)
- API keys and tokens are masked in the UI
- HTTPS should be used in production
- Implement proper user authentication and authorization
- Validate all user inputs
- Use environment variables for sensitive configuration

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend has CORS enabled
2. **Authentication Failures**: Check JWT token expiration and backend secret key
3. **API Connection Issues**: Verify backend is running and accessible
4. **Build Errors**: Clear `node_modules` and reinstall dependencies

### Development Tips

- Use browser developer tools to debug API calls
- Check network tab for failed requests
- Verify environment variables are set correctly
- Test on different screen sizes for responsive design

## Contributing

1. Follow the existing code structure and patterns
2. Use TypeScript for type safety
3. Add proper error handling
4. Test your changes thoroughly
5. Update documentation as needed

## License

This project is part of the Fulfil ShipHero Mediator system.
