Polymer({
    is: 'rhodecode-unsafe-html',
    properties: {
        text: {
            type: String,
            observer: '_handleText'
        }
    },
    _handleText: function(newVal, oldVal){
        this.innerHTML = this.text;
    }
})
