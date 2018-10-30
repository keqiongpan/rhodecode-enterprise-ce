import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '@polymer/paper-toggle-button/paper-toggle-button.js';
import {mixinBehaviors} from '@polymer/polymer/lib/legacy/class.js';
import {IronA11yKeysBehavior} from '@polymer/iron-a11y-keys-behavior/iron-a11y-keys-behavior.js';
import '../rhodecode-unsafe-html/rhodecode-unsafe-html.js';

export class RhodecodeToast extends mixinBehaviors([IronA11yKeysBehavior], PolymerElement) {

    static get is() {
        return 'rhodecode-toast';
    }

    static get template(){
        return html`
        <style include="shared-styles">
            /* inset border for buttons - does not work in ie */
            /* rounded borders */
            /* rounded borders - bottom only */
            /* rounded borders - top only */
            /* text shadow */
            /* centers text in a circle - input diameter of circle and color */
            /* pill version of the circle */
            .absolute-center {
                margin: auto;
                position: absolute;
                top: 0;
                left: 0;
                bottom: 0;
                right: 0;
            }

            .top-left-rounded-corner {
                -webkit-border-top-left-radius: 2px;
                -khtml-border-radius-topleft: 2px;
                border-top-left-radius: 2px;
            }

            .top-right-rounded-corner {
                -webkit-border-top-right-radius: 2px;
                -khtml-border-radius-topright: 2px;
                border-top-right-radius: 2px;
            }

            .bottom-left-rounded-corner {
                -webkit-border-bottom-left-radius: 2px;
                -khtml-border-radius-bottomleft: 2px;
                border-bottom-left-radius: 2px;
            }

            .bottom-right-rounded-corner {
                -webkit-border-bottom-right-radius: 2px;
                -khtml-border-radius-bottomright: 2px;
                border-bottom-right-radius: 2px;
            }

            .top-left-rounded-corner-mid {
                -webkit-border-top-left-radius: 2px;
                -khtml-border-radius-topleft: 2px;
                border-top-left-radius: 2px;
            }

            .top-right-rounded-corner-mid {
                -webkit-border-top-right-radius: 2px;
                -khtml-border-radius-topright: 2px;
                border-top-right-radius: 2px;
            }

            .bottom-left-rounded-corner-mid {
                -webkit-border-bottom-left-radius: 2px;
                -khtml-border-radius-bottomleft: 2px;
                border-bottom-left-radius: 2px;
            }

            .bottom-right-rounded-corner-mid {
                -webkit-border-bottom-right-radius: 2px;
                -khtml-border-radius-bottomright: 2px;
                border-bottom-right-radius: 2px;
            }

            .alert {
                margin: 10px 0;
            }

            .toast-close {
                margin: 0;
                float: right;
                cursor: pointer;
            }

            .toast-message-holder {
                background: rgba(255, 255, 255, 0.25);
            }

            .toast-message-holder.fixed {
                position: fixed;
                padding: 10px 0;
                margin-left: 10px;
                margin-right: 10px;
                top: 0;
                left: 0;
                right: 0;
                z-index: 100;
            }
        </style>

        <template is="dom-if" if="[[hasToasts]]">
            <div class$="container toast-message-holder [[conditionalClass(isFixed)]]">
                <template is="dom-repeat" items="[[toasts]]">
                    <div class$="alert alert-[[item.level]]">
                        <div on-click="dismissNotification" class="toast-close" index-pos="[[index]]">
                            <span>[[_gettext('Close')]]</span>
                        </div>
                        <rhodecode-unsafe-html text="[[item.message]]"></rhodecode-unsafe-html>
                    </div>
                </template>
            </div>
        </template>
        `
    }

    static get properties() {
        return {
            toasts: {
                type: Array,
                value() {
                    return []
                }
            },
            isFixed: {
                type: Boolean,
                value: false
            },
            hasToasts: {
                type: Boolean,
                computed: '_computeHasToasts(toasts.*)'
            },
            keyEventTarget: {
                type: Object,
                value() {
                    return document.body;
                }
            }
        }
    }

    get keyBindings() {
        return {
            'esc:keyup': '_hideOnEsc'
        }
    }

    static get observers() {
        return [
            '_changedToasts(toasts.splices)'
        ]
    }

    _hideOnEsc(event) {
        return this.dismissNotifications();
    }

    _computeHasToasts() {
        return this.toasts.length > 0;
    }

    _debouncedCalc() {
        // calculate once in a while
        this.debounce('debouncedCalc', this.toastInWindow, 25);
    }

    conditionalClass() {
        return this.isFixed ? 'fixed' : '';
    }

    toastInWindow() {
        if (!this._headerNode) {
            return true
        }
        var headerHeight = this._headerNode.offsetHeight;
        var scrollPosition = window.scrollY;

        if (this.isFixed) {
            this.isFixed = 1 <= scrollPosition;
        }
        else {
            this.isFixed = headerHeight <= scrollPosition;
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this._headerNode = document.querySelector('.header', document);
        this.listen(window, 'scroll', '_debouncedCalc');
        this.listen(window, 'resize', '_debouncedCalc');
        this._debouncedCalc();
    }

    _changedToasts(newValue, oldValue) {
        $.Topic('/favicon/update').publish({count: this.toasts.length});
    }

    dismissNotification(e) {
        $.Topic('/favicon/update').publish({count: this.toasts.length - 1});
        var idx = e.target.parentNode.indexPos
        this.splice('toasts', idx, 1);

    }

    dismissNotifications() {
        $.Topic('/favicon/update').publish({count: 0});
        this.splice('toasts', 0);
    }

    handleNotification(data) {
        if (!templateContext.rhodecode_user.notification_status && !data.message.force) {
            // do not act if notifications are disabled
            return
        }
        this.push('toasts', {
            level: data.message.level,
            message: data.message.message
        });
    }

    _gettext(x){
        return _gettext(x)
    }

}

customElements.define(RhodecodeToast.is, RhodecodeToast);
