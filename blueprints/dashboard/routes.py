from flask import Blueprint, Response, render_template, session, redirect, jsonify, url_for
from ai.camera_manager import get_frame
from utils.json_manager import (
    load_fire_logs, get_approved_members_with_contact, save_sms_log
)
import cv2
import time
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# 데모용 위치 매핑 (드론 ID → 위치)
DRONE_LOCATION_MAP = {
    "DR-01": "강릉 옥계 산림 지역",
    "DR-02": "속초 설악 산림 지역",
    "DR-03": "장흑 개원 산림 지역",
    "DR-04": "평창 오대산 지역",
    "DR-05": "홍천 내촌 산림 지역",
}


@dashboard_bp.route("/")
@dashboard_bp.route("/monitor")
def monitor():
    if session.get("signinedMemberId") is None:
        return redirect(url_for("auth.signin_form"))
    return render_template("dashboard/monitor.html")


@dashboard_bp.route("/history")
def history():
    if session.get("signinedMemberId") is None:
        return redirect(url_for("auth.signin_form"))
    return render_template("dashboard/history.html")


@dashboard_bp.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@dashboard_bp.route("/api/logs")
def get_logs():
    if session.get("signinedMemberId") is None:
        return jsonify({"error": "Unauthorized"}), 401
    logs = load_fire_logs()
    return jsonify(list(reversed(logs)))


@dashboard_bp.route("/api/latest_alert")
def latest_alert():
    if session.get("signinedMemberId") is None:
        return jsonify({"error": "Unauthorized"}), 401
    logs = load_fire_logs()
    if not logs:
        return jsonify({"alert": False})

    latest_log = logs[-1]
    log_time   = datetime.strptime(latest_log["time"], "%Y-%m-%d %H:%M:%S")
    time_diff  = (datetime.now() - log_time).total_seconds()

    is_danger = time_diff < 7
    if is_danger:
        drone_id = latest_log.get("drone_id", "DR-01")
        location = DRONE_LOCATION_MAP.get(drone_id, "미상 지역")
        detect_time = log_time.strftime("%H:%M:%S")
        return jsonify({
            "alert":      True,
            "drone_id":   drone_id,
            "detect_time": detect_time,
            "location":   location,
            "type":       latest_log.get("type"),
            "confidence": latest_log.get("confidence")
        })
    return jsonify({"alert": False})


@dashboard_bp.route("/api/send_alert", methods=["POST"])
def send_alert():
    """대응 조치 버튼 클릭 시 호출.
    승인된 모든 회원에게 데모 SMS 발송 시뮬레이션 후 이력을 DB에 저장.
    """
    if session.get("signinedMemberId") is None:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    drone_id    = data.get("drone_id",    "DR-??")
    detect_time = data.get("detect_time", datetime.now().strftime("%H:%M:%S"))
    location    = data.get("location",    "미상 지역")
    sent_by     = session.get("signinedMemberName", "관리자")

    # 발송 대상: 승인된 모든 회원
    targets = get_approved_members_with_contact()
    sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sms_message = (
        f"[소방 관제 시스템 긴급 알림]\n"
        f"산불 발생 감지!\n"
        f"드론 ID : {drone_id}\n"
        f"감지 시간 : {detect_time}\n"
        f"위치 : {location}\n"
        f"즉각 대응 조치 바랍니다."
    )

    records = []
    for member in targets:
        record = {
            "sent_at":   sent_at,
            "sent_by":   sent_by,
            "recipient_id":   member["id"],
            "recipient_name": member["name"],
            "phone":     member["phone"],
            "email":     member["email"],
            "message":   sms_message,
            "drone_id":  drone_id,
            "detect_time": detect_time,
            "location":  location,
            "status":    "DEMO_SENT"   # 실제 발송은 추후 연동
        }
        save_sms_log(record)
        records.append(record)

    return jsonify({
        "success":    True,
        "sent_count": len(records),
        "sent_at":    sent_at,
        "message":    sms_message,
        "recipients": [{"name": r["recipient_name"], "phone": r["phone"]} for r in records]
    })


def generate_frames():
    while True:
        frame = get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            time.sleep(0.1)
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )
        time.sleep(0.03)
