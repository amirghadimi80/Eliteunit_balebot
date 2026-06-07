"""
Flask web dashboard for EliteUniteTime admin panel.
Provides a real-time view of users, reports, and penalties.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_file
from functools import wraps
from datetime import datetime, date, timedelta

from database.db import Database
from services.reports import ReportService
from services.penalty import PenaltyService
from utils.date_utils import (
    gregorian_to_jalali_str,
    get_today_gregorian,
    get_week_start_end,
    get_month_start_end,
    format_date_persian,
)
from config.settings import BALE_ADMIN_IDS

app = Flask(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET_KEY", "elite-unite-time-secret-2024")

db = Database()
report_service = ReportService(db)
penalty_service = PenaltyService(db)


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin1234")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "رمز عبور اشتباه است"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────
# Main dashboard
# ─────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    today = get_today_gregorian()
    today_str = today.strftime("%Y-%m-%d")
    today_jalali = gregorian_to_jalali_str(today)

    all_users = db.get_all_users()
    today_reports = db.get_reports_by_date(today_str)
    reported_ids = {r.user_id for r in today_reports}

    week_start, week_end = get_week_start_end()
    month_start, month_end = get_month_start_end()

    # Weekly totals
    week_reports = []
    for u in all_users:
        week_reports += db.get_reports_by_user_and_date(
            u.id, week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")
        )

    # Monthly totals
    month_reports = []
    for u in all_users:
        month_reports += db.get_reports_by_user_and_date(
            u.id, month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")
        )

    stats = {
        "total_users": len(all_users),
        "reported_today": len(today_reports),
        "missing_today": len(all_users) - len(today_reports),
        "total_hours_today": sum(r.total_hours for r in today_reports),
        "total_hours_week": sum(r.total_hours for r in week_reports),
        "total_hours_month": sum(r.total_hours for r in month_reports),
        "today_jalali": today_jalali,
    }

    # Today's report rows
    today_rows = []
    for r in today_reports:
        user = db.get_user_by_id(r.user_id)
        if user:
            today_rows.append({
                "name": user.full_name,
                "main": r.main_hours,
                "side": r.side_hours,
                "total": r.total_hours,
                "time": r.created_at,
            })

    # Missing users
    missing_users = [u.full_name for u in all_users if u.id not in reported_ids]

    return render_template(
        "index.html",
        stats=stats,
        today_rows=today_rows,
        missing_users=missing_users,
        today_jalali=today_jalali,
    )


# ─────────────────────────────────────────────
# Users page
# ─────────────────────────────────────────────

@app.route("/users")
@login_required
def users():
    all_users = db.get_all_users()
    user_data = []
    for u in all_users:
        penalties = db.get_penalties_by_user(u.id, status="unpaid")
        total_reports = len(db.get_reports_by_user_and_date(
            u.id, "2000-01-01", get_today_gregorian().strftime("%Y-%m-%d")
        ))
        user_data.append({
            "id": u.id,
            "name": u.full_name,
            "phone": u.phone or "—",
            "bio": u.bio or "—",
            "interests": u.interests or "—",
            "total_reports": total_reports,
            "unpaid_penalties": len(penalties),
            "joined": u.created_at,
        })
    return render_template("users.html", users=user_data)


@app.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if db.delete_user(user_id):
        return jsonify({"success": True})
    return jsonify({"success": False}), 400


# ─────────────────────────────────────────────
# Reports page
# ─────────────────────────────────────────────

@app.route("/reports")
@login_required
def reports():
    # Filters
    filter_date = request.args.get("date", "")
    filter_user = request.args.get("user", "")

    all_users = db.get_all_users()
    user_map = {u.id: u.full_name for u in all_users}

    today = get_today_gregorian()
    start_default = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_default = today.strftime("%Y-%m-%d")

    start_date = request.args.get("start", start_default)
    end_date = request.args.get("end", end_default)

    rows = []
    for u in all_users:
        if filter_user and str(u.id) != filter_user:
            continue
        reps = db.get_reports_by_user_and_date(u.id, start_date, end_date)
        for r in reps:
            rows.append({
                "id": r.id,
                "user_name": u.full_name,
                "date_shamsi": r.date_shamsi,
                "date_gregorian": r.date_gregorian,
                "main": r.main_hours,
                "side": r.side_hours,
                "total": r.total_hours,
                "created_at": r.created_at,
            })

    # Sort by date desc
    rows.sort(key=lambda x: x["date_gregorian"], reverse=True)

    return render_template(
        "reports.html",
        rows=rows,
        users=all_users,
        start_date=start_date,
        end_date=end_date,
        filter_user=filter_user,
    )


@app.route("/reports/delete/<int:report_id>", methods=["POST"])
@login_required
def delete_report(report_id):
    if db.delete_report(report_id):
        return jsonify({"success": True})
    return jsonify({"success": False}), 400


@app.route("/reports/add", methods=["POST"])
@login_required
def add_report():
    user_id = int(request.form.get("user_id"))
    date_shamsi = request.form.get("date_shamsi")
    main_hours = float(request.form.get("main_hours"))
    side_hours = float(request.form.get("side_hours"))
    
    # Convert Jalali to Gregorian
    from utils.date_utils import jalali_to_gregorian
    parts = date_shamsi.split('/')
    g_date = jalali_to_gregorian(int(parts[0]), int(parts[1]), int(parts[2]))
    
    # Submit report
    success, message = report_service.submit_daily_report(
        user_id=user_id,
        main_hours=main_hours,
        side_hours=side_hours,
        report_date=g_date
    )
    
    if success:
        return redirect(url_for("reports"))
    else:
        return f"Error: {message}", 400


# ─────────────────────────────────────────────
# Penalties page
# ─────────────────────────────────────────────

@app.route("/penalties")
@login_required
def penalties():
    all_users = db.get_all_users()
    rows = []
    for u in all_users:
        pens = db.get_penalties_by_user(u.id)
        for p in pens:
            rows.append({
                "user_name": u.full_name,
                "date_shamsi": p.date_shamsi,
                "reason": p.reason,
                "amount": p.amount,
                "status": p.status,
                "id": p.id,
            })
    rows.sort(key=lambda x: x["date_shamsi"], reverse=True)
    return render_template("penalties.html", rows=rows)


@app.route("/penalties/delete/<int:penalty_id>", methods=["POST"])
@login_required
def delete_penalty(penalty_id):
    if db.delete_penalty(penalty_id):
        return redirect(url_for("penalties"))
    return "Error", 400


# ─────────────────────────────────────────────
# API endpoints (for live refresh)
# ─────────────────────────────────────────────

@app.route("/api/stats")
@login_required
def api_stats():
    today = get_today_gregorian()
    today_str = today.strftime("%Y-%m-%d")
    all_users = db.get_all_users()
    today_reports = db.get_reports_by_date(today_str)
    return jsonify({
        "total_users": len(all_users),
        "reported_today": len(today_reports),
        "missing_today": len(all_users) - len(today_reports),
        "total_hours_today": sum(r.total_hours for r in today_reports),
    })


@app.route("/api/today_reports")
@login_required
def api_today_reports():
    today = get_today_gregorian()
    today_str = today.strftime("%Y-%m-%d")
    today_reports = db.get_reports_by_date(today_str)
    rows = []
    for r in today_reports:
        user = db.get_user_by_id(r.user_id)
        if user:
            rows.append({
                "name": user.full_name,
                "main": r.main_hours,
                "side": r.side_hours,
                "total": r.total_hours,
            })
    return jsonify(rows)


# ─────────────────────────────────────────────
# Analytics & Charts
# ─────────────────────────────────────────────

@app.route("/analytics")
@login_required
def analytics():
    all_users = db.get_all_users()
    return render_template("analytics.html", users=all_users)


@app.route("/api/user_chart_data/<int:user_id>")
@login_required
def api_user_chart_data(user_id):
    from datetime import timedelta
    
    today = get_today_gregorian()
    
    # Get last 4 weeks of data
    all_reports = db.get_reports_by_user_and_date(
        user_id,
        (today - timedelta(days=28)).strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d")
    )
    
    # Group by week
    weeks_data = {}
    for r in all_reports:
        # Calculate week number (0-3 for last 4 weeks)
        report_date = datetime.strptime(r.date_gregorian, "%Y-%m-%d").date()
        days_ago = (today - report_date).days
        week_num = 3 - (days_ago // 7)  # 0 = oldest week, 3 = current week
        
        if week_num not in weeks_data:
            weeks_data[week_num] = {"main": 0, "side": 0, "total": 0}
        
        weeks_data[week_num]["main"] += r.main_hours
        weeks_data[week_num]["side"] += r.side_hours
        weeks_data[week_num]["total"] += r.total_hours
    
    # Prepare data for chart (week 1 to week 4)
    reports_data = []
    total_main = 0
    total_side = 0
    weeks_reported = 0
    
    for week in range(4):
        if week in weeks_data:
            data = weeks_data[week]
            reports_data.append({
                "week": week + 1,
                "date_shamsi": f"هفته {week + 1}",
                "main": round(data["main"], 1),
                "side": round(data["side"], 1),
                "total": round(data["total"], 1),
            })
            total_main += data["main"]
            total_side += data["side"]
            if data["total"] > 0:
                weeks_reported += 1
        else:
            reports_data.append({
                "week": week + 1,
                "date_shamsi": f"هفته {week + 1}",
                "main": 0,
                "side": 0,
                "total": 0,
            })
    
    # Get user info
    user = db.get_user_by_id(user_id)
    user_name = user.full_name if user else ""
    
    # Calculate stats
    avg_weekly = (total_main + total_side) / 4
    
    return jsonify({
        "user_name": user_name,
        "reports": reports_data,
        "stats": {
            "total_main": round(total_main, 1),
            "total_side": round(total_side, 1),
            "avg_weekly": round(avg_weekly, 2),
            "weeks_reported": weeks_reported,
        }
    })


@app.route("/api/all_users_chart")
@login_required
def api_all_users_chart():
    from datetime import timedelta
    
    all_users = db.get_all_users()
    today = get_today_gregorian()
    
    user_data = []
    for user in all_users:
        # Get last 4 weeks
        all_reports = db.get_reports_by_user_and_date(
            user.id,
            (today - timedelta(days=28)).strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )
        
        total_main = sum(r.main_hours for r in all_reports)
        total_side = sum(r.side_hours for r in all_reports)
        
        user_data.append({
            "name": user.full_name,
            "main": round(total_main, 1),
            "side": round(total_side, 1),
            "total": round(total_main + total_side, 1),
        })
    
    return jsonify(user_data)


# ─────────────────────────────────────────────
# Excel Export
# ─────────────────────────────────────────────

@app.route("/export/excel")
@login_required
def export_excel():
    export_type = request.args.get("type", "weekly")  # weekly or monthly
    
    import pandas as pd
    from io import BytesIO
    
    if export_type == "weekly":
        stats_list = report_service.get_all_weekly_stats()
        filename = f"گزارش-هفتگی-{gregorian_to_jalali_str(get_today_gregorian())}.xlsx"
    else:
        stats_list = report_service.get_all_monthly_stats()
        filename = f"گزارش-ماهانه-{gregorian_to_jalali_str(get_today_gregorian())}.xlsx"
    
    # Prepare data
    data = []
    for stats, user_name in stats_list:
        data.append({
            "نام": user_name,
            "ساعت اصلی": stats.main_hours,
            "ساعت فرعی": stats.side_hours,
            "مجموع ساعات": stats.total_hours,
            "تعداد روزهای گزارش": stats.days_reported,
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Export to Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='گزارش')
        
        # Get workbook and worksheet for formatting
        workbook = writer.book
        worksheet = writer.sheets['گزارش']
        
        # Adjust column widths
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 15
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 15
        worksheet.column_dimensions['E'].width = 20
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", 5000))
    debug = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
