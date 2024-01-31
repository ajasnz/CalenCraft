const tuiCal = tui.Calendar;
const tuiOptions = {
    usageStatistics: false,
    isReadOnly: true,
    defaultView: 'month',
    week: {
        taskView: false
    }
}
const tuiContainer = document.getElementById('tuiCalendar');
const tuiCalendar = new tuiCal(tuiContainer, tuiOptions);
tuiCalendar.setOptions(tuiOptions);

var changeCalendarPeriod = function(direction){
    if (direction == 'previous'){
        tuiCalendar.prev();
    }
    else if (direction == 'next'){
        tuiCalendar.next();
    }
}

var changeCalendarView = function(view, targetButton){
    tuiCalendar.changeView(view, true);
    var buttons = document.getElementsByClassName('calendarActionChangeViewIsActive');
    for (var i = 0; i < buttons.length; i++){
        buttons[i].classList.remove('calendarActionChangeViewIsActive');
    }
    targetButton = document.getElementById(targetButton);
    targetButton.classList.add('calendarActionChangeViewIsActive');
}
var loadCalendarEvents = function(calendarId, context){
    var calendarString = context == "None" ? calendarId : `${context}/${calendarId}`;
    var url = '/api/web-cal/get/' + calendarString;
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onload = function(){
        if (request.status >= 200 && request.status < 400){
            var data = JSON.parse(request.responseText);
            tuiCalendar.clear();
            tuiCalendar.createEvents(data);
            clearLoaders();
        }
        else{
            errorHandler(request.responseText, request.status);
        }
    }
    request.onerror = function(){
        console.log('Error: ' + request.status);
    }
    request.send();
    
}
var clearLoaders = function(){
    var loaders = document.getElementsByClassName('loader');
    for (var i = 0; i < loaders.length; i++){
        loaders[i].style.display="none";
    }
    var loading = document.getElementsByClassName('isLoading');
    for (var i = 0; i < loading.length; i++){
        loading[i].classList.remove('isLoading');
    }
}

var errorHandler = function(message, status){
    console.log('Error: ' + message + ' ' + status);
    errorText = document.getElementById("errorText");
    errorText.textContent=message;
    errorDialog = document.getElementById('errorDialog');
    errorDialog.showModal();
}
