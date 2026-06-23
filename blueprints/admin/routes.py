from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from utils.json_manager import load_members, save_members, load_sms_logs

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin():
    """관리자가 아닌 경우 None 이 아닌 redirect 객체를 반환"""
    if session.get("signinedMemberRole") != "admin":
        return redirect(url_for("dashboard.monitor"))
    return None


@admin_bp.route("/members")
def members():
    check = require_admin()
    if check:
        return check
    all_members = load_members()
    # admin 제외하고 리스트로 변환
    member_list = [
        {"id": mid, **info}
        for mid, info in all_members.items()
        if info.get("role") != "admin"
    ]
    # 미승인 먼저 정렬
    member_list.sort(key=lambda x: (x.get("approved", False), x["id"]))
    return render_template("admin/members.html", members=member_list)


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
    if member_id in members and members[member_id].get("role") != "admin":
        members[member_id]["approved"] = False
        save_members(members)
    return redirect(url_for("admin.members"))


@admin_bp.route("/delete/<member_id>", methods=["POST"])
def delete_member(member_id):
    check = require_admin()
    if check:
        return check
    members = load_members()
    if member_id in members and members[member_id].get("role") != "admin":
        del members[member_id]
        save_members(members)
    return redirect(url_for("admin.members"))


@admin_bp.route("/sms_logs")
def sms_logs():
    check = require_admin()
    if check:
        return check
    logs = list(reversed(load_sms_logs()))
    return render_template("admin/sms_logs.html", logs=logs)
