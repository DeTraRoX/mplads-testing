# Deployment Guide

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended) or similar
- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL (recommended) or SQLite
- Nginx (for reverse proxy)
- Domain name with SSL certificate

---

## Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3-pip python3-venv nodejs npm nginx postgresql

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/yourusername/mplads-ai-platform.git
cd mplads-ai-platform

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
npm run build
```

### 3. PostgreSQL Database Setup

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE mplads_db;
CREATE USER mplads_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mplads_db TO mplads_user;
\q

# Seed database
cd backend
source venv/bin/activate
python ../scripts/seed_db.py
```

### 4. Environment Configuration

```bash
# Create production .env
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://mplads_user:secure_password@localhost:5432/mplads_db
HOST=0.0.0.0
PORT=8000
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3
DEBUG=false
LOG_LEVEL=INFO
EOF
```

### 5. Systemd Service Setup

#### Backend Service

```bash
sudo nano /etc/systemd/system/mplads-backend.service
```

```ini
[Unit]
Description=MPLADS AI Platform Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/ubuntu/mplads-ai-platform/backend
Environment="PATH=/home/ubuntu/mplads-ai-platform/backend/venv/bin"
ExecStart=/home/ubuntu/mplads-ai-platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Frontend Service (if not using static files)

```bash
sudo nano /etc/systemd/system/mplads-frontend.service
```

```ini
[Unit]
Description=MPLADS AI Platform Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/ubuntu/mplads-ai-platform/frontend
ExecStart=/usr/bin/npm run preview -- --port 5173 --host
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mplads-backend
sudo systemctl start mplads-backend
sudo systemctl status mplads-backend
```

### 6. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/mplads
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend (Static Files)
    location / {
        root /home/ubuntu/mplads-ai-platform/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/mplads /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com
```

---

## Docker Deployment (Alternative)

### Create Dockerfile for Backend

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/mplads
    depends_on:
      - db

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=mplads
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  frontend:
    image: node:18
    working_dir: /app
    volumes:
      - ./frontend:/app
    command: npm run preview -- --port 5173 --host
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Run with Docker:

```bash
docker-compose up -d
```

---

## Health Checks

```bash
# Backend health
curl http://localhost:8000/api/dashboard/kpis

# Frontend
curl http://localhost:5173

# Database
psql -U mplads_user -d mplads_db -c "SELECT COUNT(*) FROM projects;"
```

---

## Monitoring

### Setup PM2 (Alternative to systemd)

```bash
npm install -g pm2

# Backend
cd backend
pm2 start "venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000" --name mplads-backend

# Save PM2 config
pm2 save
pm2 startup
```

### Logs

```bash
# Systemd logs
sudo journalctl -u mplads-backend -f

# PM2 logs
pm2 logs mplads-backend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Backup Strategy

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/backups/mplads"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -U mplads_user mplads_db > "$BACKUP_DIR/backup_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

---

## Security Checklist

- [ ] Use strong database passwords
- [ ] Enable firewall (ufw)
- [ ] Keep system updated
- [ ] Use SSL/TLS certificates
- [ ] Restrict database access
- [ ] Enable fail2ban
- [ ] Regular backups
- [ ] Monitor logs
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted domains

---

## Troubleshooting

### Backend won't start
- Check logs: `sudo journalctl -u mplads-backend`
- Verify database connection
- Check port availability: `sudo netstat -tlnp | grep 8000`

### Frontend 404 errors
- Rebuild frontend: `cd frontend && npm run build`
- Check Nginx config: `sudo nginx -t`
- Verify file permissions

### Database connection errors
- Check PostgreSQL status: `sudo systemctl status postgresql`
- Verify credentials in .env
- Test connection: `psql -U mplads_user -d mplads_db`

---

**Need help?** Open an issue or contact support.
