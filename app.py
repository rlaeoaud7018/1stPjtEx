import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, render_template, session, redirect, url_for, request
from blueprints.auth.routes import auth_bp
from blueprints.dashboard.routes import dashboard_bp
from blueprints.admin.routes import admin_bp
from ai.camera_manager import init_camera

app = Flask(__name__)
app.secret_key = "fire-control-project-secret-key"

# ── 청사진 등록 ──────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)

# ── 전역 인증 미들웨어 ──────────────────────
# 로그인 / 회원가입 관련 경로 및 정적 파일은 허용
PUBLIC_PREFIXES = ("/member/signin", "/member/signup", "/static/")

@app.before_request
def require_login():
    """모든 요청에 대해 로그인 여부를 검사한다.
    - 공개 경로(로그인/회원가입/정적파일)는 허용
    - 그 외 미로그인 → 로그인 페이지로 리다이렉트
    - 로그인됐으나 미승인 → 안내 페이지
    """
    path = request.path

    # 공개 경로 허용
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return None

    # 루트('/')는 로그인 여부에 따라 분기 — 허용
    if path == "/":
        return None

    member_id = session.get("signinedMemberId")
    if not member_id:
        return redirect(url_for("auth.signin_form"))

    # 승인 상태 확인
    from utils.json_manager import load_members
    members = load_members()
    member = members.get(member_id, {})
    if not member.get("approved", False):
        session.clear()
        return render_template("member/pending.html"), 403


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    init_camera()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
