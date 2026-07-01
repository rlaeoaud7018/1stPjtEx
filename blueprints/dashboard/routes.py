from flask import Blueprint, render_template, Response, jsonify, session, redirect, url_for, request
from ai.camera_manager import get_frame
from utils.json_manager import load_fire_logs, save_confirm_log
from datetime import datetime, timedelta
import cv2
import requests

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def generate_frames():
    import time
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
    from flask import session as flask_session
    if flask_session.get("signinedMemberRole") != "admin":
        return redirect(url_for("auth.signin_form"))
    from utils.json_manager import load_sms_logs
    logs = load_sms_logs()
    return render_template("dashboard/send_history.html", logs=logs)


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

    return jsonify({"total": total, "page": page, "per_page": per_page, "logs": paged})


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
        pass
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


# ── 로그 확인 이력 저장 ──────────────────────────────
@dashboard_bp.route("/api/confirm_log", methods=["POST"])
def api_confirm_log():
    """
    실시간 관제 화면에서 사이렌 버튼 클릭 → '확인' 또는 '알림 발송' 시 호출.
    확인한 사람과 해당 화재 로그 정보를 confirm_logs.json에 저장.
    """
    data = request.get_json() or {}

    entry = {
        "action":       data.get("action", "확인"),        # "확인" 또는 "알림발송"
        "confirmed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "drone_id":     data.get("drone_id",  "-"),
        "fire_type":    data.get("fire_type", "-"),        # "화재" 또는 "연기"
        "location":     data.get("location",  "-"),
        "fire_time":    data.get("fire_time", "-"),        # 화재 발생 시각
        "confirmed_by": session.get("signinedMemberName", "알 수 없음"),
    }

    save_confirm_log(entry)
    return jsonify({"success": True})


# ── SMS / Discord 전송 뼈대 ──────────────────────────
@dashboard_bp.route("/api/send_sms", methods=["POST"])
def api_send_sms():
    log_id = request.json.get("log_id")
    # 실제 SMS 발송 로직 연결 예정
    return jsonify({"success": True, "message": f"SMS 전송 완료 (Log #{log_id})"})


@dashboard_bp.route("/api/send_discord", methods=["POST"])
def api_send_discord():
    WEBHOOK_URL = "https://discordapp.com/api/webhooks/1521402162247110708/dosKCCC0mVLCe0mbeVTCExC5W7HxyZaP8nEv8qAPNTNXbmIgGUQdKpBaruQ_Ig5b08Wl"

    data = request.get_json()
    log_id = data.get("log_id")

    all_logs = load_fire_logs()
    target_log = next((l for l in all_logs if l.get("id") == log_id), None)

    if not target_log:
        return jsonify({"success": False, "message": "로그 데이터를 찾을 수 없습니다."}), 404

    message = f"------드론 탐지 알림------\n- 드론번호:{target_log.get('drone_id')}\n- 위치: {target_log.get('location')}\n- 유형: {target_log.get('type')}\n- 신뢰도: {target_log.get('confidence')}"
    response = requests.post(WEBHOOK_URL, json={"content": message})
    
    return jsonify({"success": True, "message": f"Discord 전송 완료 (Log #{response.status_code})"})
