import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '../channelstream-connection/channelstream-connection.js';
import '../rhodecode-toast/rhodecode-toast.js';
import '../rhodecode-favicon/rhodecode-favicon.js';

var ccLog = Logger.get('RhodeCodeApp');
ccLog.setLevel(Logger.OFF);

export class RhodecodeApp extends PolymerElement {

    static get is() {
        return 'rhodecode-app';
    }

    static get template(){
        return html`
        <channelstream-connection
                id="channelstream-connection"
                on-channelstream-listen-message="receivedMessage"
                on-channelstream-connected="handleConnected"
                on-channelstream-subscribed="handleSubscribed">
        </channelstream-connection>
        <rhodecode-favicon></rhodecode-favicon>
        `
    }

    connectedCallback() {
        super.connectedCallback();
        ccLog.debug('rhodeCodeApp created');
        $.Topic('/notifications').subscribe(this.handleNotifications.bind(this));
        $.Topic('/comment').subscribe(this.handleComment.bind(this));
        $.Topic('/favicon/update').subscribe(this.faviconUpdate.bind(this));
        $.Topic('/connection_controller/subscribe').subscribe(
            this.subscribeToChannelTopic.bind(this)
        );

        // this event can be used to coordinate plugins to do their
        // initialization before channelstream is kicked off
        $.Topic('/__MAIN_APP__').publish({});

        for (var i = 0; i < alertMessagePayloads.length; i++) {
            $.Topic('/notifications').publish(alertMessagePayloads[i]);
        }
        this.initPlugins();
        // after rest of application loads and topics get fired, launch connection
        $(document).ready(function () {
            this.kickoffChannelstreamPlugin();
        }.bind(this));
    }

    initPlugins() {
        for (var i = 0; i < window.APPLICATION_PLUGINS.length; i++) {
            var pluginDef = window.APPLICATION_PLUGINS[i];
            if (pluginDef.component) {
                var pluginElem = document.createElement(pluginDef.component);
                this.shadowRoot.appendChild(pluginElem);
                if (typeof pluginElem.init !== 'undefined') {
                    pluginElem.init();
                }
            }
        }
    }

    /** proxy to channelstream connection */
    getChannelStreamConnection() {
        return this.$['channelstream-connection'];
    }

    handleNotifications(data) {
        var elem = document.getElementById('notifications');
        if (elem) {
            elem.handleNotification(data);
        }
    }

    handleComment(data) {

        if (data.message.comment_data.length !== 0) {
          if (window.refreshAllComments !== undefined) {
              refreshAllComments()
          }
          var json_data = data.message.comment_data;

          if (window.commentsController !== undefined) {

            window.commentsController.attachComment(json_data)
          }
        }
    }

    faviconUpdate(data) {
        this.shadowRoot.querySelector('rhodecode-favicon').counter = data.count;
    }

    /** opens connection to ws server */
    kickoffChannelstreamPlugin(data) {
        ccLog.debug('kickoffChannelstreamPlugin');
        var channels = ['broadcast'];
        var addChannels = this.checkViewChannels();
        for (var i = 0; i < addChannels.length; i++) {
            channels.push(addChannels[i]);
        }
        if (window.CHANNELSTREAM_SETTINGS && CHANNELSTREAM_SETTINGS.enabled) {
            var channelstreamConnection = this.getChannelStreamConnection();
            channelstreamConnection.connectUrl = CHANNELSTREAM_URLS.connect;
            channelstreamConnection.subscribeUrl = CHANNELSTREAM_URLS.subscribe;
            channelstreamConnection.websocketUrl = CHANNELSTREAM_URLS.ws + '/ws';
            channelstreamConnection.longPollUrl = CHANNELSTREAM_URLS.longpoll + '/listen';
            // some channels might already be registered by topic
            for (var i = 0; i < channels.length; i++) {
                channelstreamConnection.push('channels', channels[i]);
            }
            // append any additional channels registered in other plugins
            $.Topic('/connection_controller/subscribe').processPrepared();

            channelstreamConnection.connect();
        }
    }

    checkViewChannels() {
        // subscribe to different channels data is sent.

        var channels = [];
        // subscribe to PR repo channel for PR's'
        if (templateContext.pull_request_data.pull_request_id) {
            var channelName = '/repo$' + templateContext.repo_name + '$/pr/' +
                String(templateContext.pull_request_data.pull_request_id);
            channels.push(channelName);
        }

        if (templateContext.commit_data.commit_id) {
            var channelName = '/repo$' + templateContext.repo_name + '$/commit/' +
                String(templateContext.commit_data.commit_id);
            channels.push(channelName);
        }

        return channels;
    }

    /** subscribes users from channels in channelstream */
    subscribeToChannelTopic(channels) {
        var channelstreamConnection = this.getChannelStreamConnection();
        var toSubscribe = channelstreamConnection.calculateSubscribe(channels);
        ccLog.debug('subscribeToChannelTopic', toSubscribe);
        if (toSubscribe.length > 0) {
            // if we are connected then subscribe
            if (channelstreamConnection.connected) {
                channelstreamConnection.subscribe(toSubscribe);
            }
            // not connected? just push channels onto the stack
            else {
                for (var i = 0; i < toSubscribe.length; i++) {
                    channelstreamConnection.push('channels', toSubscribe[i]);
                }
            }
        }
    }

    /** publish received messages into correct topic */
    receivedMessage(event) {
        for (var i = 0; i < event.detail.length; i++) {
            var message = event.detail[i];
            if (message.message.topic) {
                ccLog.debug('publishing', message.message.topic);
                $.Topic(message.message.topic).publish(message);
            }
            else if (message.type === 'presence') {
                $.Topic('/connection_controller/presence').publish(message);
            }
            else {
                ccLog.warn('unhandled message', message);
            }
        }
    }

    handleConnected(event) {
        var channelstreamConnection = this.getChannelStreamConnection();
        channelstreamConnection.set('channelsState', event.detail.channels_info);
        channelstreamConnection.set('userState', event.detail.state);
        channelstreamConnection.set('channels', event.detail.channels);
        this.propagageChannelsState();
    }

    handleSubscribed(event) {
        var channelstreamConnection = this.getChannelStreamConnection();
        var channelInfo = event.detail.channels_info;
        var channelKeys = Object.keys(event.detail.channels_info);
        for (var i = 0; i < channelKeys.length; i++) {
            var key = channelKeys[i];
            channelstreamConnection.set(['channelsState', key], channelInfo[key]);
        }
        channelstreamConnection.set('channels', event.detail.channels);
        this.propagageChannelsState();
    }

    /** propagates channel states on topics */
    propagageChannelsState(event) {
        var channelstreamConnection = this.getChannelStreamConnection();
        var channel_data = channelstreamConnection.channelsState;
        var channels = channelstreamConnection.channels;
        for (var i = 0; i < channels.length; i++) {
            var key = channels[i];
            $.Topic('/connection_controller/channel_update').publish(
                {channel: key, state: channel_data[key]}
            );
        }
    }

}

customElements.define(RhodecodeApp.is, RhodecodeApp);
