# EliteUniteTime - Deployment & Getting Started Guide

## Quick Start (5 minutes)

### 1. Create Virtual Environment
```bash
# On Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Configuration
```bash
# Copy example config
cp .env.example .env

# Edit with your values
# Windows: notepad .env
# Linux/Mac: nano .env
```

Required values:
- `BALE_API_TOKEN`: Get from @BaleBot on Bale
- `BALE_GROUP_ID`: Your group chat ID
- `BALE_ADMIN_IDS`: Admin user IDs (comma-separated)

### 4. Run the Bot
```bash
python app.py
```

You should see:
```
==================================================
EliteUniteTime Bot Starting...
==================================================
2024-04-27 10:30:15,123 - root - INFO - Database initialized
2024-04-27 10:30:15,234 - root - INFO - Scheduler service initialized
...
```

## Getting Bale API Token

1. Add @BaleBot to your contact (Bale app)
2. Send message: `newbot`
3. Follow the instructions
4. You'll receive a token like: `123456:ABCDEFGHijklmnopqrstuvwxyz`
5. Copy this to your `.env` file

## Finding Group Chat ID

1. In Bale, find your group
2. Create a test message
3. Run this Python snippet:
```python
from balethon import Client
client = Client(token="YOUR_TOKEN")
# When message comes, log message.chat_id
```

Or add the bot to group and check logs for group IDs.

## File Structure Explanation

```
EliteUniteTime/
├── app.py                 ← Run this: python app.py
├── bot.py                 ← Bot logic and handlers
├── requirements.txt       ← Dependencies
├── .env                   ← Your configuration (create from .env.example)
├── README.md             ← Full documentation
│
├── config/
│   └── settings.py       ← App settings and constants
│
├── database/
│   └── db.py             ← Database operations
│       └── Manages: users, reports, penalties
│
├── models/
│   └── models.py         ← Data classes
│       └── User, Report, Penalty, Stats
│
├── services/
│   ├── reports.py        ← Report generation (daily/weekly/monthly)
│   ├── penalty.py        ← Penalty management
│   └── scheduler.py      ← Scheduled tasks (10 AM check)
│
├── handlers/
│   ├── start.py          ← /start command and registration
│   ├── tasks.py          ← Daily report submission
│   ├── profile.py        ← User profiles and social
│   └── admin.py          ← Admin panel features
│
├── utils/
│   ├── date_utils.py     ← Timezone & Jalali calendar
│   └── formatter.py      ← Message formatting
│
└── data/
    └── database.db       ← SQLite database (auto-created)
```

## System Flow

### User Registration Flow
```
User sends /start
    ↓
Bot asks for name
    ↓
User enters name
    ↓
Bot asks for phone (share contact)
    ↓
User shares phone
    ↓
User registered ✅
    ↓
Main menu shown
```

### Daily Report Flow
```
User clicks "📊 ثبت گزارش روزانه"
    ↓
Bot shows today's Jalali date
    ↓
User enters main hours (0-12)
    ↓
User enters side hours (0-8)
    ↓
Report saved to database
    ↓
Notification sent to group
    ↓
User sees confirmation ✅
```

### Penalty Check (Automatic, Daily at 10 AM)
```
Scheduler triggers at 10:00 AM
    ↓
Check yesterday's reports
    ↓
Find users without reports
    ↓
Create penalty records
    ↓
Send notifications to users
    ↓
Admins notified ✅
```

## Database Schema

The system automatically creates 3 tables:

### users
Stores user registration data
```
Columns: id, bale_id, full_name, phone, bio, interests, created_at, updated_at
Example: (1, 123456, "Amir Hossein", "+989123456789", "...", "...", ...)
```

### reports
Stores daily work hour submissions
```
Columns: id, user_id, date_shamsi, date_gregorian, main_hours, side_hours, total_hours, created_at, updated_at
Example: (1, 1, "1405/02/07", "2024-04-27", 6.0, 2.0, 8.0, ...)
```

### penalties
Stores penalty records for missed reports
```
Columns: id, user_id, date_shamsi, date_gregorian, amount, reason, status, created_at
Example: (1, 2, "1405/02/06", "2024-04-26", 1, "عدم ثبت گزارش", "unpaid", ...)
```

## Configuration Options

### config/settings.py

Change these for your needs:

```python
# Time to check for missing reports (10 AM Iran time)
MISSING_REPORT_CHECK_HOUR = 10
MISSING_REPORT_CHECK_MINUTE = 0

# Maximum hours allowed
MAX_MAIN_HOURS = 12
MAX_SIDE_HOURS = 8
MAX_TOTAL_HOURS = 20

# Penalty amount per missed day
PENALTY_AMOUNT = 1
```

## Monitoring & Logs

### View Logs
```bash
# Real-time on console when running bot
python app.py

# Also saved to file:
cat logs/app.log

# Windows PowerShell:
Get-Content logs/app.log -Wait
```

### Check Database
```bash
# Install sqlite3 if needed
sqlite3 data/database.db

# View tables
.tables

# View users
SELECT * FROM users;

# View today's reports
SELECT * FROM reports WHERE date_gregorian = '2024-04-27';

# View unpaid penalties
SELECT * FROM penalties WHERE status = 'unpaid';

# Exit
.exit
```

## Admin Commands

Send `/admin` to access admin panel if you're in BALE_ADMIN_IDS.

Features:
- ✅ View all users
- ✅ Weekly team report
- ✅ Export Excel file
- ✅ Manage penalties
- ✅ Manual penalty check

## Troubleshooting

### "Error: BALE_API_TOKEN is not set"
**Problem**: Missing token in .env  
**Solution**: Add BALE_API_TOKEN to .env file

### "Bot doesn't respond to messages"
**Problem**: Bot not receiving updates  
**Solution**: 
1. Check API token is correct
2. Add bot to group/chat
3. Check logs for errors: `python app.py`
4. Verify internet connection

### "Database is locked"
**Problem**: Multiple processes accessing database  
**Solution**: Close all other instances of the bot

### "Messages appear in wrong language/encoding"
**Problem**: Character encoding  
**Solution**: Usually automatic, ensure Python 3.11+ and UTF-8 locale

### "Scheduler doesn't trigger at set time"
**Problem**: APScheduler timezone issue  
**Solution**: Verify TIMEZONE in settings.py is "Asia/Tehran"

## Performance Tips

### For Small Teams (< 50 users)
- SQLite is perfect
- No optimization needed
- All features work smoothly

### For Medium Teams (50-500 users)
- Monitor database file size
- Regular backups recommended
- Consider: `backup_database.py` script

### For Large Teams (> 500 users)
- Consider PostgreSQL upgrade
- Add caching layer (Redis)
- Use Celery for async tasks

## Backup & Recovery

### Backup Database
```bash
# Simple copy
cp data/database.db backups/database_$(date +%Y%m%d_%H%M%S).db

# Or use SQL dump
sqlite3 data/database.db .dump > backup.sql
```

### Restore Database
```bash
# Restore from backup
cp backups/database_backup.db data/database.db

# Or restore from SQL dump
sqlite3 data/database.db < backup.sql
```

## Running in Production

### Using systemd (Linux)
Create `/etc/systemd/system/eliteunitetime.service`:
```ini
[Unit]
Description=EliteUniteTime Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/eliteunitetime
ExecStart=/opt/eliteunitetime/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable eliteunitetime
sudo systemctl start eliteunitetime
sudo systemctl status eliteunitetime
```

### Using Docker
Create `Dockerfile`:
```dockerfile
FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t eliteunitetime .
docker run -e BALE_API_TOKEN=xxx eliteunitetime
```

### Using PM2 (Node.js, for management)
```bash
npm install -g pm2

# Create ecosystem.config.js
pm2 start app.py --name "eliteunitetime"
pm2 save
pm2 startup
```

## Testing

### Test Registration Flow
1. Send `/start` to bot
2. Enter name (e.g., "Test User")
3. Share contact
4. Check if user appears in database: `SELECT * FROM users WHERE full_name = "Test User";`

### Test Daily Report
1. Click "📊 ثبت گزارش روزانه"
2. Enter 6 for main hours
3. Enter 2 for side hours
4. Check database: `SELECT * FROM reports WHERE user_id = 1 ORDER BY created_at DESC LIMIT 1;`

### Test Scheduler
1. Open logs: `python app.py` (keep running)
2. Look for "Scheduler started" message
3. Next day at 10 AM, watch for penalty check messages

## Next Steps

1. **Customize Messages**: Edit `config/settings.py` to add your own messages
2. **Add More Features**: Follow the existing handler patterns
3. **Scale Database**: When needed, migrate to PostgreSQL
4. **Integrate Analytics**: Add Telegram/Bale Business API for group notifications
5. **Mobile App**: Create companion app for faster reporting

## Support Resources

- **Bale API Documentation**: https://bale.ai/developers
- **Balethon Documentation**: Check installed package docs
- **Python Documentation**: https://docs.python.org/3.11/
- **SQLite Documentation**: https://www.sqlite.org/docs.html

## Version Info

- **Python**: 3.11+
- **Balethon**: 3.1.1
- **APScheduler**: 3.10.4
- **pandas**: 2.2.0
- **Database**: SQLite 3.x

---

**Last Updated**: April 2026  
**Status**: Production Ready ✅  
**Support Level**: Full
