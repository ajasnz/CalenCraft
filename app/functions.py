# FIXME check alter rule contains
import json, requests
from icalendar import Calendar, Event
import regex as re
from sanitize_filename import sanitize
import datetime
import os, time, shelve
import recurring_ical_events as rie

cacheDir = "./app/cache/"
configDir = "./app/config/"


# main handler
def start_build(calId, context=None, **kwargs):
    calFileName = sanitize(calId) + ".json"
    try:
        with open("./app/config/" + calFileName) as f:
            baseConfig = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("This calendar does not exist ref=sblc")

    mergeCal = Calendar()
    mergeCal.add("prodid", "-//CalenCraft//")
    mergeCal.add("version", "2.0")

    for name, calConfig in baseConfig.items():
        if name != "cc_configuration":
            sourceCal = fetch_origin(calConfig["source"])
            if "datestamp" in calConfig:
                dateStamp = str(calConfig["datestamp"]["template"]).replace(
                    "[[date]]",
                    datetime.datetime.now().strftime(calConfig["datestamp"]["format"]),
                )
            else:
                dateStamp = None
            for event in sourceCal.walk():
                if event.name != "VEVENT":
                    continue
                if "include" in calConfig or "exclude" in calConfig:
                    event = filter_event(
                        event,
                        includes=calConfig.get("include", False),
                        excludes=calConfig.get("exclude", False),
                        context=context,
                    )
                if event is None:
                    continue
                if "alter" in calConfig:
                    event = alter_event(event, calConfig["alter"])
                if "alterRules" in calConfig:
                    for ruleSet in calConfig["alterRules"]:
                        process_alter_rule(event, ruleSet, context)
                if dateStamp != None:
                    if calConfig["datestamp"]["position"] == "prepend":
                        event["description"] = (
                            dateStamp + "\n\n" + event.get("description", "")
                        )
                    else:
                        event["description"] = (
                            event.get("description", "") + "\n\n" + dateStamp
                        )
                currentDate = datetime.datetime.now()
                recurringStart = currentDate - datetime.timedelta(days=10)
                recurringEnd = currentDate + datetime.timedelta(days=365)
                expandedEvents = rie.of(event).between(recurringStart, recurringEnd)
                for thisEvent in expandedEvents:
                    mergeCal.add_component(thisEvent)
                # mergeCal.add_component(event)

    if "format" in kwargs and kwargs["format"] == "tui":
        return format_tui(mergeCal, "calendar")
    else:
        return mergeCal.to_ical()


# get the origin calendar
def fetch_origin(source):
    sourceCalContent = requests.get(source).text
    sourceCal = Calendar.from_ical(sourceCalContent)
    return sourceCal


# handle alterations for a single event
def alter_event(event, alterations):
    for property, alteration in alterations.items():
        value = event.get(property, "")
        if "replace" in alteration:
            event[property] = value = alteration["replace"]
        if "partReplace" in alteration:
            event[property] = value = value.replace(
                alteration["partReplace"]["search"],
                alteration["partReplace"]["replace"],
            )
        if "prepend" in alteration:
            event[property] = value = alteration["prepend"] + value
        if "append" in alteration:
            event[property] = value = value + alteration["append"]

        if property == "availability":
            if "transp" in alteration:
                event["transp"] = str(alteration["transp"]).upper()
            if "fbtype" in alteration:
                event["fbtype"] = str(alteration["fbtype"]).upper()
                event["x-microsoft-cdo-intendedstatus"] = alteration["fbtype"]
    return event


# handle includes and excludes for a single event
def filter_event(event, **kwargs):
    doIncludeEvent = False

    def check_property(event, property, conditions):
        for condition, value in conditions.items():
            if condition == "contains" and event.get(property, None) is not None:
                if isinstance(value, str) and value in event.get(property):
                    return True
                if isinstance(value, list) and any(
                    item in event.get(property) for item in value
                ):
                    return True
            elif condition == "regex":
                if isinstance(value, str) and re.search(value, event.get(property)):
                    return True
                if isinstance(value, list) and any(
                    re.search(regex, event.get(property)) for regex in value
                ):
                    return True
            elif condition == "equals":
                if isinstance(value, str) and event.get(property) == value:
                    return True
                if isinstance(value, list) and any(
                    event.get(property) == item for item in value
                ):
                    return True
        return False

    includes = kwargs.get("includes", {})
    excludes = kwargs.get("excludes", {})

    for property, conditions in includes.items():
        if check_property(event, property, conditions):
            doIncludeEvent = True

    for property, conditions in excludes.items():
        if check_property(event, property, conditions):
            doIncludeEvent = False

    return event if doIncludeEvent else None


def process_alter_rule(event, ruleset, context):
    if ruleset.get("context", None) is not None and (
        ruleset["context"] != context and ruleset["context"] != "*"
    ):
        return

    property = ruleset.get("property")

    if property in event or property == "all":
        matchType = ruleset.get("matchType")
        matchPattern = ruleset.get("matchPattern")

        if matchType == "contains" and matchPattern in event.get(property):
            alter_event(event, ruleset["alter"])
        elif matchType == "equals" and matchPattern == event.get(property):
            alter_event(event, ruleset["alter"])
        elif matchType == "regex" and re.search(matchPattern, event.get(property)):
            alter_event(event, ruleset["alter"])
        elif property == "all":
            alter_event(event, ruleset["alter"])


def cache_ics(calId, context=None):
    cacheFile = (
        cacheDir + context + calId + ".ics" if context else cacheDir + calId + ".ics"
    )
    icsContents = start_build(calId, context)
    with shelve.open(cacheFile) as cache:
        cache["icsContents"] = icsContents
        cache["lastUpdated"] = time.time()


def get_cached_ics(calId, cacheTime, context=None, age=0):
    if age > 2:
        raise FileNotFoundError("Caught in cache loop ref=gcicl")
    cacheFile = (
        cacheDir + context + calId + ".ics" if context else cacheDir + calId + ".ics"
    )
    with shelve.open(cacheFile) as cache:
        if "icsContents" in cache and "lastUpdated" in cache:
            if time.time() - cache["lastUpdated"] < cacheTime:
                return cache["icsContents"]
            else:
                cache_ics(calId, context)
                return get_cached_ics(calId, cacheTime, context, age + 1)
        else:
            cache_ics(calId, context)
            return get_cached_ics(calId, cacheTime, context, age + 1)


def get_ics(calId, context=None, **kwargs):
    try:
        with open(configDir + calId + ".json") as f:
            baseConfig = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("This calendar does not exist ref=gilc")

    defaultContext = baseConfig["cc_configuration"].get("defaultContext", None)
    allowNoContext = baseConfig["cc_configuration"].get("allowNoContext", None)
    allowContexts = baseConfig["cc_configuration"].get("allowContext", None)
    allowedContexts = baseConfig["cc_configuration"].get("allowedContexts", None)

    if context is None:
        if defaultContext is not None:
            context = defaultContext
        elif allowNoContext is False:
            raise FileNotFoundError("This calendar view does not exist ref=gicnc")
    else:
        if allowedContexts is not None and context not in allowedContexts:
            raise FileNotFoundError("This calendar view does not exist ref=gicac")

    format = kwargs.get("format", "ics")

    if format == "tui":
        allowWeb = baseConfig["cc_configuration"].get("allowWeb", False)
        if allowWeb is False:
            raise FileNotFoundError("You cannot view this calendar online ref=givc")

    if context is not None and allowContexts != "true":
        raise FileNotFoundError("This calendar is not available ref=gicnac")

    cacheTime = baseConfig["cc_configuration"].get("cache", None)
    if cacheTime and cacheTime > 0 and os.getenv("CC_ENABLE_CACHING"):
        icsContents = get_cached_ics(calId, cacheTime, context)
        if format == "tui":
            icsContents = format_tui(icsContents, "ics")
    else:
        icsContents = start_build(calId, context, **kwargs)

    return icsContents


def format_tui(eventData, format):
    if format == "ics":
        eventData = Calendar.from_ical(eventData)

    tuiData = []

    for component in eventData.walk():
        if component.name == "VEVENT":
            event = {
                "id": str(component.get("uid")),
                "title": str(component.get("summary")),
                "start": component.get("dtstart").dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": component.get("dtend").dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "transp": component.get("transp", "OPAQUE"),
            }
            tuiData.append(event)

    return json.dumps(tuiData)
