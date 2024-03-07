const tuiCal = tui.Calendar;
var tuiOptions = {
    usageStatistics: false,
    isReadOnly: true,
    defaultView: 'month',
    week: {
        taskView: false
    }
}
const tuiContainer = document.getElementById('tuiCalendar');
const tuiCalendar = new tuiCal(tuiContainer, tuiOptions);

var urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('view')) {
    var view = urlParams.get('view');
    tuiOptions.defaultView = view;
    tuiCalendar.changeView(view, true);
}
if (urlParams.has('dwell')) {
    var autoViews = urlParams.get('autoViews') ? urlParams.get('autoViews') : 'day-month-week';
    var dwellTime = urlParams.get("dwell");
    dwellTime = parseInt(dwellTime) * 1000; // Convert dwellTime from seconds to milliseconds

    var views = autoViews.split("-");
    var currentViewIndex = 0;

    var changeView = function (){
        tuiCalendar.changeView(views[currentViewIndex], true);
        currentViewIndex = (currentViewIndex + 1) % views.length;

    }

    setInterval(changeView, dwellTime);
}

if (urlParams.has('displayMode')) {
    var displayMode = urlParams.get('displayMode');
    if (displayMode == 'kiosk') {
        noKioskElements = document.getElementsByClassName('noKiosk');
        for (var i = 0; i < noKioskElements.length; i++) {
            noKioskElements[i].style.display = "none";
        }
    }
}

tuiCalendar.setOptions(tuiOptions);

var changeCalendarPeriod = function (direction) {
    if (direction == 'previous') {
        tuiCalendar.prev();
    }
    else if (direction == 'next') {
        tuiCalendar.next();
    }
}

var changeCalendarView = function (view, targetButton) {
    tuiCalendar.changeView(view, true);
    var buttons = document.getElementsByClassName('calendarActionChangeViewIsActive');
    for (var i = 0; i < buttons.length; i++) {
        buttons[i].classList.remove('calendarActionChangeViewIsActive');
    }
    targetButton = document.getElementById(targetButton);
    targetButton.classList.add('calendarActionChangeViewIsActive');
}
var loadCalendarEvents = function (calendarId, context) {
    var calendarString = context == "None" ? calendarId : `${context}/${calendarId}`;
    var url = '/api/web-cal/get/' + calendarString;
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function () {
        if (request.status >= 200 && request.status < 400) {
            var data = JSON.parse(request.responseText);
            tuiCalendar.clear();
            tuiCalendar.createEvents(data);
            clearLoaders();
        }
        else {
            if (devMode) {
                tuiCalendar.createEvents(devModeEvents);
            } else {
                errorHandler(request.responseText, request.status);
            }
        }
    }
    request.onerror = function () {
        console.log('Error: ' + request.status);
    }
    request.send();

}
var clearLoaders = function () {
    var loaders = document.getElementsByClassName('loader');
    for (var i = 0; i < loaders.length; i++) {
        loaders[i].style.display = "none";
    }
    var loading = document.getElementsByClassName('isLoading');
    for (var i = 0; i < loading.length; i++) {
        loading[i].classList.remove('isLoading');
    }
}

var errorHandler = function (message, status) {
    if (!devModeBlockDialog) {
        console.log('Error: ' + message + ' ' + status);
        errorText = document.getElementById("errorText");
        errorText.textContent = message;
        errorDialog = document.getElementById('errorDialog');
        errorDialog.showModal();
    }
}

if (devMode) {
    clearLoaders();
    var devModeBlockDialog = true;
    var devModeEvents = [
        {
            id: '1',
            calendarId: 'cal1',
            title: 'Event 1',
            isAllDay: false,
            start: new Date('2024-02-07'),
            end: new Date('2024-02-07'),
            // The following three colors ignore the color value of cal1.
            color: '#fff',
            backgroundColor: '#f00',
            dragBackgroundColor: '#3c056d',
            // borderColor: '#a73eaf' // '#000' of cal1 is applied because it is commented out.
        },
        {
            id: '2',
            calendarId: 'cal1',
            title: 'Event 3',
            isAllDay: false,
            start: new Date('2024-02-08'),
            end: new Date('2024-02-08'),
            backgroundColor: '#f00',
            // The following three colors ignore the color value of cal1.
            dragBackgroundColor: '#3c056d',
            // borderColor: '#a73eaf' // '#000' of cal1 is applied because it is commented out.
        },
        {
            id: '3',
            calendarId: 'cal1',
            title: 'Event 2',
            isAllDay: false,
            start: new Date('2024-02-07'),
            end: new Date('2024-02-07'),
            // The following three colors ignore the color value of cal1.
            color: '#fff',
            backgroundColor: '#3c056d',
            dragBackgroundColor: '#3c056d',
            // borderColor: '#a73eaf' // '#000' of cal1 is applied because it is commented out.
        }]
}