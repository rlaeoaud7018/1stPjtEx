from flask import Blueprint, render_template, request, redirect, session, url_for
from utils.json_manager import load_members, save_members

auth_bp = Blueprint("auth", __name__, url_prefix="/member")


@auth_bp.route("/signin_form")
def signin_form():
    return render_template("member/signin_form.html")


@auth_bp.route("/signin", methods=["POST"])
def signin():
    member_id = request.form.get("memberId", "").strip()
    member_pw = request.form.get("memberPw", "").strip()

    members = load_members()

    if member_id not in members or members[member_id]["pw"] != member_pw:
        return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.'); history.back();</script>"

    member = members[member_id]

    # 미승인 회원 차단
    if not member.get("approved", False):
        return render_template("member/pending.html"), 403

    session["signinedMemberId"]   = member_id
    session["signinedMemberName"] = member["name"]
    session["signinedMemberRole"] = member.get("role", "member")
    return redirect(url_for("dashboard.monitor"))


@auth_bp.route("/signup_form")
def signup_form():
    return render_template("member/signup_form.html")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    member_id   = request.form.get("memberId",   "").strip()
    member_pw   = request.form.get("memberPw",   "").strip()
    member_name = request.form.get("memberName", "").strip()
    member_phone = request.form.get("memberPhone", "").strip()
    member_email = request.form.get("memberEmail", "").strip()

    members = load_members()

    if member_id in members:
        return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

    members[member_id] = {
        "pw":       member_pw,
        "name":     member_name,
        "phone":    member_phone,
        "email":    member_email,
        "role":     "member",
        "approved": False          # 관리자 승인 대기
    }
    save_members(members)
    return render_template("member/pending.html", just_registered=True)


@auth_bp.route("/signout_confirm")
def signout_confirm():
    session.clear()
    return redirect(url_for("auth.signin_form"))


@auth_bp.route("/modify_form")
def modify_form():
    member_id = session.get("signinedMemberId")
    if not member_id:
        return redirect(url_for("auth.signin_form"))
    members = load_members()
    member_info = members.get(member_id, {})
    return render_template("member/modify_form.html", member_info=member_info)


@auth_bp.route("/modify", methods=["POST"])
def modify():
    member_id = session.get("signinedMemberId")
    if not member_id:
        return redirect(url_for("auth.signin_form"))

    member_pw    = request.form.get("memberPw",    "").strip()
    member_name  = request.form.get("memberName",  "").strip()
    member_phone = request.form.get("memberPhone", "").strip()
    member_email = request.form.get("memberEmail", "").strip()

    members = load_members()
    if member_id in members:
        members[member_id]["pw"]    = member_pw
        members[member_id]["name"]  = member_name
        members[member_id]["phone"] = member_phone
        members[member_id]["email"] = member_email
        save_members(members)
        session["signinedMemberName"] = member_name
        return "<script>alert('정보가 수정되었습니다.'); location.href='/dashboard/monitor';</script>"
    return "<script>alert('오류가 발생했습니다.'); history.back();</script>"


@auth_bp.route("/delete_confirm")
def delete_confirm():
    member_id = session.get("signinedMemberId")
    if not member_id:
        return redirect(url_for("auth.signin_form"))

    # 관리자 계정은 삭제 불가
    members = load_members()
    if members.get(member_id, {}).get("role") == "admin":
        return "<script>alert('관리자 계정은 삭제할 수 없습니다.'); history.back();</script>"

    if member_id in members:
        del members[member_id]
        save_members(members)
        session.clear()
        return "<script>alert('회원 탈퇴가 완료되었습니다.'); location.href='/member/signin_form';</script>"
    return "<script>alert('오류가 발생했습니다.'); history.back();</script>"
