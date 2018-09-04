<dom-bind id="notificationsPage">
<template>
<iron-ajax id="toggleNotifications"
           method="post"
           url="${h.route_path('my_account_notifications_toggle_visibility')}"
           content-type="application/json"
           loading="{{changeNotificationsLoading}}"
           on-response="handleNotifications"
           handle-as="json">
</iron-ajax>

<iron-ajax id="sendTestNotification"
           method="post"
           url="${h.route_path('my_account_notifications_test_channelstream')}"
           content-type="application/json"
           on-response="handleTestNotification"
           handle-as="json">
</iron-ajax>

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
                        <rhodecode-toggle id="live-notifications" active="[[changeNotificationsLoading]]" on-change="toggleNotifications" ${'checked' if c.rhodecode_user.get_instance().user_data.get('notification_status') else ''}></rhodecode-toggle>
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
            <button class="btn" id="test-notification" on-tap="testNotifications">Test flash message</button>
            <button class="btn" id="test-notification-live" on-tap="testNotificationsLive">Test live notification</button>
        </div>
            <h4 id="test-response"></h4>

  </div>



</div>


</template>
</dom-bind>

<script type="text/javascript">
    /** because im not creating a custom element for this page
     * we need to push the function onto the dom-template
     * ideally we turn this into notification-settings elements
     * then it will be cleaner
     */
    var ctrlr = $('#notificationsPage')[0];
    ctrlr.toggleNotifications = function(event){
        var ajax = $('#toggleNotifications')[0];
        ajax.headers = {"X-CSRF-Token": CSRF_TOKEN};
        ajax.body = {notification_status:event.target.active};
        ajax.generateRequest();
    };
    ctrlr.handleNotifications = function(event){
        $('#live-notifications')[0].checked = event.detail.response;
    };

    ctrlr.testNotifications = function(event){
        var levels = ['info', 'error', 'warning', 'success'];
        var level = levels[Math.floor(Math.random()*levels.length)];
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
    ctrlr.testNotificationsLive = function(event){
        var ajax = $('#sendTestNotification')[0];
        ajax.headers = {"X-CSRF-Token": CSRF_TOKEN};
        ajax.body = {test_msg: 'Hello !'};
        ajax.generateRequest();
    };
    ctrlr.handleTestNotification = function(event){
        var reply = event.detail.response.response;
        reply = reply || 'no reply form server';
        $('#test-response').html(reply);
    };

</script>
