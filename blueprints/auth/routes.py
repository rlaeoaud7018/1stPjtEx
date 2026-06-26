from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from utils.json_manager import load_members, save_members

auth_bp = Blueprint("auth", __name__, url_prefix="/member")


@auth_bp.route("/signin_form")
def signin_form():
    if session.get("signinedMemberId"):
        return redirect("/")
    return render_template("member/signin_form.html")


@auth_bp.route("/signin", methods=["POST"])
def signin():
    """AJAX 로그인 처리 — JSON 응답"""
    m_id = request.form.get("mId", "").strip()
    m_pw = request.form.get("mPw", "").strip()

    members = load_members()
    member  = members.get(m_id)

    if not member or member.get("pw") != m_pw:
        return jsonify({"success": False, "message": "id_pw_mismatch"})

    session["signinedMemberId"]   = m_id
    session["signinedMemberName"] = member.get("name", m_id)
    session["signinedMemberRole"] = member.get("role", "user")

    if not member.get("approved", False):
        return jsonify({"success": True, "redirect": "/?pending=1"})

    if member.get("role") == "admin":
        return jsonify({"success": True, "redirect": url_for("admin.members")})

    return jsonify({"success": True, "redirect": "/"})


@auth_bp.route("/signup_form")
def signup_form():
    return render_template("member/signup_form.html")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    m_id    = request.form.get("mId",    "").strip()
    m_pw    = request.form.get("mPw",    "").strip()
    m_pw2   = request.form.get("mPw2",   "").strip()
    m_name  = request.form.get("mName",  "").strip()
    m_email = request.form.get("mEmail", "").strip()
    m_phone = request.form.get("mPhone", "").strip()

    members = load_members()

    if m_id in members:
        return render_template("member/signup_form.html", error="이미 사용 중인 ID입니다.")
    if m_pw != m_pw2:
        return render_template("member/signup_form.html", error="비밀번호가 일치하지 않습니다.")
    if not all([m_id, m_pw, m_name, m_email, m_phone]):
        return render_template("member/signup_form.html", error="모든 항목을 입력해 주세요.")

    members[m_id] = {
        "pw":       m_pw,
        "name":     m_name,
        "email":    m_email,
        "phone":    m_phone,
        "role":     "user",
        "approved": False,
    }
    save_members(members)
    return render_template("member/signup_form.html", success=True)


@auth_bp.route("/check_id", methods=["POST"])
def check_id():
    """ID 중복 체크 AJAX"""
    m_id    = request.form.get("mId", "").strip()
    members = load_members()
    return jsonify({"available": m_id not in members and bool(m_id)})


@auth_bp.route("/modify_form")
def modify_form():
    member_id = session.get("signinedMemberId")
    if not member_id:
        return redirect(url_for("auth.signin_form"))
    members = load_members()
    member  = members.get(member_id, {})
    return render_template("member/modify_form.html", member=member, member_id=member_id)


@auth_bp.route("/modify", methods=["POST"])
def modify():
    member_id = session.get("signinedMemberId")
    if not member_id:
        return redirect(url_for("auth.signin_form"))

    m_pw    = request.form.get("mPw",    "").strip()
    m_email = request.form.get("mEmail", "").strip()
    m_phone = request.form.get("mPhone", "").strip()

    members = load_members()
    member  = members.get(member_id, {})

    if m_pw:
        member["pw"] = m_pw
    if m_email:
        member["email"] = m_email
    if m_phone:
        member["phone"] = m_phone

    members[member_id] = member
    save_members(members)
    return jsonify({"success": True, "message": "정보가 변경되었습니다."})


@auth_bp.route("/signout")
def signout():
    session.clear()
    return redirect("/")
