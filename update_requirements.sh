# Update requirements.txt to include new dependencies
echo "Updating requirements.txt with new dependencies..."

# Add new dependencies to requirements.txt
cat >> backend/requirements.txt << 'EOF'

# Phase 2 Dependencies - Docker Sandbox
docker>=6.1.0
aiofiles>=23.0.0

# Phase 2 Dependencies - Security
cryptography>=41.0.8

# Phase 2 Dependencies - Google Colab Compatibility
psutil>=5.9.0
jupyter>=1.0.0
ipywidgets>=8.0.0
google-colab>=1.0.0

# Additional utilities
tqdm>=4.66.0
rich>=13.7.0
EOF

echo "✅ requirements.txt updated"