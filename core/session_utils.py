from datetime import date, datetime


def get_current_session():
    today = datetime.now()
    year = today.year

    if today.month >= 4:
        return f"{year}-{year + 1}"

    return f"{year - 1}-{year}"


def get_session_list():
    current_year = datetime.now().year
    return [f"{y}-{y + 1}" for y in range(current_year - 3, current_year + 4)]


def get_selected_session(request):
    selected_session = request.session.get("selected_session")

    if not selected_session:
        selected_session = get_current_session()
        request.session["selected_session"] = selected_session

    return selected_session


def get_session_dates(selected_session):
    try:
        start_year = int(selected_session.split("-")[0])
        end_year = int(selected_session.split("-")[1])
    except Exception:
        selected_session = get_current_session()
        start_year = int(selected_session.split("-")[0])
        end_year = int(selected_session.split("-")[1])

    return date(start_year, 4, 1), date(end_year, 3, 31)