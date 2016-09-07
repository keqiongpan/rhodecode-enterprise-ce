"use strict";
/** leak object to top level scope **/
var ccLog = undefined;
// global code-mirror logger;, to enable run
// Logger.get('ConnectionController').setLevel(Logger.DEBUG)
ccLog = Logger.get('ConnectionController');
ccLog.setLevel(Logger.OFF);

var ConnectionController;
var connCtrlr;
var registerViewChannels;

(function () {
    ConnectionController = function (webappUrl, serverUrl, urls) {
        var self = this;

        var channels = ['broadcast'];
        this.state = {
            open: false,
            webappUrl: webappUrl,
            serverUrl: serverUrl,
            connId: null,
            socket: null,
            channels: channels,
            heartbeat: null,
            channelsInfo: {},
            urls: urls
        };
        this.channelNameParsers = [];

        this.addChannelNameParser = function (fn) {
            if (this.channelNameParsers.indexOf(fn) === -1) {
                this.channelNameParsers.push(fn);
            }
        };

        this.listen = function () {
            if (window.WebSocket) {
                ccLog.debug('attempting to create socket');
                var socket_url = self.state.serverUrl + "/ws?conn_id=" + self.state.connId;
                var socket_conf = {
                    url: socket_url,
                    handleAs: 'json',
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
                };
                self.state.socket = new WebSocket(socket_conf.url);

                self.state.socket.onopen = function (event) {
                    ccLog.debug('open event', event);
                    if (self.state.heartbeat === null) {
                        self.state.heartbeat = setInterval(function () {
                            if (self.state.socket.readyState === WebSocket.OPEN) {
                                self.state.socket.send('heartbeat');
                            }
                        }, 10000)
                    }
                };
                self.state.socket.onmessage = function (event) {
                    var data = $.parseJSON(event.data);
                    for (var i = 0; i < data.length; i++) {
                        if (data[i].message.topic) {
                            ccLog.debug('publishing',
                                data[i].message.topic, data[i]);
                            $.Topic(data[i].message.topic).publish(data[i])
                        }
                        else {
                            ccLog.warn('unhandled message', data);
                        }
                    }
                };
                self.state.socket.onclose = function (event) {
                    ccLog.debug('closed event', event);
                    setTimeout(function () {
                        self.connect(true);
                    }, 5000);
                };

                self.state.socket.onerror = function (event) {
                    ccLog.debug('error event', event);
                };
            }
            else {
                ccLog.debug('attempting to create long polling connection');
                var poolUrl = self.state.serverUrl + "/listen?conn_id=" + self.state.connId;
                self.state.socket = $.ajax({
                    url: poolUrl
                }).done(function (data) {
                    ccLog.debug('data', data);
                    var data = $.parseJSON(data);
                    for (var i = 0; i < data.length; i++) {
                        if (data[i].message.topic) {
                            ccLog.info('publishing',
                                data[i].message.topic, data[i]);
                            $.Topic(data[i].message.topic).publish(data[i])
                        }
                        else {
                            ccLog.warn('unhandled message', data);
                        }
                    }
                    self.listen();
                }).fail(function () {
                    ccLog.debug('longpoll error');
                    setTimeout(function () {
                        self.connect(true);
                    }, 5000);
                });
            }

        };

        this.connect = function (create_new_socket) {
            var connReq = {'channels': self.state.channels};
            ccLog.debug('try obtaining connection info', connReq);
            $.ajax({
                url: self.state.urls.connect,
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify(connReq),
                dataType: "json"
            }).done(function (data) {
                ccLog.debug('Got connection:', data.conn_id);
                self.state.channels = data.channels;
                self.state.channelsInfo = data.channels_info;
                self.state.connId = data.conn_id;
                if (create_new_socket) {
                    self.listen();
                }
                self.update();
            }).fail(function () {
                setTimeout(function () {
                    self.connect(create_new_socket);
                }, 5000);
            });
            self.update();
        };

        this.subscribeToChannels = function (channels) {
            var new_channels = [];
            for (var i = 0; i < channels.length; i++) {
                var channel = channels[i];
                if (self.state.channels.indexOf(channel)) {
                    self.state.channels.push(channel);
                    new_channels.push(channel)
                }
            }
            /**
             * only execute the request if socket is present because subscribe
             * can actually add channels before initial app connection
             **/
            if (new_channels && self.state.socket !== null) {
                var connReq = {
                    'channels': self.state.channels,
                    'conn_id': self.state.connId
                };
                $.ajax({
                    url: self.state.urls.subscribe,
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify(connReq),
                    dataType: "json"
                }).done(function (data) {
                    self.state.channels = data.channels;
                    self.state.channelsInfo = data.channels_info;
                    self.update();
                });
            }
            self.update();
        };

        this.update = function () {
            for (var key in this.state.channelsInfo) {
                if (this.state.channelsInfo.hasOwnProperty(key)) {
                    // update channels with latest info
                    $.Topic('/connection_controller/channel_update').publish(
                        {channel: key, state: this.state.channelsInfo[key]});
                }
            }
            /**
             * checks current channel list in state and if channel is not present
             * converts them into executable "commands" and pushes them on topics
             */
            for (var i = 0; i < this.state.channels.length; i++) {
                var channel = this.state.channels[i];
                for (var j = 0; j < this.channelNameParsers.length; j++) {
                    this.channelNameParsers[j](channel);
                }
            }
        };

        this.run = function () {
            this.connect(true);
        };

        $.Topic('/connection_controller/subscribe').subscribe(
            self.subscribeToChannels);
    };

    $.Topic('/plugins/__REGISTER__').subscribe(function (data) {
        if (window.CHANNELSTREAM_SETTINGS && window.CHANNELSTREAM_SETTINGS.enabled) {
            connCtrlr = new ConnectionController(
                CHANNELSTREAM_SETTINGS.webapp_location,
                CHANNELSTREAM_SETTINGS.ws_location,
                CHANNELSTREAM_URLS
            );
            registerViewChannels();

            $(document).ready(function () {
                connCtrlr.run();
            });
        }
    });

registerViewChannels = function (){
    // subscribe to PR repo channel for PR's'
    if (templateContext.pull_request_data.pull_request_id) {
        var channelName = '/repo$' + templateContext.repo_name + '$/pr/' +
            String(templateContext.pull_request_data.pull_request_id);
        connCtrlr.state.channels.push(channelName);
    }
}

})();
