from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from utils.json_manager import load_members, save_members, load_notices, save_notices, get_next_notice_id

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    if session.get("signinedMemberRole") != "admin":
        return redirect(url_for("auth.signin_form"))
    return None


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
        from datetime import datetime
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
