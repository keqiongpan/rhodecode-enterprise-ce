Polymer({
    is: 'rhodecode-favicon',
    properties: {
        favicon: Object,
        counter: {
            type: Number,
            observer: '_handleCounter'
        }
    },

    ready: function () {
        this.favicon = new Favico({
            type: 'rectangle',
            animation: 'none'
        });
    },
    _handleCounter: function (newVal, oldVal) {
        this.favicon.badge(this.counter);
    }
});
