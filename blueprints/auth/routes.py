from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from utils.json_manager import load_members, save_members
from email.message import EmailMessage
from datetime import datetime
import random
import smtplib


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

@auth_bp.route('/id_find_form')
def id_find_form():
    session.pop('is_email_verified', None)
    session.pop('verified_email', None)
    session.pop('otp', None)
    session.pop('otp_email', None)
    session.pop('otp_time', None)
    
    return render_template('member/id_find_form.html')


@auth_bp.route('/pw_find_form')
def pw_find_form():
    session.pop('is_email_verified', None)
    session.pop('verified_email', None)
    session.pop('otp', None)
    session.pop('otp_email', None)
    session.pop('otp_time', None)
    
    return render_template('member/pw_find_form.html')


@auth_bp.route('/send_verification', methods=['POST'])
def send_verification():
    email_to = request.form.get('mMail')

    if not email_to:
        return jsonify({"status": "error", "message": "이메일 주소가 없습니다."})

    session.pop('otp', None)
    session.pop('otp_email', None)
    session.pop('otp_time', None)
    session.pop('is_email_verified', None)
    session.pop('verified_email', None)

    otp = ''.join(str(random.randint(0, 9)) for _ in range(6))

    session['otp'] = otp
    session['otp_email'] = email_to
    session['otp_time'] = datetime.now().timestamp()

    otpMail = EmailMessage()
    otpMail['Subject'] = "이메일 인증 번호 안내"
    otpMail['To'] = email_to
    otpMail.set_content(f"당신의 인증번호는 [{otp}] 입니다.")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('igoeun126@gmail.com', 'wbyl yhub iatk frsr')
            server.send_message(otpMail)
        return jsonify({"status": "success", "message": "인증번호가 발송되었습니다."})
    except Exception as e:
        print("메일 발송 에러 :", e)
        return jsonify({"status": "error", "message": "메일 발송에 실패했습니다."})


@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    user_email = request.form.get('mMail')
    user_otp = request.form.get('otp')

    if not user_email or not user_otp:
        return jsonify({"status": "error", "message": "데이터가 누락되었습니다."})

    saved_otp = session.get('otp')
    saved_email = session.get('otp_email')
    saved_time = session.get('otp_time')

    if not saved_time or datetime.now().timestamp() - saved_time > 180:
        return jsonify({"status": "error", "message": "인증번호가 만료되었습니다."})

    if saved_otp and saved_email == user_email and str(saved_otp) == str(user_otp).strip():
        session['is_email_verified'] = True
        session['verified_email'] = user_email
        session.pop('otp', None)
        session.pop('otp_email', None)
        session.pop('otp_time', None)
        return jsonify({"status": "success", "message": "인증에 성공했습니다."})

    return jsonify({"status": "error", "message": "인증번호가 일치하지 않습니다."})


@auth_bp.route('/id_find_confirm', methods=['POST'])
def id_find_confirm():
    if not session.get('is_email_verified'):
        return "<script>alert('이메일 인증이 필요합니다.'); history.back();</script>"

    user_name = request.form.get('mName')
    user_email = request.form.get('mMail')

    if session.get('verified_email') != user_email:
        return "<script>alert('인증한 이메일과 입력한 이메일이 다릅니다.'); history.back();</script>"

    found_id = "test_user_id" 

    if found_id:
        return render_template('id_find_result.html', found_id=found_id)

    return "<script>alert('일치하는 회원 정보가 없습니다.'); history.back();</script>"


@auth_bp.route('/pw_find_confirm', methods=['POST'])
def pw_find_confirm():
    if not session.get('is_email_verified'):
        return "<script>alert('이메일 인증이 필요합니다.'); history.back();</script>"

    user_id = request.form.get('mId')
    user_name = request.form.get('mName')
    user_email = request.form.get('mMail')

    if session.get('verified_email') != user_email:
        return "<script>alert('인증한 이메일과 입력한 이메일이 다릅니다.'); history.back();</script>"

    user_exists = True

    if user_exists:
        return render_template('pw_reset_form.html', mId=user_id)

    return "<script>alert('일치하는 회원 정보가 없습니다.'); history.back();</script>"
