"use strict";


function notifySystem(data) {
    var notification = new Notification(data.message.level + ': ' + data.message.message);
};

function notifyToaster(data){
    var notifications = document.getElementById('notifications');
    notifications.push('toasts',
        {   level: data.message.level,
            message: data.message.message
        });
    notifications.open();
}

function handleNotifications(data) {
    if (!templateContext.rhodecode_user.notification_status && !data.message.force) {
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
