
<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('Your Live Notification Settings')}</h3>
  </div>
  <div class="panel-body">

        <p><strong>IMPORTANT:</strong> This feature requires enabled channelstream websocket server to function correctly.</p>

        <p class="hidden">Status of browser notifications permission: <strong id="browser-notification-status"></strong></p>

        <div class="form">
            <div class="fields">
                <div class="field">
                    <div class="label">
                        <label for="new_email">${_('Notifications Status')}:</label>
                    </div>
                    <div class="checkboxes">

                        <div class="form-check">
                          <label class="form-check-label">
                            <input type="radio" name="notification" id="notificationEnable1" value="1" onchange="notificationsController.toggleNotifications(this);return false" ${'checked' if c.rhodecode_user.get_instance().user_data.get('notification_status') else ''}>
                              ${_('Enabled')}
                          </label>
                          <label class="form-check-label">
                            <input type="radio" name="notification" id="notificationEnable2" value="0" onchange="notificationsController.toggleNotifications(this);return false" ${'checked' if not c.rhodecode_user.get_instance().user_data.get('notification_status') else ''}>
                            ${_('Disabled')}
                          </label>
                        </div>

                    </div>
                </div>
            </div>
        </div>
  </div>
</div>

<div class="panel panel-default">
  <div class="panel-heading">
    <h3 class="panel-title">${_('Test Notifications')}</h3>
  </div>
  <div class="panel-body">

        <div style="padding: 0px 0px 20px 0px">
            <button class="btn" id="test-notification" onclick="notificationsController.testNotifications(); return false">Test flash message</button>
            <button class="btn" id="test-notification-live" onclick="notificationsController.testNotificationsLive(); return false">Test live notification</button>
        </div>
        <h4 id="test-response"></h4>

  </div>

</div>

<script type="text/javascript">

    var NotificationsController = function () {
        var self = this;
        this.$testResponse = $('#test-response');
        this.$notificationPage = $('#notificationsPage');

        this.toggleNotifications = function (elem) {
            var $elem = $(elem);

            var post_data = {'val': $elem.val(), 'csrf_token': CSRF_TOKEN};
            var url = pyroutes.url('my_account_notifications_toggle_visibility');

            ajaxPOST(url, post_data, function (resp) {
                if (resp === true) {
                    $('input[name="notification"]').filter('[value="1"]').prop('checked', true);
                    $('input[name="notification"]').filter('[value="0"]').prop('checked', false);
                } else {
                    $('input[name="notification"]').filter('[value="1"]').prop('checked', false);
                    $('input[name="notification"]').filter('[value="0"]').prop('checked', true);
                }
            })
        };

        this.testNotifications = function (elem) {
            var levels = ['info', 'error', 'warning', 'success'];
            var level = levels[Math.floor(Math.random() * levels.length)];

            function getRandomArbitrary(min, max) {
                return parseInt(Math.random() * (max - min) + min);
            }

            function shuffle(a) {
                var j, x, i;
                for (i = a.length; i; i--) {
                    j = Math.floor(Math.random() * i);
                    x = a[i - 1];
                    a[i - 1] = a[j];
                    a[j] = x;
                }
            }

            var wordDb = [
                "Leela,", "Bender,", "we are", "going", "grave", "robbing.",
                "Oh,", "I", "think", "we", "should", "just", "stay", "friends.",
                "got", "to", "find", "a", "way", "to", "escape", "the", "horrible",
                "ravages", "of", "youth.", "Suddenly,", "going", "to",
                "the", "bathroom", "like", "clockwork,", "every", "three",
                "hours.", "And", "those", "jerks", "at", "Social", "Security",
                "stopped", "sending", "me", "checks.", "Now", "have", "to", "pay"
            ];
            shuffle(wordDb);
            wordDb = wordDb.slice(0, getRandomArbitrary(3, wordDb.length));
            var randomMessage = wordDb.join(" ");
            var payload = {
                message: {
                    message: randomMessage + " " + new Date(),
                    level: level,
                    force: true
                }
            };
            $.Topic('/notifications').publish(payload);
        };

        this.testNotificationsLive = function (event) {
            var post_data = {'test_msg': 'Hello Server', 'csrf_token': CSRF_TOKEN};
            var url = pyroutes.url('my_account_notifications_test_channelstream');

            ajaxPOST(url, post_data, function (resp) {
                resp = resp['response'] || 'no reply form server';
                self.$testResponse.html(resp);
                self.$testResponse.show();
            })
        };
    };

    notificationsController = new NotificationsController();
</script>
