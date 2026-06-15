from urllib.parse import quote


# =========================
# SAFE IMPORT
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
WHATSAPP_API_KEY = ""   # পরে API key বসাবেন
PHONE_PREFIX = "+91"


# =========================
# PHONE CLEANER
# =========================

def clean_phone_number(phone):
    if not phone:
        return ""

    phone = str(phone).strip().replace(" ", "").replace("-", "")

    if phone.startswith("+91"):
        phone = phone[3:]

    if phone.startswith("91") and len(phone) > 10:
        phone = phone[2:]

    return phone


# =========================
# WHATSAPP SEND
# =========================

def send_whatsapp_message(phone, message):
    phone = clean_phone_number(phone)

    if not phone:
        print("❌ No phone number")
        return False

    if REQUESTS_AVAILABLE and WHATSAPP_API_KEY:
        try:
            url = (
                f"{WHATSAPP_API_URL}"
                f"?phone={PHONE_PREFIX}{phone}"
                f"&text={quote(str(message))}"
                f"&apikey={WHATSAPP_API_KEY}"
            )

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                print(f"✅ WhatsApp SENT to {phone}")
                return True

            print(f"❌ WhatsApp failed: {response.status_code}")
            return False

        except Exception as e:
            print(f"❌ WhatsApp Error: {e}")
            return False

    print(f"[WhatsApp MOCK] {phone}: {message}")
    return True


# =========================
# SMS SEND SAFE MOCK
# =========================

def send_sms_message(phone, message):
    phone = clean_phone_number(phone)

    if not phone:
        print("❌ No phone number")
        return False

    print(f"[SMS MOCK] {phone}: {message}")
    return True


# =========================
# DAY NAME HELPER
# =========================

def get_day_name(date):
    return date.strftime("%A")


# =========================
# SCHOOL SETTINGS HELPER
# =========================

def get_school_settings():
    try:
        from settings_app.models import GeneralSetting
        return GeneralSetting.get_settings()
    except Exception:
        return None


# =========================
# HOLIDAY CHECK
# =========================

def get_holiday_status(date):
    """
    Attendance Holiday Logic

    Priority:
    1. Holiday Database
    2. General Settings Weekly Holiday
    3. General Settings Half Day
    """

    try:
        from .models import Holiday

        holiday = Holiday.objects.filter(
            date=date,
            is_active=True
        ).first()

        if holiday:

            if holiday.is_half_day:
                return {
                    "is_holiday": True,
                    "is_half_day": True,
                    "title": holiday.title,
                    "status": "Half Day",
                    "source": "database",
                }

            return {
                "is_holiday": True,
                "is_half_day": False,
                "title": holiday.title,
                "status": "Holiday",
                "source": "database",
            }

    except Exception:
        pass

    day_name = get_day_name(date)
    settings = get_school_settings()

    if settings:

        weekly_holiday = getattr(
            settings,
            "weekly_holiday",
            None
        )

        half_day_enabled = getattr(
            settings,
            "half_day_enabled",
            False
        )

        half_day = getattr(
            settings,
            "half_day",
            None
        )

        # Weekly Holiday
        if weekly_holiday and day_name == weekly_holiday:

            return {
                "is_holiday": True,
                "is_half_day": False,
                "title": f"{weekly_holiday} Weekly Holiday",
                "status": "Holiday",
                "source": "settings",
            }

        # Half Day
        if (
            half_day_enabled
            and half_day
            and day_name == half_day
        ):

            return {
                "is_holiday": True,
                "is_half_day": True,
                "title": f"{half_day} Half Day",
                "status": "Half Day",
                "source": "settings",
            }

    # Normal Working Day

    return {
        "is_holiday": False,
        "is_half_day": False,
        "title": "",
        "status": "",
        "source": "normal",
    }