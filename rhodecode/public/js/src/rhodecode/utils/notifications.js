"use strict";

toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": false,
    "progressBar": false,
    "positionClass": "toast-top-center",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": "300",
    "hideDuration": "300",
    "timeOut": "0",
    "extendedTimeOut": "0",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

function notifySystem(data) {
    var notification = new Notification(data.message.level + ': ' + data.message.message);
};

function notifyToaster(data){
    toastr[data.message.level](data.message.message);
}

function handleNotifications(data) {

    if (!templateContext.rhodecode_user.notification_status && !data.testMessage) {
        // do not act if notifications are disabled
        return
    }
    // use only js notifications for now
    var onlyJS = true;
    if (!("Notification" in window) || onlyJS) {
        // use legacy notificartion
        notifyToaster(data);
    }
    else {
        // Let's check whether notification permissions have already been granted
        if (Notification.permission === "granted") {
            notifySystem(data);
        }
        // Otherwise, we need to ask the user for permission
        else if (Notification.permission !== 'denied') {
            Notification.requestPermission(function (permission) {
                if (permission === "granted") {
                    notifySystem(data);
                }
            });
        }
        else{
            notifyToaster(data);
        }
    }
};

$.Topic('/notifications').subscribe(handleNotifications);
