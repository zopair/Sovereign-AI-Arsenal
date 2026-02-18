# Security Hardening Guide

This guide provides comprehensive security measures for deploying the Sovereign AI Arsenal platform in production environments.

## 🔐 Security Overview

### Security Layers
1. **Network Security**: Firewall, SSL/TLS, DDoS protection
2. **Application Security**: Authentication, authorization, input validation
3. **Data Security**: Encryption, access control, backup security
4. **Infrastructure Security**: OS hardening, container security, monitoring

### Threat Model
- **External Threats**: Unauthorized access, data breaches, DDoS attacks
- **Internal Threats**: Insider threats, privilege escalation
- **System Threats**: Vulnerabilities, misconfigurations, zero-days

## 🛡️ Network Security

### 1. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw enable

# Advanced rules
sudo ufw deny 2375:2376/tcp  # Block RDP
sudo ufw deny 3389/tcp      # Block RDP
sudo ufw deny 5432/tcp      # Block PostgreSQL from outside
```

### 2. SSL/TLS Configuration

```nginx
# SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
```

### 3. DDoS Protection

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=5r/s burst=10 nodelay;
limit_req_zone $binary_remote_addr zone=search:10m rate=3r/s burst=5 nodelay;

# Connection limiting
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10;
limit_conn conn_limit_per_ip 10;
```

### 4. Intrusion Detection

```bash
# Install and configure Fail2Ban
sudo apt install fail2ban

# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd
usedns = warn

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 600
```

## 🔐 Application Security

### 1. Authentication & Authorization

```python
# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Policy
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SYMBOLS = True
```

### 2. API Key Security

```python
# API Key Generation
def generate_api_key():
    return secrets.token_urlsafe(32)

# API Key Validation
def validate_api_key(api_key: str, user_id: str):
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    # Validate against database
    return key_hash == stored_key_hash
```

### 3. Input Validation

```python
# Pydantic models for validation
from pydantic import BaseModel, validator

class RepositoryCreate(BaseModel):
    name: str
    description: str
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid name format')
        return v
```

### 4. Rate Limiting

```python
# Advanced rate limiting
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def check_rate_limit(self, identifier: str, limit: int, window: int):
        key = f"rate_limit:{identifier}"
        now = time.time()
        
        # Use Redis sorted set for sliding window
        self.redis.zremrangebyscore(key, 0, now - window)
        current = self.redis.zcard(key)
        
        if current >= limit:
            return False
        
        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, window * 2)
        return True
```

## 🔒 Data Security

### 1. Encryption at Rest

```yaml
# PostgreSQL Encryption
postgresql.conf:
  password_encryption: scram-sha-256
  ssl: on
  ssl_cert_file: '/etc/ssl/certs/server.crt'
  ssl_key_file: '/etc/ssl/private/server.key'
```

### 2. Encryption in Transit

```python
# Fernet encryption for sensitive data
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes):
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
```

### 3. Database Security

```sql
-- Row Level Security
CREATE POLICY user_data_policy ON users
    FOR ALL TO authenticated_users
    USING (user_id = current_user_id());

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Secure passwords
ALTER SYSTEM SET password_encryption = 'scram-sha-256';
```

### 4. API Key Storage

```python
# Secure API key storage
class APIKeyManager:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def store_api_key(self, raw_key: str) -> str:
        encrypted = self.cipher.encrypt(raw_key.encode())
        # Store encrypted key in database
        return encrypted.decode()
    
    def retrieve_api_key(self, encrypted_key: str) -> str:
        decrypted = self.cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()
```

## 🖥️ Infrastructure Security

### 1. Container Security

```dockerfile
# Security-focused Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy files with proper permissions
COPY --chown=appuser:appuser . .
USER appuser

# Remove unnecessary packages
RUN apt-get purge -y python3-pip
RUN apt-get autoremove -y
RUN rm -rf /var/lib/apt/lists/*
```

### 2. Docker Security

```yaml
# Docker Compose security
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - NET_BIND_SERVICE
    user: "1001:1001"
```

### 3. System Hardening

```bash
# System hardening script
#!/bin/bash

# Disable unnecessary services
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon

# Secure SSH
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitEmptyPasswords yes/PermitEmptyPasswords no/' /etc/ssh/sshd_config

# Set file permissions
chmod 600 /etc/ssh/sshd_config
chmod 600 /etc/ssh/sshd_config

# Configure sysctl
cat >> /etc/sysctl.conf << EOF
# Network Security
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.syncookies = 1

# Kernel Security
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
net.ipv4.conf.tcp_syncookies = 1
EOF

sysctl -p
```

### 4. Log Security

```python
# Secure logging configuration
import logging
from logging.handlers import RotatingFileHandler
import json

class SecureLogging:
    def __init__(self):
        self.logger = logging.getLogger('secure_logger')
        
        # Remove sensitive data from logs
        self.addFilter(SensitiveDataFilter())
        
        # Use secure file handler
        handler = RotatingFileHandler(
            '/var/log/sovereign-ai-arsenal/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.addFilter(SensitiveDataFilter())
        
        self.logger.addHandler(handler)

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Remove sensitive data from log records
        record.msg = self._sanitize_message(record.msg)
        return record
    
    def _sanitize_message(self, message):
        # Remove passwords, tokens, etc.
        import re
        # Remove patterns that look like passwords or tokens
        sanitized = re.sub(r'(?i)(password|token|key|secret)[\'"]?\s*[:=]\s*[^\s]+', '***', message)
        return sanitized
```

## 📊 Security Monitoring

### 1. Security Metrics

```yaml
# Prometheus security metrics
- name: security_metrics
  rules:
    - alert: SuspiciousLoginAttempts
      expr: rate(login_attempts_total{status="failed"}[5m]) > 0.1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High rate of failed login attempts"
    
    - alert: UnauthorizedAPIAccess
      expr: rate(api_requests_total{status="401"}[5m]) > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High rate of unauthorized API access"
```

### 2. Security Auditing

```python
# Security audit logging
class SecurityAuditor:
    def __init__(self, db_session):
        self.db = db_session
    
    def audit_user_permissions(self):
        """Audit user permissions"""
        users = self.db.query(User).all()
        for user in users:
            permissions = self.get_user_permissions(user.id)
            if self.check_excessive_permissions(permissions):
                self.log_security_event("excessive_permissions", user.id, permissions)
    
    def audit_api_keys(self):
        """Audit API keys"""
        api_keys = self.db.query(APIKey).all()
        for key in api_keys:
            if self.check_key_anomalies(key):
                self.log_security_event("api_key_anomaly", key.id, key.__dict__)
```

### 3. Intrusion Detection

```python
# Simple intrusion detection
class IntrusionDetection:
    def __init__(self):
        self.suspicious_patterns = [
            r'.*union.*select.*',
            r'.*drop.*table.*',
            r'.*insert.*into.*values.*',
            r'.*update.*set.*where.*',
            r'.*delete.*from.*where.*'
        ]
    
    def detect_sql_injection(self, query: str) -> bool:
        for pattern in self.suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
```

## 🔧 Security Best Practices

### 1. Development Security

```python
# Secure development practices
class SecureDevelopment:
    @staticmethod
    def validate_input(input_data: str, max_length: int = 1000) -> str:
        """Validate and sanitize input"""
        if len(input_data) > max_length:
            raise ValueError("Input too long")
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_data)
        return sanitized
    
    @staticmethod
    def escape_sql(query: str) -> str:
        """Escape SQL queries"""
        # Use parameterized queries instead
        return query
```

### 2. Code Review Checklist

- [ ] Input validation implemented
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Authentication properly implemented
- [ ] Authorization checks in place
- [ ] Error handling doesn't leak information
- [ ] Logging doesn't contain sensitive data
- [ ] Dependencies are up-to-date

### 3. Security Testing

```python
# Security testing utilities
class SecurityTesting:
    def test_authentication(self):
        """Test authentication mechanisms"""
        # Test weak passwords
        weak_passwords = ["123456", "password", "admin"]
        for password in weak_passwords:
            response = self.client.post("/auth/login", json={
                "email": "test@example.com",
                "password": password
            })
            assert response.status_code == 401
    
    def test_authorization(self):
        """Test authorization controls"""
        # Test unauthorized access
        response = self.client.get("/admin/users", headers=self.user_headers)
        assert response.status_code == 403
        
        # Test with admin privileges
        response = self.client.get("/admin/users", headers=self.admin_headers)
        assert response.status_code == 200
```

## 🚨 Incident Response

### 1. Incident Response Plan

```yaml
# Incident Response Phases
phases:
  - name: Preparation
    description: "Establish policies, procedures, and tools"
    duration: "Ongoing"
  
  - name: Detection
    description: "Monitor for security events"
    duration: "Immediate"
  
  - name: Analysis
    description: "Investigate and assess impact"
    duration: "1-2 hours"
  
  - name: Containment
    description: "Limit damage and prevent spread"
    duration: "1-4 hours"
  
  - name: Eradication
    description: "Remove threats and restore systems"
    duration: "4-24 hours"
  
  - name: Recovery
    description: "Restore normal operations"
    duration: "24-72 hours"
  
  - name: Lessons Learned
    description: "Document and improve"
    duration: "1-2 weeks"
```

### 2. Security Incident Response

```python
class SecurityIncidentResponse:
    def __init__(self):
        self.severity_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
    
    def handle_security_incident(self, incident: dict):
        severity = self.assess_severity(incident)
        
        if severity >= self.severity_levels['high']:
            self.activate_incident_response(incident)
        
        self.log_incident(incident)
        self.notify_stakeholders(incident, severity)
    
    def activate_incident_response(self, incident: dict):
        """Activate incident response procedures"""
        # Containment
        self.contain_incident(incident)
        
        # Investigation
        self.investigate_incident(incident)
        
        # Eradication
        self.eradicate_threat(incident)
        
        # Recovery
        self.recover_systems(incident)
```

### 3. Forensics

```python
class SecurityForensics:
    def __init__(self):
        self.evidence = []
    
    def collect_evidence(self, incident: dict):
        """Collect and preserve evidence"""
        evidence = {
            'timestamp': datetime.utcnow(),
            'incident_type': incident['type'],
            'severity': incident['severity'],
            'affected_systems': incident['affected_systems'],
            'logs': self.collect_relevant_logs(incident),
            'network_data': self.collect_network_data(incident)
        }
        self.evidence.append(evidence)
    
    def generate_forensic_report(self, incident_id: str) -> dict:
        """Generate forensic report"""
        return {
            'incident_id': incident_id,
            'evidence': self.evidence,
            'timeline': self.create_timeline(),
            'findings': self.analyze_evidence(),
            'recommendations': self.generate_recommendations()
        }
```

## 📋 Security Checklist

### Pre-Deployment
- [ ] Security audit completed
- [ ] Penetration testing performed
- [ ] Code review completed
- [ ] Dependencies scanned for vulnerabilities
- [ ] SSL certificates configured
- [ ] Firewall rules implemented
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested
- [ ] Incident response plan ready

### Ongoing
- [ ] Daily security scans
- [ ] Weekly vulnerability assessments
- [ ] Monthly security reviews
- [ ] Quarterly penetration testing
- [ ] Annual security audit
- [ ] Compliance checks
- [ ] Security training for team
- [ ] Incident response drills

### Emergency
- [ ] Security incident response team identified
- - [ ] Communication channels established
- [ ] Backup and recovery procedures tested
    - [ ] Contact information documented
    - [ ] Escalation procedures defined
    - [ ] Media statements prepared

---

**Note**: Security is an ongoing process. Regular reviews, updates, and improvements are essential for maintaining a strong security posture. For security issues, contact security@sovereign-ai-arsenal.com.