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
from services.notifications import notify_penalty_created, notify_penalty_paid
from utils.date_utils import (
    gregorian_to_jalali_str,
    get_today_gregorian,
    get_week_start_end,
    get_month_start_end,
    format_date_persian,
)
from utils.time_utils import parse_time_input, format_duration
from config.settings import (
    BALE_ADMIN_IDS,
    PAYMENT_APPROVER_NAME,
    PAYMENT_APPROVER_PIN,
    PAYMENT_CARD_HOLDER,
    PAYMENT_CARD_NUMBER,
)

app = Flask(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET_KEY", "elite-unite-time-secret-2024")

db = Database()
report_service = ReportService(db)
penalty_service = PenaltyService(db)


@app.template_filter("dur")
def duration_filter(hours):
    return format_duration(hours)


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

    unpaid_penalties = penalty_service.get_recent_unpaid_penalties(limit=10)
    all_unpaid = [p for p in db.get_all_penalties() if p.status == "unpaid"]
    total_unpaid_toman = sum(p.amount for p in all_unpaid)

    return render_template(
        "index.html",
        stats=stats,
        today_rows=today_rows,
        missing_users=missing_users,
        today_jalali=today_jalali,
        unpaid_penalties=unpaid_penalties,
        total_unpaid_toman=total_unpaid_toman,
        payment_card=PAYMENT_CARD_NUMBER,
        payment_holder=PAYMENT_CARD_HOLDER,
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
            "bot_linked": not db.is_placeholder_bale_id(u.bale_id),
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
    try:
        main_hours = parse_time_input(request.form.get("main_hours", ""), max_hours=12)
        side_hours = parse_time_input(request.form.get("side_hours", ""), max_hours=8)
    except ValueError:
        return "Error: فرمت ساعت نامعتبر است (مثال: 2:30)", 400
    
    # Convert Jalali to Gregorian
    from utils.date_utils import jalali_to_gregorian
    parts = date_shamsi.split('/')
    g_date = jalali_to_gregorian(int(parts[0]), int(parts[1]), int(parts[2]))
    
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
    all_penalties = db.get_all_penalties()
    rows = []
    for p in all_penalties:
        user = db.get_user_by_id(p.user_id)
        if user:
            rows.append({
                "id": p.id,
                "user_name": user.full_name,
                "date_shamsi": p.date_shamsi,
                "amount": p.amount,
                "reason": p.reason,
                "status": p.status,
                "created_at": p.created_at,
            })
    rows.sort(key=lambda x: x["date_shamsi"], reverse=True)
    return render_template(
        "penalties.html",
        rows=rows,
        penalties_enabled=penalty_service.is_penalties_enabled(),
        approver_name=PAYMENT_APPROVER_NAME,
        payment_card=PAYMENT_CARD_NUMBER,
        payment_holder=PAYMENT_CARD_HOLDER,
        is_approver=session.get("payment_approver", False),
        flash_msg=request.args.get("msg"),
        flash_type=request.args.get("type", "ok"),
    )


@app.route("/penalties/toggle", methods=["POST"])
@login_required
def toggle_penalties():
    currently_enabled = penalty_service.is_penalties_enabled()
    new_state = not currently_enabled
    if penalty_service.set_penalties_enabled(new_state):
        if new_state:
            msg = "جریمه‌ها از این لحظه فعال شد — جریمه جدید اعمال می‌شود"
        else:
            msg = "جریمه‌ها از این لحظه غیرفعال شد — جریمه جدیدی اعمال نمی‌شود"
        return redirect(url_for("penalties", msg=msg, type="ok"))
    return redirect(url_for("penalties", msg="خطا در تغییر وضعیت جریمه‌ها", type="error"))


@app.route("/penalties/approver", methods=["POST"])
@login_required
def penalties_approver_login():
    pin = request.form.get("approver_pin", "").strip()
    if pin == PAYMENT_APPROVER_PIN:
        session["payment_approver"] = True
        return redirect(url_for("penalties", msg="دسترسی تأیید پرداخت فعال شد", type="ok"))
    return redirect(url_for("penalties", msg="رمز تأیید‌کننده اشتباه است", type="error"))


@app.route("/penalties/pay/<int:penalty_id>", methods=["POST"])
@login_required
def pay_penalty(penalty_id):
    if not session.get("payment_approver"):
        return redirect(url_for("penalties", msg="ابتدا با رمز تأیید‌کننده وارد شوید", type="error"))

    penalty = db.get_penalty_by_id(penalty_id)
    if not penalty:
        return redirect(url_for("penalties", msg="جریمه یافت نشد", type="error"))
    if penalty.status == "paid":
        return redirect(url_for("penalties", msg="این جریمه قبلاً پرداخت شده", type="error"))

    user = db.get_user_by_id(penalty.user_id)
    if not user:
        return redirect(url_for("penalties", msg="کاربر یافت نشد", type="error"))

    if db.mark_penalty_paid(penalty_id):
        notify_penalty_paid(user.full_name, user.bale_id, penalty.amount)
        return redirect(
            url_for(
                "penalties",
                msg=f"پرداخت جریمه {user.full_name} ({penalty.amount:,} تومان) تأیید شد",
                type="ok",
            )
        )
    return redirect(url_for("penalties", msg="خطا در تأیید پرداخت", type="error"))


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
    view_type = request.args.get("view_type", "daily")  # daily or weekly
    
    # Get ALL data (no time limit)
    all_reports = db.get_reports_by_user_and_date(
        user_id,
        "2000-01-01",  # Start from very old date to get all data
        today.strftime("%Y-%m-%d")
    )
    
    # Group data based on view type
    if view_type == "weekly":
        # Group by week
        weeks_data = {}
        for r in all_reports:
            report_date = datetime.strptime(r.date_gregorian, "%Y-%m-%d").date()
            # Calculate week number (weeks since start of data)
            # Find the earliest date
            if not weeks_data:
                earliest_date = report_date
            
            days_since_start = (report_date - earliest_date).days if 'earliest_date' in locals() else 0
            week_num = days_since_start // 7
            
            if week_num not in weeks_data:
                weeks_data[week_num] = {"main": 0, "side": 0, "total": 0, "date": r.date_shamsi}
            
            weeks_data[week_num]["main"] += r.main_hours
            weeks_data[week_num]["side"] += r.side_hours
            weeks_data[week_num]["total"] += r.total_hours
        
        # Convert to list
        reports_data = []
        for week_num in sorted(weeks_data.keys()):
            data = weeks_data[week_num]
            reports_data.append({
                "date_shamsi": f"هفته {week_num + 1}",
                "main": round(data["main"], 1),
                "side": round(data["side"], 1),
                "total": round(data["total"], 1),
            })
    else:
        # Daily view - individual reports
        reports_data = []
        for r in all_reports:
            reports_data.append({
                "date_shamsi": r.date_shamsi,
                "main": round(r.main_hours, 1),
                "side": round(r.side_hours, 1),
                "total": round(r.total_hours, 1),
            })
        
        # Sort by date
        reports_data.sort(key=lambda x: x["date_shamsi"])
    
    # Calculate totals
    total_main = sum(r["main"] for r in reports_data)
    total_side = sum(r["side"] for r in reports_data)
    
    # Get user info
    user = db.get_user_by_id(user_id)
    user_name = user.full_name if user else ""
    
    # Calculate stats
    if view_type == "weekly":
        weeks_reported = len(reports_data)
        avg_weekly = (total_main + total_side) / weeks_reported if weeks_reported > 0 else 0
    else:
        days_reported = len(reports_data)
        avg_daily = (total_main + total_side) / days_reported if days_reported > 0 else 0
        avg_weekly = avg_daily * 7
        weeks_reported = days_reported // 7
    
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
    all_users = db.get_all_users()
    today = get_today_gregorian()
    
    data = []
    for u in all_users:
        # Get ALL data for each user
        all_reports = db.get_reports_by_user_and_date(
            u.id,
            "2000-01-01",
            today.strftime("%Y-%m-%d")
        )
        
        total_main = sum(r.main_hours for r in all_reports)
        total_side = sum(r.side_hours for r in all_reports)
        
        data.append({
            "name": u.full_name,
            "main": round(total_main, 1),
            "side": round(total_side, 1),
            "total": round(total_main + total_side, 1),
        })
    
    return jsonify(data)


# ─────────────────────────────────────────────
# Excel Export
# ─────────────────────────────────────────────

@app.route("/export/excel")
@login_required
def export_excel():
    import pandas as pd
    from io import BytesIO
    
    all_users = db.get_all_users()
    today = get_today_gregorian()
    
    rows = []
    for u in all_users:
        reps = db.get_reports_by_user_and_date(
            u.id, "2000-01-01", today.strftime("%Y-%m-%d")
        )
        for r in reps:
            rows.append({
                "Name": u.full_name,
                "Date (Shamsi)": r.date_shamsi,
                "Date (Gregorian)": r.date_gregorian,
                "Main Hours": r.main_hours,
                "Side Hours": r.side_hours,
                "Total Hours": r.total_hours,
            })
    
    df = pd.DataFrame(rows)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"elite_unite_time_export_{today.strftime('%Y%m%d')}.xlsx"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
