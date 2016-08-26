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
    ready: function(){

    },

    _changedToasts: function(newValue, oldValue){
        this.$['p-toast'].notifyResize();
    },
    dismissNotifications: function(){
        this.$['p-toast'].close();
        this.splice('toasts', 0);
    },
    open: function(){
        this.$['p-toast'].open();
    },
    _gettext: _gettext
});
