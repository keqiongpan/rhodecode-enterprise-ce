import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';

export class RhodecodeUnsafeHtml extends PolymerElement {

    static get is() {
        return 'rhodecode-unsafe-html';
    }

    static get template() {
        return html`
        <style include="shared-styles"></style>
        <slot></slot>
    `;
    }

    static get properties() {
        return {
            text: {
                type: String,
                observer: '_handleText'
            }
        }
    }

    _handleText(newVal, oldVal) {
        this.innerHTML = this.text;
    }
}

customElements.define(RhodecodeUnsafeHtml.is, RhodecodeUnsafeHtml);
