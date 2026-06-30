import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MEMBER_FILE       = os.path.join(BASE_DIR, "db", "members.json")
FIRE_LOG_FILE     = os.path.join(BASE_DIR, "db", "fire_logs.json")
SMS_LOG_FILE      = os.path.join(BASE_DIR, "db", "sms_logs.json")
NOTICE_FILE       = os.path.join(BASE_DIR, "db", "notices.json")
CONFIRM_LOG_FILE  = os.path.join(BASE_DIR, "db", "confirm_logs.json")

# ── Members ──────────────────────────────────────
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
    members = load_members()
    return [
        {"id": mid, **info}
        for mid, info in members.items()
        if info.get("approved", False)
    ]

# ── Fire Logs ─────────────────────────────────────
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

def get_next_log_id():
    logs = load_fire_logs()
    if not logs:
        return 1
    return max(l.get("id", 0) for l in logs) + 1

# ── SMS Logs ──────────────────────────────────────
def load_sms_logs():
    try:
        if not os.path.exists(SMS_LOG_FILE):
            return []
        with open(SMS_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_sms_log(entry):
    try:
        logs = load_sms_logs()
        logs.append(entry)
        os.makedirs(os.path.dirname(SMS_LOG_FILE), exist_ok=True)
        with open(SMS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving sms log:", e)

# ── Notices ───────────────────────────────────────
def load_notices():
    try:
        if not os.path.exists(NOTICE_FILE):
            return []
        with open(NOTICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading notices:", e)
        return []

def save_notices(notices):
    try:
        os.makedirs(os.path.dirname(NOTICE_FILE), exist_ok=True)
        with open(NOTICE_FILE, "w", encoding="utf-8") as f:
            json.dump(notices, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving notices:", e)

def get_next_notice_id():
    notices = load_notices()
    if not notices:
        return 1
    return max(n.get("id", 0) for n in notices) + 1

# ── Confirm Logs (사이렌 확인 이력) ──────────────────
def load_confirm_logs():
    """로그 확인 이력 불러오기"""
    try:
        if not os.path.exists(CONFIRM_LOG_FILE):
            return []
        with open(CONFIRM_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading confirm logs:", e)
        return []

def save_confirm_log(entry):
    """로그 확인 이력 저장 (하나씩 추가)"""
    try:
        logs = load_confirm_logs()
        # 자동 ID 부여
        entry["id"] = max((l.get("id", 0) for l in logs), default=0) + 1
        logs.append(entry)
        os.makedirs(os.path.dirname(CONFIRM_LOG_FILE), exist_ok=True)
        with open(CONFIRM_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving confirm log:", e)
