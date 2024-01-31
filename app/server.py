from flask import Flask, make_response, jsonify, request, render_template
from functions import get_ics
import os, jinja2

os.environ["CC_BASE_URL"] = os.getenv("CC_BASE_URL", "")
os.environ["CC_ENABLE_NON_ICS_PATH"] = os.getenv("CC_ENABLE_NON_ICS_PATH", "false")
os.environ["CC_ENABLE_CACHING"] = os.getenv("CC_ENABLE_CACHING", "true")

app = Flask(__name__)

# Custom decorator to enable/disable routes based on environment variables
def conditional_route(envVar, targetRoutes=[]):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if (
                not targetRoutes
                or any(route in request.url_rule.rule for route in targetRoutes)
            ) and not os.getenv(envVar):
                return jsonify({"error": "This calendar does not exist"}), 404
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ICS download link
@app.route("/<calId>")
@conditional_route("CC_ENABLE_NON_ICS_PATH", ["/<calId>"])
@app.route("/ics/<calId>")
@app.route("/ics/<context>/<calId>")
def serve_ics(calId, context=None):
    try:
        resultCal = get_ics(calId, context)
        appResponse = make_response(resultCal, 200)
        appResponse.headers["Content-Disposition"] = (
            "attachment; filename=" + calId + ".ics"
        )
        appResponse.headers["Content-Type"] = "text/calendar; charset=utf-8"
    except FileNotFoundError as e:
        appResponse = make_response("An error occured: " + str(e), 404)
    return appResponse


# ICS Viewer
@app.route("/view/<calId>")
@app.route("/view/<context>/<calId>")
def view_ics(calId, context=None):
    calendarPath = calId if context is None else context + "/" + calId
    pageData={
        "calendarName": calId,
        "calendarId": calId,
        "calendarContext": context,
        "allowSubscribe": True,
        "calendarSubscribeLink": os.getenv("CC_BASE_URL") + "/ics/" + calendarPath
    }
    return render_template("view.html", **pageData)

# API
@app.route("/api/web-cal/get/<calId>")
@app.route("/api/web-cal/get/<context>/<calId>")
def api_web_get(calId, context=None):
    try:
        resultCal = get_ics(calId, context, format="tui")
        appResponse = make_response(resultCal, 200)
        appResponse.headers["Content-Type"] = "text/json; charset=utf-8"
    except FileNotFoundError as e:
        appResponse = make_response("An error occured: " + str(e), 404)
    return appResponse


app.run(host="0.0.0.0", port=8088)
