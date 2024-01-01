# This will contain information
*Eventually...*

## Some things don't work yet...
### Like:
- Include filters
- Exclude filters

## And some things are not tested...
### Like:
- Everything

# In the mean time:
This script will combine multiple ics feeds into one feed.

## Docker
- Build an docker image from the Dockerfile. 
- It will run on port 8088 by default. 
- Map a volume to `/usr/src/cc/app/config` containing your configuration files.

## Usage
1. Create a configuration file
2. Place it in `/config/`
3. Make a web request to `yourserver.com/configfilename` Do not include `.json`
4. The script will return a combined ics file

## Configuration file
> ***IMPORTANT:*** The use of an include or exclude filter will currently break everything. This will (hopefully) be fixed in the future


There is a sample configuration file in the `docs` folder. The completed configuration file should be saved in `/config/` as a `.json` file. The fields are as follows:
Items marked with a `*` are required.
- `name`*: The name of the calendar (currently only for your reference)
- `source`*: The URL of an origin ics file
- `alter`: A JSON set containing the following fields, used to alter the calender events before merging
    - `summary/description/location`: The property to alter. Only use one per set, you can repeat the set to alter multiple properties
        - `replace`: A string to replace the property with
        - `prepend`: A string to prepend to the property
        - `append`: A string to append to the property
- `include`: A JSON set containing the following fields, used to filter events. Only events meeting the filter will be included
    - `summary/description/location`: The property to filter. Only use one per set, you can repeat the set to filter multiple properties
        - `contains`: A string to check if it is contained in the property
        - `equals`: A string to check if the property is equal to
        - `regex`: A regex string to check for in the property
- `exclude`: A JSON set containing the following fields, used to filter events. Events meeting the criteria will be excluded (if an include and exclude exists then exclude will take precedence)
    - `summary/description/location`: The property to filter. Only use one per set, you can repeat the set to filter multiple properties
        - `contains`: A string to check if it is contained in the property
        - `equals`: A string to check if the property is equal to
        - `regex`: A regex string to check for in the property
- `datestamp`: If this set exists a datestamp can be added to each event's description (useful for including a last updated time)
    - `dateformat`*: The format of the datestamp e.g. "%Y-%m-%d %H:%M:%S"
    - `stamptemplate`*: The template for the datestamp e.g. "Last updated: [[date]]" (the date will be inserted into the template where [[date]] is)
    - `position`: Where to insert the datestamp. Can be `prepend` or `append`. If not specified it will be appended

Repeat this JSON set for as many calenders as you want to combine.
### example config
[
    {
        "name": "My Calendar",
        "source": "https://example.com/sourcecal.ics",
        "alter": {
            "summary": {
                "prepend": "[Personal Event] "
            },
            "description": {
                "replace": ""
            },
            "location": {
                "replace": ""
            }
        },
        "datestamp": {
            "dateformat": "%Y-%m-%d %H:%M:%S",
            "stamptemplate": "Event last fetched from origin: [[date]]",
            "stampposition": "prepend"
        }
    },
    {
        "name": "Work Calendar",
        "source": "https://example.com/workcal.ics",
        "alter": {
            "summary": {
                "prepend": "[WORK EVENT]"
            }
        },
        "exclude":{
            "summary": {
                "contains": "meeting",
                "regex": "",
                "equals": ""
            },
            "location": {
                "contains": "office"
            }
        },
        "datestamp": {
            "dateformat": "%Y-%m-%d %H:%M:%S",
            "stamptemplate": "Event last fetched from origin: [[date]]",
            "stampposition": "prepend"
        }
    }
]

# Roadmap
- [x] Combine multiple ics files into one
- [x] Alter core event properties
- [_] Filter events
- [x] Add datestamp to events
- [_] Add caching
- [_] Allow altering transparancy
- [_] Allow adding/updating config files via web
- [_] Add an ICS viewer

