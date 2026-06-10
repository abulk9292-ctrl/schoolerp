from datetime import datetime


def get_current_session():
    today = datetime.now()
    year = today.year

    if today.month >= 4:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def global_session(request):
    current_year = datetime.now().year

    sessions = []
    for y in range(current_year - 3, current_year + 4):
        sessions.append(f"{y}-{y + 1}")

    selected_session = request.session.get("selected_session")

    if not selected_session:
        selected_session = get_current_session()

    return {
        "sessions": sessions,
        "selected_session": selected_session,
    }