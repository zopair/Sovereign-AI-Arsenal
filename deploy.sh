#!/bin/bash

# Sovereign AI Arsenal - Production Deployment Script
# This script automates the deployment of the complete SaaS platform

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root (for production deployment)
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root for production deployment"
    fi
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get >/dev/null 2>&1; then
            DISTRO="debian"
        elif command -v yum >/dev/null 2>&1; then
            DISTRO="redhat"
        elif command -v dnf >/dev/null 2>&1; then
            DISTRO="fedora"
        else
            error "Unsupported Linux distribution"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    else
        error "Unsupported operating system: $OSTYPE"
    fi
    
    log "Detected OS: $OS, Distribution: $DISTRO"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    case $DISTRO in
        debian|ubuntu)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update
            apt-get install -y \
                curl \
                wget \
                git \
                build-essential \
                software-properties-common \
                apt-transport-https \
                ca-certificates \
                gnupg \
                lsb-release \
                htop \
                unzip \
                jq \
                docker.io \
                docker-compose-plugin
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null 2>&1; then
                dnf update -y
                dnf install -y \
                    curl \
                    wget \
                    git \
                    gcc \
                    make \
                    openssl-devel \
                    jq \
                    htop \
                    unzip \
                    docker \
                    docker-compose
            else
                yum update -y
                yum install -y \
                    epel-release \
                    curl \
                    wget \
                    git \
                    gcc \
                    make \
                    openssl-devel \
                    jq \
                    htop \
                    unzip
            fi
            ;;
        macos)
            # Check if Homebrew is installed
            if ! command -v brew >/dev/null 2>&1; then
                error "Homebrew is required. Please install it first: https://brew.sh/"
            fi
            brew update
            brew install \
                docker \
                docker-compose \
                jq \
                htop
            ;;
    esac
    
    log "System dependencies installed successfully"
}

# Install Docker and Docker Compose
install_docker() {
    log "Installing Docker and Docker Compose..."
    
    if command -v docker >/dev/null 2>&1; then
        log "Docker is already installed: $(docker --version)"
    else
        case $DISTRO in
            debian|ubuntu)
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
                add-apt-repository \
                    "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
                apt-get update
                apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                ;;
            centos|rhel|fedora)
                if command -v dnf >/dev/null 2>&1; then
                    dnf install -y dnf-plugins-core
                    dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
                    dnf install -y docker-ce docker-ce-cli containerd.io
                else
                    yum install -y yum-utils
                    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                    yum install -y docker-ce docker-ce-cli containerd.io
                fi
                ;;
        esac
    fi
    
    # Start and enable Docker
    systemctl start docker || true
    systemctl enable docker || true
    
    log "Docker and Docker Compose installed successfully"
}

# Setup firewall rules
setup_firewall() {
    log "Setting up firewall rules..."
    
    if command -v ufw >/dev/null 2>&1; then
        ufw --force reset
        ufw default deny incoming
        ufw allow ssh
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 3000/tcp
        ufw allow 8000/tcp
        ufw allow 9090/tcp
        ufw allow 3000/tcp
        ufw enable
        log "UFW firewall configured"
    elif command -v firewall-cmd >/dev/null 2>&1; then
        systemctl start firewalld || true
        systemctl enable firewalld || true
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --permanent --add-port=9090/tcp
        firewall-cmd --reload
        log "firewalld configured"
    else
        warning "No firewall management tool found (ufw/firewalld)"
    fi
}

# Create application directories
create_directories() {
    log "Creating application directories..."
    
    DIRS=(
        "/opt/sovereign-ai-arsenal"
        "/opt/sovereign-ai-arsenal/config"
        "/opt/sovereign-ai-arsenal/data"
        "/opt/sovereign-ai-arsenal/logs"
        "/opt/sovereign-ai-arsenal/backups"
        "/opt/sovereign-ai-arsenal/ssl"
        "/var/log/sovereign-ai-arsenal"
        "/etc/sovereign-ai-arsenal"
    )
    
    for dir in "${DIRS[@]}"; do
        mkdir -p "$dir"
        chmod 755 "$dir"
    done
    
    # Set proper ownership
    chown -R root:root /opt/sovereign-ai-arsenal
    
    log "Application directories created"
}

# Generate SSL certificates
generate_ssl_certs() {
    log "Generating SSL certificates..."
    
    SSL_DIR="/opt/sovereign-ai-arsenal/ssl"
    
    # Create private key
    openssl genrsa -out "$SSL_DIR/sovereign-ai.key" 2048
    
    # Create certificate signing request
    openssl req -new -key "$SSL_DIR/sovereign-ai.key" -out "$SSL_DIR/sovereign-ai.csr" -subj "/C=US/ST=State/L=City/O=Sovereign AI Arsenal/CN=sovereign-ai-arsenal.com" -nodes
    
    # Generate self-signed certificate (in production, use Let's Encrypt or CA-signed cert)
    openssl x509 -req -days 365 -in "$SSL_DIR/sovereign-ai.csr" -signkey "$SSL_DIR/sovereign-ai.key" -out "$SSL_DIR/sovereign-ai.crt"
    
    # Create fullchain file
    cat "$SSL_DIR/sovereign-ai.crt" > "$SSL_DIR/fullchain.pem"
    
    # Set proper permissions
    chmod 600 "$SSL_DIR/sovereign-ai.key"
    chmod 644 "$SSL_DIR/sovereign-ai.crt" "$SSL_DIR/fullchain.pem"
    
    log "SSL certificates generated"
}

# Create environment file
create_env_file() {
    log "Creating environment file..."
    
    ENV_FILE="/opt/sovereign-ai-arsenal/.env"
    
    # Generate random secrets
    JWT_SECRET=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    DB_PASSWORD=$(openssl rand -base64 16)
    REDIS_PASSWORD=$(openssl rand -base64 16)
    GRAFANA_PASSWORD=$(openssl rand -base64 16)
    
    cat > "$ENV_FILE" << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/sovereign_ai arsenal
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sovereign_ai arsenal
DB_USER=postgres
DB_PASSWORD=${DB_PASSWORD}

# Redis Configuration
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# Security Configuration
JWT_SECRET=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
SECURITY_REQUIRE_HTTPS=false
CORS_ORIGINS=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here

# Monitoring
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# Application Configuration
LOG_LEVEL=INFO
MAX_WORKERS=4
DEBUG=false
EOF
    
    chmod 600 "$ENV_FILE"
    log "Environment file created at $ENV_FILE"
    
    warning "Please update the following values in $ENV_FILE:"
    warning "- OPENAI_API_KEY: Set your OpenAI API key"
    warning "- GITHUB_TOKEN: Set your GitHub token"
    warning "- CORS_ORIGINS: Set your actual domain"
    warning "- SECURITY_REQUIRE_HTTPS: Set to true in production"
}

# Deploy the application
deploy_application() {
    log "Deploying Sovereign AI Arsenal..."
    
    cd /opt/sovereign-ai-arsenal
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    sleep 30
    
    # Check service health
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log "Application deployed successfully!"
        
        # Show service status
        docker-compose -f docker-compose.prod.yml ps
        
        log "Services available at:"
        log "  - Frontend: http://localhost:3000"
        log "  - Backend API: http://localhost:8000"
        log "  - Grafana: http://localhost:3000 (admin/${GRAFANA_PASSWORD})"
        log "  - Prometheus: http://localhost:9090"
        
        # Show first-time admin credentials
        log "First-time admin credentials:"
        log "  - Grafana: admin/${GRAFANA_PASSWORD}"
        log "  - Environment file: /opt/sovereign-ai-arsenal/.env"
        
    else
        error "Application deployment failed. Check logs:"
        docker-compose -f docker-compose.prod.yml logs --tail=50
    fi
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/sovereign-ai-arsenal << EOF
/var/log/sovereign-ai-arsenal/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644
    postrotate
        docker-compose -f /opt/sovereign-ai-arsenal/docker-compose.prod.yml restart
    endscript
}
EOF
    
    log "Log rotation configured"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create systemd service files
    cat > /etc/systemd/system/sovereign-ai-arsenal.service << EOF
[Unit]
Description=Sovereign AI Arsenal
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/sovereign-ai-arsenal
ExecStart=/usr/bin/docker-compose -f /opt/sovereign-ai-arsenal/docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f /opt/sovereign-ai-arsenal/docker-compose.prod.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable sovereign-ai-arsenal
    
    log "Systemd service created"
}

# Setup backup script
setup_backup() {
    log "Setting up backup system..."
    
    cat > /opt/sovereign-ai-arsenal/backup.sh << 'EOF'
#!/bin/bash

# Backup script for Sovereign AI Arsenal
BACKUP_DIR="/opt/sovereign-ai-arsenal/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="sovereign_ai_backup_\${DATE}.tar.gz"

# Create backup directory
mkdir -p "\$BACKUP_DIR"

# Backup database
docker-compose -f /opt/sovereign-ai-arsenal/docker-compose.prod.yml exec -T postgres pg_dump -U postgres sovereign_ai arsenal > "\$BACKUP_DIR/database_\${DATE}.sql"

# Backup data directories
tar -czf "\$BACKUP_DIR/\$BACKUP_FILE" \
    /opt/sovereign-ai-arsenal/data \
    /opt/sovereign-ai-arsenal/config \
    /opt/sovereign-ai-arsenal/.env

# Keep only last 30 days of backups
find "\$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "\$BACKUP_DIR" -name "*.sql" -mtime +30 -delete

echo "Backup completed: \$BACKUP_FILE"
EOF
    
    chmod +x /opt/sovereign-ai-arsenal/backup.sh
    
    # Add to crontab for daily backups at 2 AM
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/sovereign-ai-arsenal/backup.sh") | crontab -
    
    log "Backup system configured"
}

# Main deployment function
main() {
    log "Starting Sovereign AI Arsenal production deployment..."
    
    check_root
    detect_os
    install_system_deps
    install_docker
    setup_firewall
    create_directories
    generate_ssl_certs
    create_env_file
    deploy_application
    setup_log_rotation
    setup_monitoring
    setup_backup
    
    log "🎉 Sovereign AI Arsenal deployed successfully!"
    log ""
    log "Next steps:"
    log "1. Update environment variables: /opt/sovereign-ai-arsenal/.env"
    log "2. Configure your domain in nginx/nginx.prod.conf"
    log "3. Update SSL certificates (use Let'sEncrypt in production)"
    log "4. Set up monitoring alerts in Grafana"
    log "5. Configure backup retention policies"
    log ""
    log "Service management:"
    log "  - Start:   sudo systemctl start sovereign-ai-arsenal"
    log "  - Stop:    sudo systemctl stop sovereign-ai-arsenal"
    log "  - Restart: sudo systemctl restart sovereign-ai-arsenal"
    log "  - Status:  docker-compose -f /opt/sovereign-ai-arsenal/docker-compose.prod.yml ps"
    log "  - Logs:   docker-compose -f /opt/sovereign-ai-arsenal/docker-compose.prod.yml logs -f"
    log ""
    log "Access the application:"
    log "  - Frontend: http://your-domain.com"
    log "  - Backend API: http://your-domain.com/api"
    log "  - Grafana: http://your-domain.com:3000 (admin/$(grep GRAFANA_PASSWORD /opt/sovereign-ai-arsenal/.env | cut -d'=' -f2))"
    log ""
    log "For support and documentation: https://github.com/your-org/sovereign-ai-arsenal"
}

# Run main function
main "$@"