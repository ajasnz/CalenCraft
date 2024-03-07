# CalenCraft
CalenCraft is a basic flask application that can merge multiple ics links into one, creating a single consolidated calendar.

## Features
- Combine multiple ics files into one subscribable link
- Filters to include or exclude events based on keywords or regex
- Ability to alter event properties before combining files
- Ability to specify contexts for different views of the same calendar
- Web based calendar viewer

## Setup

### Docker
- Install the dependencies listed in `requirements.txt`
- Build a Docker image using the provided Dockerfile.
- Create a volume mapping to `/usr/src/cc/app/config` for your configuration files.

By default, the application will be accessible on port 8088.

#### Global configuration
Some configuration options can be set globally via environment variables, these are:
- `cc_enable_non_ics_path`: Whether to allow calendars to be accessed at https://example.com/calendar if this is set to true, calendars will be accessible at https://example.com/calendar. This should be set to `true` or `false` and defaults to `false`. This is included for backwards compatibility with previous versions, enabling this may cause issues if a calendar config shares it's name with a defined path.
- `cc_enable_caching`: Whether to enable caching of the combined ics file. This should be set to `true` or `false` and defaults to `false`


## Usage
1. Create a configuration file
2. Place it in your mapped volume
3. Make a web request to `yourserver.com/ics/configfilename` Do not include `.json` in the request. Remember to include the port if the app is not behind a proxy
4. The CalenCraft will return a combined ics file


### Configuration file
Each calendar configuration is a .json file that tells CalenCraft how to merge and alter your source calendars. Each file should contain a top level dictionary that contains all other configuration.

#### Merge configuration
The first key in your configuration should be `cc_configuration`. This set tells CalenCraft about settings that apply to the configuration file and is mandatory.
`cc_configuration` should contain the following key-value pairs:
- `cache`: The number of minutes to cache the combined ics file for, this is optional and defaults to `0` (no caching). This speeds up the response time for clients but may cause issues if your source calendars are updated frequently.
- `allowContext`: Whether to allow context-specific configuration files to be used. This should be set to `true` or `false` and defaults to `false`. Setting to false will disable all contexts and a request to a context will fail.
- `allowNoContext`: Whether to allow requests without a context to be processed. This should be set to `true` or `false` and defaults to `false`. If set to `false` requests without a context will fail.
- `defaultContext`: The name of the context to use if no context is specified in the request. The context specified here will be used for all requests without a context if `allowNoContext` is set to `false`
- `allowedContexts`: A list of contexts that are allowed to be used. If anoter context is specified in the request and `allowNoContext` is set to `false` and `defaultContext` is not specified the request will fail.
- `allowWeb`: Whether to allow the ICS to be viewed online via the web interface. This should be set to `true` or `false` and defaults to `false`. If set to `true` the calendar will be available at `yourserver.com/view/calendar`
<pre><code>
    "cc_configuration": {
        "cache": int,
        "cacheSource": int,
        "allowContext": bool,
        "allowNoContext": bool,
        "defaultContext": "str",
        "allowedContexts": ["str", "str2", "str3"],
        "allowWeb": bool
    }
</code></pre>

#### Source configuration
Each source calendar you want to merge should then be provided as a dictionary, with the key set as a name for that source (currently only used for personal reference)
- `source`: Each source must have a URL specified for the calendar you want to merge
<pre><code>
"ics1name": {
    "source": "https://example.com/ics1.ics"
}
</code></pre>

##### Datestamp
You can add a datestamp to each event, this will be set to the server time that the event was processed and is useful for identifying when the event was last fetched, this is done by adding a `datestamp` dictionary to the source calendar.
- `format`: The date/time format for the datestamp in strftime format e.g. `%Y-%m-%d %H:%M:%S`
- `template`: The datestamp string you want shown, add `[[date]]` where you want the current date/time inserted
- `position`: Where the datestamp should be inserted (in the description). Permitted values are `append` (default) or `prepend`
<pre><code>
"datestamp": {
    "format": "%Y-%m-%d %H:%M:%S",
    "template": "Event last updated: [[date]]",
    "position": "prepend"
}
</code></pre>

##### Altering events
You can alter the properties of each event before they are merged, this is done by adding an `alter` dictionary to the source calendar. This should contain a sub-dictionary for each property you want to alter.
- `alter`: This allows you to modify the properties of all events in the source calendar, this should be a dictionary containing a sub-dictionary for each property you want to modify. You may specify multiple alterations on one property
    - `property name`: The name of the property you want to modify, currently accepted values are `summary`, `description`, `location`, or `availability`. If altering availability see additional requirements and properties below. NB: This is the KEY of the sub-dictionary, not a property within the sub-dictionary
        - `prepend`: A string to prepend to the selected property
        - `append`: A string to append to the selected property
        - `replace`: Replace the entire property with the value specified (the value may be left blank to redact that property)
        - `partReplace`: Replace a substring of the property with another string, this should be a dictionary with the following keys
            - `search`: The value to replace 
            - `replace`: The value to replace the search with
<pre><code>
"alter": {
    "Property Name":{
        "prepend": "",
        "append": "",
        "replace": "",
        "partReplace": {
            "search": "",
            "replace": ""
        }
    }
}
</code></pre>

###### Availability
If altering availability, set the property name to `availability` and include a dictionary with the following keys, both keys are optional depending on your requirements:
- `transp`: The transparency of the event, currently accepted values are `transparent` and `opaque`. This determines whether the vent will be considered in free/busy calculations by the client
- `fbtype`: The type of free/busy information to provide, currently accepted values are `free`, `busy`, `busy-unavailable`, and `busy-tentative`. This will also set Microsoft's proprietary fields.
**NB: Other alter attributes are not supported within the `availability` dictionary**

<pre><code>
"availability":{
    "transp": "",
    "fbtype": ""
}
</code></pre>

##### Filtering events
You can filter events before they are merged, this is done by adding an `filter` dictionary to the source calendar. This should contain a sub-dictionary for each property you want to filter on, the dictionary should be named either `exclude` or `include`.
- `include` or `exclude`: These allow filtering of which events to include, an include filter will only include events that meet the specified critera, while an exclude filter will remove events that meet the criteria. Both filters currently only apply an **OR** logic for filters of the same type. Ecludes will take priority over Includes. This dictionary should contain a sub-dictionary for each property you want to use as a filter
    - `property name`: The name of the property you want to check for filters, currently accepted values are `summary`, `description`, and `location`
        - `contains`: Check if the property contains the specified string
        - `equals`: Check if the property equals the specified string
        - `regex`: Check the property value against the specified regex
<pre><code>
"include": {
    "Property Name": {
        "contains": "",
        "equals": ,
        "regex": ""
    },
}
</code></pre>
For each of these filter types you may specify multiple matching criteria by passing in a list `"contains": ["string1", "string2"]`. For all filters, matching is case sensitive and uses OR logic.
If using contexts, you can specify different rules for each context by passing in a dictionary with the context name, and a list as the property `"contains": {"context1": ["string1", "string2"], "context2": ["string1", "string3"]}`

##### Altering events on a per-event basis
Alterations can be made to an event based on rules and criteria the event must meet, rather than a blanket alteration for all events. This is done by adding an `alterRules` key to the source calendar. the `alterRules` should contain a list which contains a dictionary for each rule you want to apply. Each rule should contain the following keys:
- `alterRules`: Allows for more complex alterations on a per-event basis. This should contain multiple sub-dictionaries with each criteria you want to match for to alter
    - `property`: The property you want to match, currently accepted values are `summary`, `description`, and `location`. You can also set this to `all` to apply rule to all events
    - `matchType`: How you want to match against the property, currently accepted values are `contains`, `equals`, and `regex`
    - `matchPattern`: The pattern or string to match against
    - `alter`: The alterations to make to the events that meet the criteria above. This should use the same syntax as the `alter` configurations above
    - `context`: The name of a context, if set this rule will only apply to a specific context. See below for more information on contexts. Specify `*` to apply to all contexts
<pre><code>
"alterRules": [
    {
        "property": "",
        "matchType": "",
        "matchPattern": "",
        "context": "",
        "alter": {
            
        }
    }
]
</code></pre>

#### Contexts
Contexts allow the use of a single configuration with multiple views depending on who is looking at it (contexts are specified before the calendar id in the url). For example time off may show as busy if viewed from a work context, but free if viewed from a personal context.
Contexts are currently only suupported for the following parts of a configuration: `alterRules`. Support for include and exclude filters will be added in a future version.

## Viewer
CalenCraft contains a basis calendar viewer which can be accessed by swapping `/ics/` in a calendar's URL to `/view/` e.g. `https://yoursever.com/view/calendar`.

### Viewer URL parameters
When using the viewer you can pass parameters in the URL to alter the view of the calendar. These are:
- `view`: The view to use, currently accepted values are `day`, `week`, `month`, and `agenda`. This defaults to `month`.
- `displayMode`: set this to `kiosk` to hide the header and footer of the viewer
- `viewDwell`: A number of seconds. If set the view will cycle through the views specified in the `autoViews` parameter every `viewDwell` seconds
- `autoViews`: A list of views to cycle through if `viewDwell` is set (seperated by `-`)

## Possible URL formats
- `https://example.com/calendar`: This format has been superceded by default, but can be enabked by setting the `cc_enable_non_ics_path` environment variable to `true`. This format does not support contexts, and will be removed in a future version.
- `https://example.com/calendar`: This format has been superceded by default, but can be enabked by setting the `cc_enable_non_ics_path` environment variable to `true`. This format does not support contexts, and will be removed in a future version.
- `https://example.com/ics/calendar`: This format is the default and will work for all configurations
- `https://example.com/ics/context/calendar`: This format will only work if contexts are enabled in the configuration file and the `cc_enable_contexts` environment variable is set to `true`
- `https://example.com/ics/context/calendar`: This format will only work if contexts are enabled in the configuration file and the `cc_enable_contexts` environment variable is set to `true`

## Environment variables
Some configuration options can be set globally via environment variables, these are:
- `CC_ENABLE_NON_ICS_PATH`: Whether to allow calendars to be accessed at https://example.com/calendar if this is set to true, calendars will be accessible at https://example.com/calendar. This should be set to `true` or `false` and defaults to `false`. This is included for backwards compatibility with previous versions, enabling this may cause issues if a calendar config shares it's name with a defined path.
- `CC_ENABLE_CACHING`: Whether to enable caching of the combined ics file. This should be set to `true` or `false` and defaults to `true`
- `CC_BASE_URL`: The base URL for the application, this is used to generate links in the web interface. This should be set to the URL of the application e.g. `https://example.com`

## Caching
CalenCraft currently supports basic caching of the combined ics file ON REQUESTS i.e. it currently only updates each calendar's cache when it is requested rather than on a schedule. This will work on frequently requested calendars with a longer cache time, but will mean little effect on calendars that are rarely requested. This will be improved in a future version.

# Notes & Bugs
- CalenCraft does not currently vaildate configuration files, if you get it wrong the program may behave unexpectedly.
- Recurring events will only include the past 10 days and future 365 days. This will become customisable in the future
- Some all day events do not render correctly


# Roadmap
- [x] Combine multiple ics files into one
- [x] Alter core event properties
- [x] Filter events
- [x] Add datestamp to events
- [x] Add caching
- [x] Allow altering transparancy
- [x] Allow altering free/busy type
- [ ] Allow adding/updating config files via web
- [x] Add an ICS viewer
- [x] Add ability to specify alter rules on a per-event basis
- [x] Add env variables for configuration
- [x] Add env variables for configuration
- [ ] Better (or any) error handling
- [x] Allow partial replaces in alter
- [ ] Configuration generator
- [ ] Improved web interface
- [x] Add ability to specify multiple contexts for a single calendar
- [ ] Add context support for include/exclude
- [ ] Add scheduled cache updates
- [ ] Source calendar caching
- [ ] Event Buffers
- [ ] Show transparency in viewer
- [ ] Allow customising the start and end of recurring events
- [ ] Allow altering event start and end times


