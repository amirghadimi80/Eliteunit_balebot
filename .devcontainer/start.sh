#!/bin/bash
# Auto-start script for GitHub Codespaces
# Runs bot + dashboard in background and keeps Codespace alive

echo "================================================"
echo "  EliteUniteTime — Starting..."
echo "================================================"

# اگه .env وجود نداره از .env.example کپی کن
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  .env file created from .env.example"
    echo "    Please set your BALE_API_TOKEN in the Secrets section"
fi

# اجرای بات + داشبورد در background
nohup python run_all.py > logs/app.log 2>&1 &
BOT_PID=$!
echo "✅ Bot + Dashboard started (PID: $BOT_PID)"
echo $BOT_PID > /tmp/eliteunitetime.pid

echo ""
echo "📊 Dashboard: check the PORTS tab → port 5000"
echo "📄 Logs: tail -f logs/app.log"
echo ""
