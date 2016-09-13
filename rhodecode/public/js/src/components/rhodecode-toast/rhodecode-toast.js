Polymer({
    is: 'rhodecode-toast',
    properties: {
        toasts: {
            type: Array,
            value: function(){
                return []
            }
        }
    },
    observers: [
        '_changedToasts(toasts.splices)'
    ],
    _changedToasts: function(newValue, oldValue){
        this.$['p-toast'].notifyResize();
    },
    dismissNotifications: function(){
        this.$['p-toast'].close();
    },
    handleClosed: function(){
        this.splice('toasts', 0);
    },
    open: function(){
        this.$['p-toast'].open();
    },
    handleNotification: function(data){
        if (!templateContext.rhodecode_user.notification_status && !data.message.force) {
            // do not act if notifications are disabled
            return
        }
        this.push('toasts',{
            level: data.message.level,
            message: data.message.message
        });
        this.open();
    },
    _gettext: _gettext
});
