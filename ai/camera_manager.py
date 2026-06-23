import cv2
import threading
from datetime import datetime, timedelta
# from ultralytics import YOLO
from utils.json_manager import load_fire_logs, save_fire_logs

camera = None
camera_lock = threading.Lock()

# ESP32-CAM 영상 스트리밍 주소 (데모 현장 IP 주소로 추후 수정)
ESP32_STREAM_URL = "http://192.168.137.158:82/stream"

# YOLO 모델 로드 (초기 뼈대 연동용으로 yolov8n.pt 사용)
# 1주차 학습 완료 후 'ai/fire_smoke_best.pt' 등으로 경로 교체 가능
try:
    model = YOLO("yolov8n.pt")
    print("YOLOv8 Model loaded successfully in new project.")
except Exception as e:
    print("Failed to load YOLO Model in new project:", e)
    model = None

last_alert_time = None

def init_camera():
    global camera
    if camera is None:
        print("Camera connecting to ESP32-CAM...")
        camera = cv2.VideoCapture(ESP32_STREAM_URL)
        print("Camera connection initialized.")

def reconnect_camera():
    global camera
    print("Reconnecting to ESP32 Camera...")
    try:
        if camera is not None:
            camera.release()
    except:
        pass
    camera = cv2.VideoCapture(ESP32_STREAM_URL)
    print("Camera reconnected.")

def save_fire_log(detected_class, confidence):
    logs = load_fire_logs()
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": detected_class,          # "FIRE" 또는 "SMOKE"
        "confidence": round(confidence, 2),
        "message": f"Danger! {detected_class} detected with {confidence:.2f} confidence."
    })
    save_fire_logs(logs)
    print(f"[{detected_class}] Fire event log saved to database.")

def get_frame():
    global camera
    global last_alert_time

    if camera is None:
        return None

    try:
        if not camera.isOpened():
            reconnect_camera()
            return None

        with camera_lock:
            success, frame = camera.read()

        if not success:
            reconnect_camera()
            return None

        # 모델 미로드 시 원본 프레임 반환
        if model is None:
            return frame

        # YOLO 화재/연기 감지 추론
        results = model(frame, verbose=False)
        result = results[0]

        is_fire_event = False
        detected_type = None
        max_conf = 0.0

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # --- 임시 매핑 (yolov8n.pt 기본 모델 사용 시 데모 테스트용) ---
            # 0=person -> FIRE(Demo), 24=backpack -> SMOKE(Demo)로 임시 처리
            is_detected = False
            label_text = "Unknown"
            
            if class_id == 0:  # 사람 -> 불꽃(FIRE) 대역용 임시
                label_text = "FIRE (Demo)"
                is_detected = True
                detected_type = "FIRE"
            elif class_id == 24: # 배낭 -> 연기(SMOKE) 대역용 임시
                label_text = "SMOKE (Demo)"
                is_detected = True
                detected_type = "SMOKE"
            
            # --- 커스텀 모델(best.pt) 사용 시 아래와 같이 수정 ---
            # if class_id == 0:  # 0: fire
            #     label_text = "FIRE"
            #     is_detected = True
            #     detected_type = "FIRE"
            # elif class_id == 1: # 1: smoke
            #     label_text = "SMOKE"
            #     is_detected = True
            #     detected_type = "SMOKE"
            
            if is_detected and confidence >= 0.5:
                is_fire_event = True
                if confidence > max_conf:
                    max_conf = confidence
                
                # 경계 박스 렌더링
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 0, 255) if detected_type == "FIRE" else (128, 128, 128)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"{label_text} {confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )

        # 감지 발생 시 5초마다 로그 기록
        if is_fire_event:
            now = datetime.now()
            if last_alert_time is None or now - last_alert_time > timedelta(seconds=5):
                save_fire_log(detected_type, max_conf)
                last_alert_time = now
                
                # 경고 오버레이 텍스트 추가
                cv2.putText(
                    frame,
                    "FIRE ALERT!",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 0, 255),
                    3
                )

        return frame

    except Exception as e:
        print("Camera processing error:", e)
        reconnect_camera()
        return None
