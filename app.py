import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, render_template, session, redirect, url_for, request
from blueprints.auth.routes import auth_bp
from blueprints.dashboard.routes import dashboard_bp
from blueprints.admin.routes import admin_bp
from blueprints.notice.routes import notice_bp
from ai.camera_manager import init_camera
from utils.json_manager import load_members, load_fire_logs, load_notices

app = Flask(__name__)
app.secret_key = "fire-control-project-2024"

# ── Blueprint 등록 ──────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(notice_bp)

# ── 인증 미들웨어 ────────────────────────────────────────
PUBLIC_PREFIXES = ("/member/", "/static/", "/notice")

@app.before_request
def check_auth():
    path = request.path

    # 공개 경로 허용
    if path == "/":
        return None
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return None

    member_id = session.get("signinedMemberId")

    # 관리자 전용 경로
    if path.startswith("/admin/"):
        if not member_id or session.get("signinedMemberRole") != "admin":
            return redirect(url_for("auth.signin_form"))
        return None

    # 대시보드 경로 — 로그인 + 승인 필요
    if path.startswith("/dashboard/"):
        if not member_id:
            return redirect(url_for("auth.signin_form"))
        members = load_members()
        member = members.get(member_id, {})
        if not member.get("approved", False):
            # 미승인 — 홈으로 리다이렉트 (홈에서 팝업 처리)
            return redirect("/?pending=1")
        return None

    return None


# ── 홈페이지 ────────────────────────────────────────────
@app.route("/")
def home():
    member_id   = session.get("signinedMemberId")
    member_name = session.get("signinedMemberName")
    approved    = False
    show_pending = request.args.get("pending") == "1"
    show_signup_success = request.args.get("signup_success") == "1"

    if member_id:
        members = load_members()
        member  = members.get(member_id, {})
        approved = member.get("approved", False)
        member_name = member.get("name", member_id)
        if not approved:
            show_pending = True

    # 통계 데이터
    logs        = load_fire_logs()
    total_count = len(logs)
    fire_count  = sum(1 for l in logs if l.get("type") == "화재")
    smoke_count = sum(1 for l in logs if l.get("type") == "연기")

    # 공지 마커
    notices = sorted(load_notices(), key=lambda x: x["id"], reverse=True)[:3]

    return render_template(
        "index.html",
        member_id=member_id,
        member_name=member_name,
        approved=approved,
        show_pending=show_pending,
        show_signup_success=show_signup_success,
        total_count=total_count,
        fire_count=fire_count,
        smoke_count=smoke_count,
        notices=notices,
    )

if __name__ == "__main__":
    # 캠 연결 실패 시 에러를 터트리지 않고 넘어가도록 예외 처리
    try:
        print("ESP32-CAM 연결 시도 중...")
        init_camera()
    except Exception as e:
        print(f"\n[경고] ESP32-CAM 연결에 실패했습니다. (에러: {e})")
        print("캠 연결 없이 웹 서버(Flask)를 실행합니다.\n")
        

    # 카메라 연결 성공/실패 여부와 상관없이 Flask 서버 정상 구동
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)