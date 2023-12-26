import json, requests
from icalendar import Calendar, Event
import regex as re
from sanitize_filename import sanitize
import datetime

# main handler
def start_build(calId):
    calFileName = sanitize(calId) + ".json"
    mergeCal = Calendar()
    mergeCal.add('prodid', '-//AJAS Calendars//')
    mergeCal.add('version', '2.0')
    
    try:
        with open("./app/config/" + calFileName) as f:
            baseConfig = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("This calendar does not exist")
    for calConfig in baseConfig:
        sourceCal = fetch_origin(calConfig["source"])
        if "datestamp" in calConfig:
            currentTime = datetime.datetime.now().strftime(calConfig["datestamp"]["dateformat"])
            datestamp = calConfig["datestamp"]["stamptemplate"].replace("[[date]]", currentTime)
            if calConfig["datestamp"]["position"] == "prepend":
                calConfig["alter"]["description"]["prepend"] = datestamp + calConfig["alter"]["description"]["prepend"]
            elif calConfig["datestamp"]["position"] == "append":
                calConfig["alter"]["description"]["append"] = calConfig["alter"]["description"]["append"] + datestamp
        if "include" in calConfig:
            sourceCal = include_filter(sourceCal, calConfig["include"], calConfig)
        if "alter" in calConfig and "include" not in calConfig: #if there is an include filter, events are altered at inclusion, so we don't want to do it again
            sourceCal = alter_calendar(sourceCal, calConfig["alter"])
        mergeCal = merge_calendars(mergeCal, sourceCal)
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

# handle alterations for calendar
def alter_calendar(sourceCal, alterations):
    for event in sourceCal.walk():
        event = alter_event(event, alterations)
    return sourceCal   

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

# filter for inclusions
def include_filter(calendar, includeFilters, calConfig):
    filteredCal = Calendar()
    for property in includeFilters:
        doAddEvent = False
        if "contains" in property:
            for event in calendar.walk():
                if property["contains"] in event[property]:
                    doAddEvent = True
        if "regex" in property:
            for event in calendar.walk():
                if re.search(property["regex"], event[property]):
                    doAddEvent = True
        if "equals" in property:
            for event in calendar.walk():
                if event[property] == property["equals"]:
                    doAddEvent = True
        if doAddEvent:
            if "alter" in calConfig:
                event = alter_event(event, calConfig["alter"])
            filteredCal.add_component(event)
    return filteredCal
    