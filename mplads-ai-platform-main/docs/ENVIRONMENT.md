# Environment Configuration Guide

This file documents all environment variables used in the MPLADS AI Platform.

## Backend Environment Variables (.env)

Create a `.env` file in the project root with the following variables:

### Database Configuration

#### Option 1: SQLite (Default - Zero Config)
```env
DATABASE_URL=sqlite+aiosqlite:///./backend/mplads.db
```

#### Option 2: PostgreSQL (Production)
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/mplads_db
```

#### Option 3: PostgreSQL with Supabase
```env
DATABASE_URL=postgresql+asyncpg://postgres.projectref:password@aws-0-region.pooler.supabase.com:6543/postgres
```

### Server Configuration
```env
# Backend server host and port
HOST=0.0.0.0
PORT=8000
```

### Ollama LLM Configuration (Optional)
```env
# Local Ollama endpoint
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3
```

### Additional Optional Variables
```env
# JWT Secret for authentication (if implementing auth)
JWT_SECRET=your-secret-key-here

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Debug mode
DEBUG=false

# Log level
LOG_LEVEL=INFO
```

## Frontend Environment Variables

The frontend uses Vite's environment system. Create `.env.local` in the `frontend/` directory:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# App name
VITE_APP_NAME=MPLADS AI Platform

# Environment
VITE_ENV=development
```

## Environment-Specific Files

### Development
- `.env` - Local development (gitignored)
- `.env.local` - Local overrides (gitignored)

### Production
- `.env.production` - Production settings (deploy via CI/CD)
- Use environment variables in your hosting platform

### Example
- `.env.example` - Template file (committed to git)

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong passwords** for database connections
3. **Rotate secrets regularly** in production
4. **Use environment-specific configs** for different stages
5. **Validate environment variables** on startup

## Verifying Configuration

Run this command to check if environment is set up correctly:

```bash
# Backend
cd backend
source venv/bin/activate
python -c "from app.database import engine; print('✅ Database connection OK')"

# Frontend
cd frontend
npm run dev
```

## Troubleshooting

### Database Connection Issues
- Check DATABASE_URL format
- Verify database server is running
- Check network connectivity
- Verify credentials

### Ollama Issues
- Ollama is optional - system will use fallback
- Check if Ollama is running: `curl http://localhost:11434`
- Verify model is downloaded: `ollama list`

### CORS Issues
- Add your frontend URL to CORS_ORIGINS
- Check browser console for specific errors
- Verify backend allows the origin

---

**Need help?** Check the documentation in `/docs` or open an issue.
