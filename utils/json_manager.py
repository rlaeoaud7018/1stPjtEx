import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MEMBER_FILE   = os.path.join(BASE_DIR, "db", "members.json")
FIRE_LOG_FILE = os.path.join(BASE_DIR, "db", "fire_logs.json")
SMS_LOG_FILE  = os.path.join(BASE_DIR, "db", "sms_logs.json")

# ──────────────────────────────────────────────
# Members
# ──────────────────────────────────────────────
def load_members():
    try:
        if not os.path.exists(MEMBER_FILE):
            return {}
        with open(MEMBER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading members:", e)
        return {}

def save_members(members):
    try:
        os.makedirs(os.path.dirname(MEMBER_FILE), exist_ok=True)
        with open(MEMBER_FILE, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving members:", e)

def get_approved_members_with_contact():
    """승인된 모든 회원의 이름/전화번호/이메일 반환 (SMS 발송용)"""
    members = load_members()
    result = []
    for member_id, info in members.items():
        if info.get("approved", False):
            result.append({
                "id": member_id,
                "name": info.get("name", ""),
                "phone": info.get("phone", ""),
                "email": info.get("email", "")
            })
    return result

# ──────────────────────────────────────────────
# Fire Logs
# ──────────────────────────────────────────────
def load_fire_logs():
    try:
        if not os.path.exists(FIRE_LOG_FILE):
            return []
        with open(FIRE_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading fire logs:", e)
        return []

def save_fire_logs(logs):
    try:
        os.makedirs(os.path.dirname(FIRE_LOG_FILE), exist_ok=True)
        with open(FIRE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving fire logs:", e)

# ──────────────────────────────────────────────
# SMS Logs
# ──────────────────────────────────────────────
def load_sms_logs():
    try:
        if not os.path.exists(SMS_LOG_FILE):
            return []
        with open(SMS_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading sms logs:", e)
        return []

def save_sms_log(entry):
    """단일 발송 이력 항목을 sms_logs.json에 append"""
    try:
        logs = load_sms_logs()
        logs.append(entry)
        os.makedirs(os.path.dirname(SMS_LOG_FILE), exist_ok=True)
        with open(SMS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving sms log:", e)
