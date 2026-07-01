from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from utils.json_manager import (
    load_members, save_members, load_notices, save_notices,
    get_next_notice_id, load_sms_logs, save_sms_log
)
from datetime import datetime
import json

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    if session.get("signinedMemberRole") != "admin":
        return redirect(url_for("auth.signin_form"))
    return None


@admin_bp.route("/management")
def management():
    """관리자 메뉴 — 사용자 관리 + 발송 이력 통합 페이지"""
    check = require_admin()
    if check:
        return check

    # 사용자 목록 — 구별 그룹핑
    all_members = load_members()
    district_order = ["동구", "중구", "서구", "유성구", "대덕구", "전체", "관제 센터"]
    by_district = {}
    for mid, info in all_members.items():
        d = info.get("district", "기타")
        by_district.setdefault(d, [])
        by_district[d].append({"id": mid, **info})

    # district_order 기준 정렬, 나머지는 '기타'로
    ordered_districts = []
    for d in district_order:
        if d in by_district:
            ordered_districts.append((d, by_district[d]))
    for d, members_list in by_district.items():
        if d not in district_order:
            ordered_districts.append((d, members_list))

    # 발송 이력
    sms_logs = load_sms_logs()
    sms_logs_sorted = sorted(sms_logs, key=lambda x: x.get("sent_at", ""), reverse=True)

    return render_template(
        "admin/management.html",
        ordered_districts=ordered_districts,
        sms_logs=sms_logs_sorted,
    )


@admin_bp.route("/api/confirm_sms/<int:log_id>", methods=["POST"])
def confirm_sms(log_id):
    """발송 이력 확인 토글 API"""
    check = require_admin()
    if check:
        return jsonify({"error": "unauthorized"}), 403

    # 🛠️ [수정]: 직접 open하지 않고 json_manager의 공통 함수 및 파일 경로 참조 활용
    logs = load_sms_logs()
    target_log = None

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for log in logs:
        if log.get("id") == log_id:
            if log.get("confirmed"):
                log["confirmed"] = False
                log["confirmed_at"] = None
            else:
                log["confirmed"] = True
                log["confirmed_at"] = now_str
            target_log = log
            break

    if not target_log:
        return jsonify({"error": "Log not found"}), 404

    # 데이터 통일성 유지 보관을 위해 전체 쓰기 작업 수행
    try:
        with open(SMS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        return jsonify({"error": f"Failed to save log: {e}"}), 500

    return jsonify({
        "success": True, 
        "confirmed": target_log.get("confirmed"), 
        "confirmed_at": target_log.get("confirmed_at")
    })


@admin_bp.route("/members")
def members():
    check = require_admin()
    if check:
        return check
    all_members = load_members()
    pending = [
        {"id": mid, **info}
        for mid, info in all_members.items()
        if not info.get("approved", False)
    ]
    approved = [
        {"id": mid, **info}
        for mid, info in all_members.items()
        if info.get("approved", False)
    ]
    return render_template("admin/members.html", pending=pending, approved=approved)


@admin_bp.route("/approve/<member_id>", methods=["POST"])
def approve(member_id):
    check = require_admin()
    if check:
        return check
    members = load_members()
    if member_id in members:
        members[member_id]["approved"] = True
        save_members(members)
    return redirect(url_for("admin.members"))


@admin_bp.route("/reject/<member_id>", methods=["POST"])
def reject(member_id):
    check = require_admin()
    if check:
        return check
    members = load_members()
    if member_id in members:
        del members[member_id]
        save_members(members)
    return redirect(url_for("admin.members"))


@admin_bp.route("/delete/<member_id>", methods=["POST"])
def delete_member(member_id):
    check = require_admin()
    if check:
        return check
    members = load_members()
    if member_id in members:
        del members[member_id]
        save_members(members)
    return redirect(url_for("admin.members"))


@admin_bp.route("/notice/write", methods=["GET", "POST"])
def write_notice():
    check = require_admin()
    if check:
        return check
    if request.method == "POST":
        title   = request.form.get("title",   "").strip()
        content = request.form.get("content", "").strip()
        pinned  = request.form.get("pinned") == "on"
        notices = load_notices()
        notice_id = get_next_notice_id()

        notices.append({
            "id":          notice_id,
            "title":       title,
            "content":     content,
            "author":      session.get("signinedMemberId"),
            "author_name": session.get("signinedMemberName", "관리자"),
            "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pinned":      pinned,
        })
        save_notices(notices)
        return redirect(url_for("notice.list_notices"))
    return render_template("notice/write.html")


@admin_bp.route("/notice/delete/<int:notice_id>", methods=["POST"])
def delete_notice(notice_id):
    check = require_admin()
    if check:
        return check
    notices = load_notices()
    notices = [n for n in notices if n["id"] != notice_id]
    save_notices(notices)
    return redirect(url_for("notice.list_notices"))
