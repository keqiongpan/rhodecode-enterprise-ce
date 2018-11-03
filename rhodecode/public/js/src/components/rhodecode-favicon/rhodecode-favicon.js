import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';

export class RhodecodeFavicon extends PolymerElement {

    static get is() {
        return 'rhodecode-favicon';
    }

    static get properties() {
        return {
            favicon: Object,
            counter: {
                type: Number,
                observer: '_handleCounter'
            }
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.favicon = new Favico({
            type: 'rectangle',
            animation: 'none'
        });
    }

    _handleCounter(newVal, oldVal) {
        this.favicon.badge(this.counter);
    }

}

customElements.define(RhodecodeFavicon.is, RhodecodeFavicon);
