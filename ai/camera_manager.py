import os
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
import cv2
import numpy as np
import threading
import time
from datetime import datetime, timedelta
from utils.json_manager import load_fire_logs, save_fire_logs, get_next_log_id

camera1 = None
camera2 = None

camera_lock1 = threading.Lock()
camera_lock2 = threading.Lock()

# ── ESP32-CAM 스트리밍 주소 (현장 IP로 수정 필요) ──────
ESP32_STREAM1_URL = "http://192.168.137.150:81/stream"
ESP32_STREAM2_URL = "http://192.168.137.26:81/stream"

# ── YOLO 모델 (best.pt 준비 후 주석 해제) ───────────────
# from ultralytics import YOLO
# try:
#     model = YOLO("ai/best.pt")
#     print("YOLO 모델 로드 성공")
# except Exception as e:
#     print("YOLO 모델 로드 실패:", e)
#     model = None
model = None

last_alert_time1 = None
last_alert_time2 = None


def init_camera():
    global camera1, camera2
    print("ESP32-CAM 연결 시도...")
    try:
        camera1 = cv2.VideoCapture(ESP32_STREAM1_URL, cv2.CAP_FFMPEG)
        camera2 = cv2.VideoCapture(ESP32_STREAM2_URL, cv2.CAP_FFMPEG)
        if camera1.isOpened():
            print("카메라1 연결 성공!")

        else:
            print("카메라1 연결 실패 — NO SIGNAL 모드로 실행")

        if camera2.isOpened():
            print("카메라2 연결 성공!")

        else:
            print("카메라2 연결 실패 — NO SIGNAL 모드로 실행")
    except Exception as e:
        print(f"카메라 초기화 오류: {e}")
        camera1, camera2 = None


def reconnect_camera(camera_num):
    global camera1, camera2

    print(f"카메라 {camera_num} 재연결 시도...")

    try:
        if camera_num == 1:
            if camera1:
                camera1.release()

            camera1 = cv2.VideoCapture(ESP32_STREAM1_URL)

        else:
            if camera2:
                camera2.release()

            camera2 = cv2.VideoCapture(ESP32_STREAM2_URL)

    except Exception:
        if camera_num == 1:
            camera1 = None
        else:
            camera2 = None


def get_no_signal_frame():
    """카메라 미연결 시 NO SIGNAL 프레임 생성"""
    h, w = 360, 640
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:] = [8, 14, 24]

    # 격자
    for x in range(0, w, 80):
        cv2.line(frame, (x, 0), (x, h), (18, 30, 48), 1)
    for y in range(0, h, 60):
        cv2.line(frame, (0, y), (w, y), (18, 30, 48), 1)

    # 중앙 박스
    cx, cy = w // 2, h // 2
    cv2.rectangle(frame, (cx - 130, cy - 55), (cx + 130, cy + 55), (35, 60, 95), 1)
    cv2.putText(frame, "NO SIGNAL", (cx - 95, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (55, 85, 120), 2)
    cv2.putText(frame, "ESP32-CAM NOT CONNECTED", (cx - 118, cy + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 65, 95), 1)

    # 코너 데코
    clr = (45, 80, 120)
    for (ox, oy) in [(10, 10), (w - 10, 10), (10, h - 10), (w - 10, h - 10)]:
        sx = -1 if ox > w // 2 else 1
        sy = -1 if oy > h // 2 else 1
        cv2.line(frame, (ox, oy), (ox + 30 * sx, oy), clr, 2)
        cv2.line(frame, (ox, oy), (ox, oy + 20 * sy), clr, 2)

    return frame


def save_fire_log_entry(detected_type, confidence, drone_id="DR-01", location="미상 지역"):
    logs   = load_fire_logs()
    log_id = get_next_log_id()
    logs.append({
        "id":         log_id,
        "time":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "drone_id":   drone_id,
        "type":       detected_type,
        "confidence": round(confidence, 2),
        "location":   location,
        "status":     "확인",
        "message":    f"{detected_type} 감지됨",
    })
    save_fire_logs(logs)
    print(f"[{detected_type}] 로그 저장 완료 — {location}")


def get_frame(camera_num):
    global camera1, camera2
    global last_alert_time1, last_alert_time2

    if camera_num == 1:
        camera = camera1
        lock = camera_lock1
        last_alert_time = last_alert_time1
    else:
        camera = camera2
        lock = camera_lock2
        last_alert_time = last_alert_time2

    if camera is None or not camera.isOpened():
        return get_no_signal_frame()

    try:
        with lock:
            success, frame = camera.read()

        if not success:
            reconnect_camera(camera_num)
            return get_no_signal_frame()

        # YOLO 감지
        if model is not None:
            results = model(frame, verbose=False)
            result = results[0]

            is_fire_event = False
            detected_type = None
            max_conf = 0.0

            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id == 0:
                    label_text = "FIRE"
                    detected_type = "화재"
                elif class_id == 1:
                    label_text = "SMOKE"
                    detected_type = "연기"
                else:
                    continue

                if confidence >= 0.5:
                    is_fire_event = True
                    max_conf = max(max_conf, confidence)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    color = (0, 0, 255) if detected_type == "화재" else (0, 140, 180)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    cv2.putText(
                        frame,
                        f"{label_text} {confidence:.0%}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        color,
                        2
                    )

            if is_fire_event:
                now = datetime.now()

                if last_alert_time is None or now - last_alert_time > timedelta(seconds=5):
                    save_fire_log_entry(
                        detected_type,
                        max_conf,
                        camera_num   # 몇 번 카메라인지 저장
                    )

                    if camera_num == 1:
                        last_alert_time1 = now
                    else:
                        last_alert_time2 = now

        return frame

    except Exception as e:
        print(e)
        return get_no_signal_frame()
    
def get_raw_frame(camera_num):
    global camera1, camera2

    if camera_num == 1:
        camera = camera1
        lock = camera_lock1
    else:
        camera = camera2
        lock = camera_lock2

    if camera is None or not camera.isOpened():
        return get_no_signal_frame()

    try:
        with lock:
            success, frame = camera.read()

        if not success:
            reconnect_camera(camera_num)
            return get_no_signal_frame()

        return frame

    except Exception as e:
        print(e)
        return get_no_signal_frame()
    
latest_frames = {1: None, 2: None}
frame_locks = {1: threading.Lock(), 2: threading.Lock()}

def camera_worker(camera_num, src):
    print(f"[알림] 카메라 {camera_num} 연결 시도 중: {src}")
    while True:
        cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        if cap.isOpened():
            print(f"[성공] 카메라 {camera_num} 연결됨")
            while True:
                success, frame = cap.read()
                if not success:
                    print(f"[경고] 카메라 {camera_num} 프레임 수신 실패")
                    break
                with frame_locks[camera_num]:
                    latest_frames[camera_num] = frame.copy()
            cap.release()
        else:
            time.sleep(5)

def get_shared_frame(camera_num):
    with frame_locks[camera_num]:
        return latest_frames[camera_num].copy() if latest_frames[camera_num] is not None else None