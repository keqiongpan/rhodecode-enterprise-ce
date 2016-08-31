Polymer({
  is: 'rhodecode-toggle',
  properties: {
    noSpinner: { type: Boolean, value: false, reflectToAttribute:true},
    tooltipText: { type: String, value: "Click to toggle", reflectToAttribute:true},
    checked: { type:  Boolean, value: false, reflectToAttribute:true},
    active: { type: Boolean, value: false, reflectToAttribute:true, notify:true}
  },
  shouldShow: function(){
    return !this.noSpinner
  },
  labelStatus: function(isActive){
    return this.checked? 'Enabled' : "Disabled"
  }
  
});