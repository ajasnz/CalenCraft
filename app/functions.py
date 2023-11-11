import json, requests
from icalendar import Calendar, Event
import regex as re
from sanitize_filename import sanitize

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
        if "include" in calConfig:
            sourceCal = include_filter(sourceCal, calConfig["include"])
        if "alter" in calConfig:
            sourceCal = alter_calendar(sourceCal, calConfig["alter"])
        mergeCal = merge_calendars(mergeCal, sourceCal)
    return mergeCal.to_ical()
        

# get the origin calendar
def fetch_origin(source):
    sourceCal = Calendar.from_ical(requests.get(source).text)
    return sourceCal

# merge the origin calendar into the merge calendar
def merge_calendars(mergeCal, sourceCal):
    for component in sourceCal.walk():
        if component.name == "VEVENT":
            mergeCal.add_component(component)
    return mergeCal

# handle alterations for calendar
def alter_calendar(sourceCal, alterations):
    properties = alterations.keys()
    for property in properties:
        for event in sourceCal.walk():
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
    return sourceCal   

# filter for inclusions
def include_filter(calendar, includeFilters):
    filteredCal = Calendar()
    for property in includeFilters:
        if "contains" in property:
            for event in calendar.walk():
                if property["contains"] in event[property]:
                    filteredCal.add_component(event)
        if "regex" in property:
            for event in calendar.walk():
                if re.search(property["regex"], event[property]):
                    filteredCal.add_component(event)
        if "equals" in property:
            for event in calendar.walk():
                if event[property] == property["equals"]:
                    filteredCal.add_component(event)
    return filteredCal
    