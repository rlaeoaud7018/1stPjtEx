from flask import Blueprint, render_template, Response, jsonify, session, redirect, url_for
from ai.camera_manager import get_frame
from utils.json_manager import load_fire_logs, load_sms_logs
from datetime import datetime, timedelta
import cv2
import time

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def generate_frames():    
    while True:
        frame = get_frame()
        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
        except Exception as e:
            print("Frame encode error:", e)
        time.sleep(0.05)


@dashboard_bp.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@dashboard_bp.route("/monitor")
def monitor():
    return render_template("dashboard/monitor.html")


@dashboard_bp.route("/history")
def history():
    return render_template("dashboard/history.html")


@dashboard_bp.route("/send_history")
def send_history():
    """발송 이력 — 관리자 전용 (app.py check_auth에서 /admin/ 경로와 별도로 여기서 role 체크)"""
    if session.get("signinedMemberRole") != "admin":
        return redirect(url_for("auth.signin_form"))

    logs = load_sms_logs()
    logs_sorted = sorted(logs, key=lambda x: x.get("sent_at", ""), reverse=True)
    return render_template("dashboard/send_history.html", logs=logs_sorted)


@dashboard_bp.route("/log_detail/<int:log_id>")
def log_detail(log_id):
    logs   = load_fire_logs()
    log    = next((l for l in logs if l.get("id") == log_id), None)
    if not log:
        return redirect(url_for("dashboard.history"))
    return render_template("dashboard/log_detail.html", log=log)


# ── API ──────────────────────────────────────────────
@dashboard_bp.route("/api/logs")
def api_logs():
    """전체 로그 — 최신순, 필터 지원"""
    logs     = load_fire_logs()
    drone_id = request.args.get("drone")
    log_type = request.args.get("type")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per", 10))

    if drone_id and drone_id != "all":
        logs = [l for l in logs if l.get("drone_id") == drone_id]
    if log_type and log_type != "all":
        logs = [l for l in logs if l.get("type") == log_type]

    logs.sort(key=lambda x: x.get("time", ""), reverse=True)

    total   = len(logs)
    start   = (page - 1) * per_page
    end     = start + per_page
    paged   = logs[start:end]

    return jsonify({
        "total": total, 
        "page": page, 
        "per_page": per_page, 
        "logs": paged
    })

@dashboard_bp.route("/api/recent_logs")
def api_recent_logs():
    """관제 화면 최근 로그 10개"""
    logs = load_fire_logs()
    logs.sort(key=lambda x: x.get("time", ""), reverse=True)
    return jsonify(logs[:10])


@dashboard_bp.route("/api/latest_alert")
def api_latest_alert():
    """최신 화재 알림 — 7초 이내 발생한 항목"""
    logs = load_fire_logs()
    if not logs:
        return jsonify({"alert": False})
    logs.sort(key=lambda x: x.get("time", ""), reverse=True)
    latest = logs[0]
    try:
        log_time = datetime.strptime(latest["time"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - log_time <= timedelta(seconds=7):
            return jsonify({"alert": True, "log": latest})
    except Exception:
        print("Alert 타임스탬프 파싱 오류:", e)
    return jsonify({"alert": False})


@dashboard_bp.route("/api/stats")
def api_stats():
    """통계 데이터"""
    logs        = load_fire_logs()
    fire_count  = sum(1 for l in logs if l.get("type") == "화재")
    smoke_count = sum(1 for l in logs if l.get("type") == "연기")
    return jsonify({
        "total":  len(logs),
        "fire":   fire_count,
        "smoke":  smoke_count,
    })


# ── 비상 전송 채널 연동 뼈대 (향후 웹훅 및 외부 API 적용) ──

@dashboard_bp.route("/api/send_sms", methods=["POST"])
def api_send_sms():
    data = request.get_json() or {}
    log_id = data.get("log_id")
    # TODO: 알리고(Aligo) 또는 CoolSMS 또는 DISCORD 모듈 연동 구역
    return jsonify({"success": True, "message": f"현장 대원 비상 SMS 발송 완료 (로그 코드 #{log_id})"})


@dashboard_bp.route("/api/send_discord", methods=["POST"])
def api_send_discord():
    data = request.get_json() or {}
    log_id = data.get("log_id")
    # TODO: requests.post(DISCORD_WEBHOOK_URL, json=payload) 연동 구역
    return jsonify({"success": True, "message": f"상황실 디스코드 원격 상황 전파 완료 (로그 코드 #{log_id})"})