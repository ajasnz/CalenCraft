from flask import Flask, make_response
from functions import start_build

app = Flask(__name__)

@app.route('/<calId>')
def main(calId):
    try:
        resultCal = start_build(calId)
        appResponse = make_response(resultCal, 200)
        appResponse.headers["Content-Disposition"] = "attachment; filename=" + calId + ".ics"
        appResponse.headers["Content-Type"] = "text/calendar; charset=utf-8"
    except FileNotFoundError:
        appResponse = make_response("This calendar does not exist", 404)
    return appResponse 
      


app.run(host='0.0.0.0', port=8088)