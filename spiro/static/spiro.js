function bgGet(url) {
    var x=new XMLHttpRequest;
    x.open('GET', url);
    x.send();
}

function toggleLED(value) {
    if(value){
        bgGet('/led/on');
    } else {
        bgGet('/led/off');
    }
}

function updateFocusNumber(value) {
    focusnumber = document.getElementById('focusnumber');
    focusnumber.value = value;
    bgGet('/focus/' + value);
}

function updateFocusSlider(value) {
    focusslider = document.getElementById('focusslider');
    focusslider.value = value;
    bgGet('/focus/' + value);
}

function updateShutter(value) {
    shutterrange = document.getElementById('shutterrange');
    shutternumber = document.getElementById('shutternumber');
    bgGet('/shutter/live/' + value);
    shutterrange.value = value;
    shutternumber.value = value;
}

function calcDiskSpace(){
    disk = document.getElementById('disk');
    delay = document.getElementById('delay');
    delay = parseFloat(delay.value);
    duration = document.getElementById('duration');
    duration = parseFloat(duration.value);
    req = 4 * 4 * duration * 24 * 60 / delay / 1024;
    disk.innerHTML = req.toFixed(1) + " GB";
}

function tryCalibration(){
    calib = document.getElementById('calibration');
    bgGet('/findstart/' + calib.value);
}
