from flask import Flask, make_response, jsonify, request
from functions import get_ics
import os

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
    except FileNotFoundError:
        appResponse = make_response("This calendar does not exist", 404)
    return appResponse


# ICS Viewer
@app.route("/view/<calId>")
@app.route("/view/<context>/<calId>")
def view_ics(calId, context=None):
    return


app.run(host="0.0.0.0", port=8088)
