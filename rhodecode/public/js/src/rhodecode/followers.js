// # Copyright (C) 2010-2019 RhodeCode GmbH
// #
// # This program is free software: you can redistribute it and/or modify
// # it under the terms of the GNU Affero General Public License, version 3
// # (only), as published by the Free Software Foundation.
// #
// # This program is distributed in the hope that it will be useful,
// # but WITHOUT ANY WARRANTY; without even the implied warranty of
// # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// # GNU General Public License for more details.
// #
// # You should have received a copy of the GNU Affero General Public License
// # along with this program.  If not, see <http://www.gnu.org/licenses/>.
// #
// # This program is dual-licensed. If you wish to learn more about the
// # RhodeCode Enterprise Edition, including its added features, Support services,
// # and proprietary license terms, please see https://rhodecode.com/licenses/

var onSuccessFollow = function (target) {
    var targetEl = $(target);

    var callback = function () {
        targetEl.animate({'opacity': 1.00}, 200);
        if (targetEl.hasClass('watching')) {
            targetEl.removeClass('watching');
            targetEl.attr('title', _gettext('Stopped watching this repository'));
            $(targetEl).html('<i class="icon-eye"></i>'+_gettext('Watch'));
        } else {
            targetEl.addClass('watching');
            targetEl.attr('title', _gettext('Started watching this repository'));
            $(targetEl).html('<i class="icon-eye-off"></i>'+_gettext('Unwatch'));
        }
    };
    targetEl.animate({'opacity': 0.15}, 200, callback);
};


var toggleFollowingUser = function (target, follows_user_id) {
    var args = {
        'follows_user_id': follows_user_id,
        'csrf_token': CSRF_TOKEN
    };

    ajaxPOST(pyroutes.url('toggle_following'), args, function () {
        onSuccessFollow(target);
    });
    return false;
};

var toggleFollowingRepo = function (target, follows_repo_id) {
    var args = {
        'follows_repo_id': follows_repo_id,
        'csrf_token': CSRF_TOKEN
    };

    ajaxPOST(pyroutes.url('toggle_following'), args, function () {
        onSuccessFollow(target);
    });
    return false;
};
