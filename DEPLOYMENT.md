# Sovereign AI Arsenal - Production Deployment Guide

## 🚀 Production Deployment Architecture

This guide provides comprehensive instructions for deploying the Sovereign AI Arsenal SaaS platform in production environments.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Security Configuration](#security-configuration)
4. [Deployment Steps](#deployment-steps)
5. Monitoring & Alerting](#monitoring--alerting)
6. [Scaling Architecture](#scaling-architecture)
7. [Backup & Recovery](#backup--recovery)
8. [Maintenance](#maintenance)

## 🖥️ System Requirements

### Minimum Requirements
- **CPU**: 4 cores (8+ recommended)
- **RAM**: 8GB (16GB+ recommended)
- **Storage**: 100GB SSD (500GB+ recommended)
- **Network**: 1Gbps (for production traffic)
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

### Recommended Production Setup
- **CPU**: 8-16 cores
- **RAM**: 32-64GB
- **Storage**: 1TB NVMe SSD
- **Load Balancer**: HAProxy / AWS ALB / Nginx Plus
- **Database**: PostgreSQL 15 with replication
- **Cache**: Redis Cluster (3+ nodes)
- **Monitoring**: Prometheus + Grafana + AlertManager

### VPS Providers
- **AWS**: EC2 (t3.xlarge or larger)
- **DigitalOcean**: Droplets (8GB+)
- **Vultr**: High Frequency Droplets
- **Linode**: Dedicated CPU instances
- **Hetzner**: AX/AX servers

## 🏗️ Infrastructure Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git build-essential software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release htop unzip jq

# Create application user
sudo useradd -m -s /bin/bash sovereign
sudo usermod -aG sudo,docker sovereign
```

### 2. Docker Installation

```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker sovereign
```

### 3. Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/sovereign-ai-arsenal
sudo chown sovereign:sovereign /opt/sovereign-ai-arsenal
cd /opt/sovereign-ai-arsenal

# Clone repository
git clone https://github.com/your-org/sovereign-ai-arsenal.git .
```

## 🔒 Security Configuration

### 1. Firewall Setup

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw enable

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. SSL/TLS Configuration

```bash
# Generate SSL certificates (Let's Encrypt recommended)
sudo apt install certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -m admin@yourdomain.com --agree-tos --non-interactive
```

### 3. Security Headers

Add to `nginx/nginx.prod.conf`:
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'";
```

## 🚀 Deployment Steps

### 1. Automated Deployment

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
sudo ./deploy.sh
```

### 2. Manual Deployment

```bash
# Create environment variables
cat > .env << EOF
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/sovereign_ai arsenal
REDIS_URL=redis://:your_redis_password@localhost:6379/0
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token
EOF

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 3. SSL Certificate Setup

```bash
# For production, use Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com
```

### 4. Nginx Configuration

```nginx
# /etc/nginx/sites-available/sovereign-ai-arsenal
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv13;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy to frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Proxy to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=5r/s;
        limit_req zone=api burst=10 nodelay;
    }
    
    # Grafana
    location /grafana/ {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        auth_basic "Grafana";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

## 📊 Monitoring & Alerting

### 1. Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'sovereign-ai-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### 2. Alerting Rules

```yaml
# monitoring/rules/alerts.yml
groups:
  - name: sovereign-ai-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      - alert: DatabaseConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database has {{ $value }} connections"
```

### 3. Grafana Dashboards

1. Import pre-configured dashboards from `monitoring/grafana/dashboards/`
2. Set up alert notifications (Email, Slack, PagerDuty)
3. Configure data sources (Prometheus, PostgreSQL, Redis)

## 📈 Scaling Architecture

### 1. Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  backend:
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/sovereign_ai arsenal
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.scale.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
```

### 2. Database Scaling

```sql
-- PostgreSQL configuration optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

### 3. Load Balancer Configuration

```nginx
# nginx/nginx.scale.conf
upstream backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}

server {
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 💾 Backup & Recovery

### 1. Automated Backup Script

```bash
#!/bin/bash
# /opt/sovereign-ai-arsenal/backup.sh

BACKUP_DIR="/opt/sovereign-ai-arsenal/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Database backup
docker-compose exec -T postgres pg_dump -U postgres sovereign_ai arsenal > "$BACKUP_DIR/db_$DATE.sql"

# File backup
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" \
    /opt/sovereign-ai-arsenal/data \
    /opt/sovereign-ai-arsenal/config \
    /opt/sovereign-ai-arsenal/.env

# Clean old backups
find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

### 2. Recovery Procedures

```bash
# Database recovery
docker-compose exec -T postgres psql -U postgres -d sovereign_ai arsenal < backup.sql

# File recovery
tar -xzf backup_file.tar.gz -C /

# Service restart
docker-compose restart
```

### 3. Disaster Recovery Plan

1. **Immediate Response**
   - Identify issue scope
   - Notify stakeholders
   - Begin recovery procedures

2. **Service Restoration**
   - Restore from most recent backup
   - Verify data integrity
   - Restart services

3. **Post-Incident**
   - Conduct root cause analysis
   - Update procedures
   - Document lessons learned

## 🔧 Maintenance

### 1. Regular Tasks

```bash
# Daily
- Check service status
- Review logs for errors
- Verify backup completion

# Weekly
- Update security patches
- Review resource usage
- Clean old logs

# Monthly
- Update application
- Review SSL certificates
- Test backup restoration

# Quarterly
- Security audit
- Performance review
- Capacity planning
```

### 2. Performance Monitoring

```bash
# Check resource usage
docker stats

# Monitor logs
docker-compose logs -f --tail=100

# Check database performance
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### 3. Update Procedures

```bash
# Application update
git pull origin main
docker-compose build
docker-compose up -d

# System update
sudo apt update && sudo apt upgrade -y
docker system prune -f
```

## 🌐 Multi-Region Deployment

### 1. Architecture Overview

```
Internet
    │
┌─────────────────┐
│   CDN/CloudFlare │
└─────────────────┘
    │
┌─────────────────┐
│   Load Balancer │
└─────────────────┘
    │
┌─────────────────┐
┌─────────────────┐
│   Region 1      │   │
│ ┌─────┬─────┐   │
│ │ LB  │  App│   │
│ └─────┴─────┘   │
└─────────────────┘
    │
┌─────────────────┐
│   Region 2      │
│ ┌─────┬─────┐   │
│ │ LB  │  App│   │
│ └─────┴─────┘   │
└─────────────────┘
    │
┌─────────────────┐
│   Global DB     │
│ (PostgreSQL)    │
└─────────────────┘
```

### 2. Database Replication

```sql
-- Master configuration
postgresql.conf:
  wal_level = replica
  max_wal_senders = 3
  wal_keep_segments = 64
  archive_mode = on
  archive_command = 'cp %p /var/lib/postgresql/archive/%f'
  restore_command = 'cp /var/lib/postgresql/archive/%f %p'
```

### 3. DNS Configuration

```yaml
# Route 53 example
sovereign-ai-arsenal.com:
  type: A
  alias_target:
    name: global-loadbalancer
    zone_id: Z1
```

## 🛡️ Security Hardening

### 1. Network Security

```bash
# Fail2Ban configuration
sudo apt install fail2ban
sudo systemctl enable fail2ban

# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

### 2. Application Security

```yaml
# Security headers in nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### 3. Database Security

```sql
-- PostgreSQL security
-- Create read-only user for monitoring
CREATE USER monitoring WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE sovereign_ai arsenal TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;

-- Remove unnecessary permissions
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
```

## 📋 Production Checklist

### Pre-Deployment
- [ ] Security audit completed
- [ ] SSL certificates configured
- [ ] Firewall rules set
- [ ] Monitoring configured
- [ ] Backup system tested
- [ ] Load testing completed
- [ ] Documentation updated

### Post-Deployment
- [ ] All services healthy
- [ ] Monitoring alerts configured
- [ ] Backup verification
- [ ] Performance benchmarks met
- [ ] Security headers verified
- [ ] Log rotation working
- [ ] SSL certificate valid

### Ongoing
- [ ] Daily health checks
- [ ] Weekly backup verification
- [ ] Monthly security updates
- [ ] Quarterly performance reviews
- [ ] Annual penetration testing

## 🆘 Support & Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Restart services if needed
   docker-compose restart
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready -U postgres
   
   # Check logs
   docker-compose logs postgres
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate
   openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
   ```

### Support Channels
- **Email**: support@sovereign-ai-arsenal.com
- **Documentation**: https://docs.sovereign-ai-arsenal.com
- **GitHub Issues**: https://github.com/your-org/sovereign-ai-arsenal/issues
- **Status Page**: https://status.sovereign-ai-arsenal.com

---

**Note**: This guide is for production deployment. Always test in a staging environment first. For additional support, contact our team.