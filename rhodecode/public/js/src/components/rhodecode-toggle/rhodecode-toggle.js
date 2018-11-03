import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '@polymer/paper-toggle-button/paper-toggle-button.js';
import '@polymer/paper-spinner/paper-spinner.js';
import '@polymer/paper-tooltip/paper-tooltip.js';

export class RhodecodeToggle extends PolymerElement {

    static get is() {
        return 'rhodecode-toggle';
    }

    static get template() {
        return html`
        <style include="shared-styles">
            .rc-toggle {
                float: left;
                position: relative;
            }
    
            .rc-toggle paper-spinner {
                position: absolute;
                top: 0;
                left: -30px;
                width: 20px;
                height: 20px;
            }
        </style>
        <div class="rc-toggle">
            <paper-toggle-button checked={{checked}}>[[labelStatus(checked)]]
            </paper-toggle-button>
            <paper-tooltip>[[tooltipText]]</paper-tooltip>
            <template is="dom-if" if="[[shouldShow(noSpinner)]]">
                <paper-spinner active=[[active]]></paper-spinner>
            </template>
        </div>
    `;
    }

    static get properties() {
        return {
            noSpinner: {type: Boolean, value: false, reflectToAttribute: true},
            tooltipText: {type: String, value: "Click to toggle", reflectToAttribute: true},
            checked: {type: Boolean, value: false, reflectToAttribute: true},
            active: {type: Boolean, value: false, reflectToAttribute: true, notify: true}
        }
    }

    shouldShow() {
        return !this.noSpinner
    }

    labelStatus(isActive) {
        return this.checked ? 'Enabled' : "Disabled"
    }
}

customElements.define(RhodecodeToggle.is, RhodecodeToggle);
