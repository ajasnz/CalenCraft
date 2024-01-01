# TODO test include filters
# TODO test exclude filters

import json, requests
from icalendar import Calendar, Event
import regex as re
from sanitize_filename import sanitize
import datetime


# main handler
def start_build(calId):
    calFileName = sanitize(calId) + ".json"
    mergeCal = Calendar()
    mergeCal.add("prodid", "-//CalenCraft//")
    mergeCal.add("version", "2.0")

    try:
        with open("./app/config/" + calFileName) as f:
            baseConfig = json.load(f)

    except FileNotFoundError:
        raise FileNotFoundError("This calendar does not exist")
    for calConfig in baseConfig:
        sourceCal = fetch_origin(calConfig["source"])
        
        if "datestamp" in calConfig:
            dateStamp = str(calConfig["datestamp"]["stamptemplate"]).replace("[[date]]", datetime.datetime.now().strftime(calConfig["datestamp"]["dateformat"]))
        else:
            dateStamp = None
        newCal = Calendar()
        for event in sourceCal.walk():
            if "include" in calConfig or "exclude" in calConfig:
                event = filter_event(event, includes=calConfig.get("include", False), excludes=calConfig.get("exclude", False))
            if event is None:
                continue
            if "alter" in calConfig:
                event = alter_event(event, calConfig["alter"])
            if dateStamp != None:
                if calConfig["datestamp"]["stampposition"] == "prepend":
                    event["description"] = dateStamp + "\n\n" + event.get("description", "")
                else:
                    event["description"] = event.get("description","") + "\n\n" + dateStamp
            newCal.add_component(event)
        mergeCal = merge_calendars(mergeCal, newCal)
    return mergeCal.to_ical()


# get the origin calendar
def fetch_origin(source):
    sourceCalContent = requests.get(source).text
    sourceCal = Calendar.from_ical(sourceCalContent)
    return sourceCal


# merge the origin calendar into the merge calendar
def merge_calendars(mergeCal, sourceCal):
    for component in sourceCal.walk():
        if component.name == "VEVENT":
            mergeCal.add_component(component)

    return mergeCal

# handle alterations for a single event
def alter_event(event, alterations):
    properties = alterations.keys()
    for property in properties:
        try:
            if "replace" in alterations[property]:
                event[property] = alterations[property]["replace"]
            if "prepend" in alterations[property]:
                value = event[property] if property in event else ""
                event[property] = alterations[property]["prepend"] + value
            if "append" in alterations[property]:
                value = event[property] if property in event else ""
                event[property] = value + alterations[property]["append"]
        except KeyError:
            pass

    return event


# handle includes and excludes for a single event
def filter_event(event, **kwargs):
    doIncludeEvent = False
    try:
        if "includes" in kwargs and kwargs["includes"] is not False:
            includes = kwargs["includes"]
            for property in includes:
                if "contains" in includes[property]:
                    print(f"Checking if {includes[property]['contains']} is in {event[property]}: {includes[property]['contains'] in event[property]}")
                    if includes[property]["contains"] in event[property]:
                        doIncludeEvent = True
                        break
                if "regex" in includes[property]:
                    if re.search(includes[property]["regex"], event[property]):
                        doIncludeEvent = True
                        break
                if "equals" in includes[property]:
                    if event[property] == includes[property]["equals"]:
                        doIncludeEvent = True
                        break
        if "excludes" in kwargs and kwargs["excludes"] is not False:
            excludes = kwargs["excludes"]
            for property in excludes:
                if "contains" in excludes[property]:
                    if excludes[property]["contains"] in event[property]:
                        doIncludeEvent = False
                        break
                    else:
                        doIncludeEvent = True
                if "regex" in excludes[property]:
                    if re.search(excludes[property]["regex"], event[property]):
                        doIncludeEvent = False
                        break
                    else:
                        doIncludeEvent = True
                if "equals" in excludes[property]:
                    if event[property] == excludes[property]["equals"]:
                        doIncludeEvent = False
                        break
                    else:
                        doIncludeEvent = True
    except KeyError:
        pass
    if doIncludeEvent:
        return event
    else:
        return None