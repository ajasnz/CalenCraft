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
        #FIXME Include and Exclude filters currently break everything, strip these from any config
        if True:
            if "include" in calConfig:
                del calConfig["include"]
            if "exclude" in calConfig:
                del calConfig["exclude"]
        sourceCal = fetch_origin(calConfig["source"])
        if "datestamp" in calConfig:
            currentTime = datetime.datetime.now().strftime(
                calConfig["datestamp"]["dateformat"]
            )
            dateStamp = str(calConfig["datestamp"]["stamptemplate"]).replace(
                "[[date]]", currentTime
            )

            if "alter" not in calConfig:
                calConfig["alter"] = {}
            if "description" not in calConfig["alter"]:
                calConfig["alter"]["description"] = {}
            if calConfig["datestamp"]["stampposition"] == "prepend":
                if "prepend" not in calConfig["alter"]["description"]:
                    calConfig["alter"]["description"]["prepend"] = ""
                calConfig["alter"]["description"]["prepend"] = (
                    dateStamp + calConfig["alter"]["description"]["prepend"]
                )
            elif (
                calConfig["datestamp"]["stampposition"] == "append" or True
            ):  # make this the default position
                if "append" not in calConfig["alter"]["description"]:
                    calConfig["alter"]["description"]["append"] = ""
                calConfig["alter"]["description"]["append"] = (
                    calConfig["alter"]["description"]["append"] + dateStamp
                )

        if "include" in calConfig or "exclude" in calConfig:
            sourceCal = filter_calendar(
                sourceCal,
                includes=calConfig.get("include", None),
                excludes=calConfig.get("exclude", None),
                alterations=calConfig.get("alter", None),
            )  # To prevent double handling of alterations, we pass the alterations to the include filter
        elif (
            "alter" in calConfig
            and "include" not in calConfig
            and "exclude" not in calConfig
        ):  # if there is an include filter, events are altered at inclusion, so we don't want to do it again
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


# filters
def filter_calendar(calendar, **kwargs):
    filteredCal = Calendar()
    for event in calendar.walk():
        filteredEvent = filter_event(event, **kwargs)
        if filteredEvent is not None:
            filteredCal.add_component(filteredEvent)


def filter_event(event, **kwargs):
    doIncludeEvent = False
    try:
        if "includes" in kwargs and kwargs["includes"] is not None:
            includes = kwargs["includes"]
            for property in includes:
                if "contains" in includes[property]:
                    print(includes[property]["contains"] in event[property])
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
        if "excludes" in kwargs and kwargs["excludes"] is not None:
            excludes = kwargs["excludes"]
            for property in excludes:
                if "contains" in excludes[property]:
                    if excludes[property]["contains"] in event[property]:
                        doIncludeEvent = False
                        break
                if "regex" in excludes[property]:
                    if re.search(excludes[property]["regex"], event[property]):
                        doIncludeEvent = False
                        break
                if "equals" in excludes[property]:
                    if event[property] == excludes[property]["equals"]:
                        doIncludeEvent = False
                        break
    except KeyError:
        pass
    if doIncludeEvent:
        if "alterations" in kwargs and kwargs["alterations"] is not None:
            event = alter_event(event, kwargs["alterations"])
        return event
    else:
        return None
