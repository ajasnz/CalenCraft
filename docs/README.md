# CalenCraft
This Flask application simplifies the process of managing multiple iCalendar (ics) links or calendars by merging them into a single ics link. This consolidated link can then be easily imported or subscribed to.
## Docker
- Construct a Docker image using the provided Dockerfile.
- By default, the application will be accessible on port 8088.
- Establish a volume mapping to `/usr/src/cc/app/config` for your configuration files.

## Usage
1. Create a configuration file
2. Place it in your mapped volume
3. Make a web request to `yourserver.com/configfilename` Do not include `.json` in the request. Remember to include the port if the app is not behind a proxy
4. The CalenCraft will return a combined ics file

## Configuration file
Each calendar configuration is a .json file that tells CalenCraft how to merge and alter your source calendars. Each file should contain a top level dictionary that contains all other configuration.

The first key in your configuration should be `cc_configuration`. This set tells CalenCraft about settings that apply to the configuration file and is mandatory.
`cc_configuration` should contain the following key-value pairs:
- `key`: This key prevents unauthorised modification of the configuration file via the web interface (not required if `allowWeb` is set to `"false"`) [Future version]
- `allowWeb`: This controls whether the configuration file can be managed via the web interface, allowed values are `"true"` or `"false"` [Future version]
- `version`: This is the version of the configuration schema and is present for future-proofing in case the schema changes. This should be set to `1.0`

Each source calendar you want to merge should then be provided as a dictionary, with the key set as a name for that source (currently only used for personal reference)
- `sourceCalendarName`: Used for personal reference, this is the top level key and can be set to any value
    - `source`: The source URL of the calendar you want to merge
    - `datestamp`: Including this set will allow you to add a datestamp to each calendar event, this will be set to the server time that the event was processed and is useful for identifying when the event was last fetched
        - `format`: The date/time format for the datestamp in strftime format e.g. `%Y-%m-%d %H:%M:%S`
        - `template`: The datestamp string you want shown, add `[[date]]` where you want the current date/time inserted
        - `position`: Where the datestamp should be inserted (in the description). Permitted values are `append` (default) or `prepend`
    - `alter`: This allows you to modify the properties of all events in the source calendar, this should be a dictionary containing a sub-dictionary for each property you want to modify. You may specify multiple alterations on one property
        - `*property name*`: The name of the property you want to modify, currently accepted values are `summary`, `description`, `location`, or `availability`. If altering availability see additional requirements and properties below.
            - `prepend`: A string to prepend to the selected property
            - `append`: A string to append to the selected property
            - `replace`: Replace the entire property with the value specified (the value may be left blank to redact that property)
            - `partReplace`: Replace a substring of the property with another string, this should be a dictionary with the following keys
                - `search`: The value to replace 
                - `replace`: The value to replace the search with
    - `include` and `exclude`: These allow filtering of which events to include, an include filter will only include events that meet the specified critera, while an exclude filter will remove events that meet the criteria. Both filters currently only apply an **OR** logic. This dictionary should contain a sub-dictionary for each property you want to use as a filter
        - `property name`: The name of the property you want to check for filters, currently accepted values are `summary`, `description`, and `location`
            - `contains`: Check if the property contains the specified string
            - `equals`: Check if the property equals the specified string
            - `regex`: Check the property value against the specified regex
    - `alterRules`: Allows for more complex alterations on a per-event basis. This should contain multiple sub-dictionaries with each criteria you want to match for to alter
        - `property`: The property you want to match, currently accepted values are `summary`, `description`, and `location`
        - `matchType`: How you want to match against the property, currently accepted values are `contains`, `equals`, and `regex`
        - `matchPattern`: The pattern or string to match against
        - `alter`: The alterations to make to the events that meet the criteria above. This should use the same syntax as the `alter` configurations above

### Availability configuration
Availability takes a dictionary with the following keys, each key is optional:
- `transp`: The transparency of the event, currently accepted values are `transparent` and `opaque`. This determines whether the vent will be considered in free/busy calculations by the client
- `fbtype`: The type of free/busy information to provide, currently accepted values are `free`, `busy`, `busy-unavailable`, and `busy-tentative`. This will also set Microsoft's proprietary fields.


### Full sample config (all parameters)
<pre><code>{
    {
    "cc_configuration": {
         "key": "value",
         "allowWeb": "true",
         "version": "1.0"
     },
    "ics1name": {
        "source":"",
        "datestamp": {
            "format": "%Y-%m-%d %H:%M:%S",
            "template": "Event last updated: [[date]]",
            "position": "prepend"
        },
        "alter": {
            "summary":{
                "prepend": "",
                "append": "",
                "replace": "",
                "partReplace": {
                    "search": "",
                    "replace": ""
                }
            },
            "description":{
                "prepend": "",
                "append": "",
                "replace": "",
                "partReplace": {
                    "search": "",
                    "replace": ""
                }
            },
            "location":{
                "prepend": "",
                "append": "",
                "replace": "",
                "partReplace": {
                    "search": "",
                    "replace": ""
                }
            },
            "availability":{
                "transp": "",
                "fbtype": ""
            }
        },
        "include": {
            "summary": {
                "contains": "",
                "equals": "",
                "regex": ""
            },
            "description": {
               "contains": "",
               "equals": "",
               "regex": ""
            },
            "location": {
               "contains": "",
               "equals": "",
               "regex": ""
            }
        },
        "exclude": {
            "summary": {
                "contains": "",
                "equals": "",
                "regex": ""
            },
            "description": {
               "contains": "",
               "equals": "",
               "regex": ""
            },
            "location": {
               "contains": "",
               "equals": "",
               "regex": ""
            }
        },
        "alterRules": [
            {
                "property": "",
                "matchType": "",
                "matchPattern": "",
                "alter": {
                    "summary":{
                        "prepend": "",
                        "append": "",
                        "replace": "",
                        "partReplace": {
                            "search": "",
                            "replace": ""
                        }
                    },
                    "description":{
                        "prepend": "",
                        "append": "",
                        "replace": "",
                        "partReplace": {
                            "search": "",
                            "replace": ""
                        }
                    },
                    "location":{
                        "prepend": "",
                        "append": "",
                        "replace": "",
                        "partReplace": {
                            "search": "",
                            "replace": ""
                        }
                    }
                }
            }
        ]  
    }
}
}</code></pre>

# Other funtionality

## Web interface: Under Development
**~~The web interface is a very basic implementation with little to no security or sanitization. It should be used with care. By default it is disabled, if you understand the risks change the `enableweb` variable at the top of server.py before building the docker image.~~**
~~CalenCraft contains a basic web interface which allows adding and updating a configuration file without access the volume, this is available at `yourserver.com/manage/upload`. You must specify the name of the configuration (filename) and the key in the file. If you are replacing an existing file the key must match both the old and new files.~~

# Notes
- CalenCraft does not currently vaildate configuration files, if you get it wrong the program may behave unexpectedly.


# Roadmap
- [x] Combine multiple ics files into one
- [x] Alter core event properties
- [x] Filter events
- [x] Add datestamp to events
- [ ] Add caching
- [x] Allow altering transparancy
- [x] Allow altering free/busy type
- [ ] Allow adding/updating config files via web
- [ ] Add an ICS viewer
- [x] Add ability to specify alter rules on a per-event basis
- [ ] Add env variables for configuration
- [ ] Better (or any) error handling
- [x] Allow partial replaces in alter
- [ ] Configuration generator
- [ ] Improved web interface and security

