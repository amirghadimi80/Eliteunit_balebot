#!/bin/bash
# این اسکریپت از GitHub Codespace Secrets فایل .env میسازه
# Secrets رو در: github.com → Settings → Codespaces → Secrets تعریف کن

cat > .env << EOF
BALE_API_TOKEN=${BALE_API_TOKEN}
BALE_GROUP_ID=${BALE_GROUP_ID}
BALE_ADMIN_IDS=${BALE_ADMIN_IDS}
DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD:-admin1234}
DASHBOARD_SECRET_KEY=${DASHBOARD_SECRET_KEY:-change-me}
DASHBOARD_PORT=5000
DASHBOARD_DEBUG=false
LOG_LEVEL=INFO
EOF

echo "✅ .env created from Codespace Secrets"
