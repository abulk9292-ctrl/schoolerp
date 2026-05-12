# =========================
# SAFE IMPORT (NO ERROR)
# =========================
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# =========================
# CONFIG
# =========================
WHATSAPP_API_URL = "https://api.callmebot.com/whatsapp.php"
WHATSAPP_API_KEY = ""   # 🔥 এখানে পরে key বসাবে
PHONE_PREFIX = "+91"


# =========================
# WHATSAPP SEND
# =========================
def send_whatsapp_message(phone, message):

    if not phone:
        print("❌ No phone number")
        return False

    phone = str(phone).strip().replace(" ", "")

    if REQUESTS_AVAILABLE and WHATSAPP_API_KEY:
        try:
            url = f"{WHATSAPP_API_URL}?phone={PHONE_PREFIX}{phone}&text={message}&apikey={WHATSAPP_API_KEY}"
            requests.get(url, timeout=10)

            print(f"✅ WhatsApp SENT to {phone}")
            return True

        except Exception as e:
            print(f"❌ WhatsApp Error: {e}")
            return False

    else:
        print(f"[WhatsApp MOCK] {phone}: {message}")
        return True


# =========================
# SMS SEND (SAFE)
# =========================
def send_sms_message(phone, message):

    if not phone:
        print("❌ No phone number")
        return False

    phone = str(phone).strip()

    print(f"[SMS] {phone}: {message}")

    return True


# =========================
# HOLIDAY CHECK
# =========================
def get_holiday_status(date):
    """
    Monday = Weekly Holiday
    Friday = Half Day
    Database Holiday = Special/Eid/Emergency holiday
    """

    from .models import Holiday

    holiday = Holiday.objects.filter(date=date).first()

    if holiday:
        if holiday.is_half_day:
            return {
                "is_holiday": True,
                "is_half_day": True,
                "title": holiday.title,
                "status": "Half Day Holiday",
            }

        return {
            "is_holiday": True,
            "is_half_day": False,
            "title": holiday.title,
            "status": "Holiday",
        }

    # Monday
    if date.weekday() == 0:
        return {
            "is_holiday": True,
            "is_half_day": False,
            "title": "Weekly Holiday",
            "status": "Holiday",
        }

    # Friday
    if date.weekday() == 4:
        return {
            "is_holiday": True,
            "is_half_day": True,
            "title": "Friday Half Day",
            "status": "Half Day",
        }

    return {
        "is_holiday": False,
        "is_half_day": False,
        "title": "",
        "status": "",
    }