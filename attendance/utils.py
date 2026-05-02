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

    # clean number
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
        # 🔥 FALLBACK (no API)
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

    # 🔥 FUTURE: add real SMS API
    print(f"[SMS] {phone}: {message}")

    return True