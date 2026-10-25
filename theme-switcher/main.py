from time import sleep
import base64
import json
import os
import urllib.request

sensor_url = os.environ.get("SENSOR_URL")
grafana_url = os.environ.get("GRAFANA_URL")
grafana_user = os.environ.get("GRAFANA_USER")
grafana_password = os.environ.get("GRAFANA_PASSWORD")
scope = os.environ.get("GRAFANA_SCOPE")

dark_below_lux = 50
prefs_url = f"{grafana_url}/api/" f"{'org' if scope == 'org' else 'user'}/preferences"
auth = (
    "Basic " + base64.b64encode(f"{grafana_user}:{grafana_password}".encode()).decode()
)


def decide_theme(lux: float):
    if lux < dark_below_lux:
        return "dark"
    else:
        return "light"


def read_lux():
    with urllib.request.urlopen(sensor_url, timeout=5) as response:
        data = json.load(response)
        return float(data["data"]["value"])


def grafana(method: str, data: dict | None = None):
    request = urllib.request.Request(
        prefs_url,
        method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def get_theme():
    return grafana("GET").get("theme") or ""


def set_theme(theme: str, current_prefs: dict):
    grafana("PATCH", {"theme": theme})

    actual_theme = get_theme()
    if actual_theme != theme:
        print(f"Grafana did not accept theme: '{theme}' ")
        print(f"Current theme: '{actual_theme}'")

    return actual_theme


def main():
    try:
        lux = read_lux()
        preferences = grafana("GET")
        current_theme = preferences.get("theme") or ""
        desired_theme = decide_theme(lux)

        if current_theme != desired_theme:
            set_theme(desired_theme, preferences)

    except Exception as error:
        print(f"Error: {error}")

    sleep(2)


if __name__ == "__main__":
    main()
