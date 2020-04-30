// # Copyright (C) 2010-2020 RhodeCode GmbH
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

var generatePassword = function(length) {
    if (length === undefined){
        length = 8
    }

    var charset = "abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    var gen_pass = "";

    for (var i = 0, n = charset.length; i < length; ++i) {
        gen_pass += charset.charAt(Math.floor(Math.random() * n));
    }
    return gen_pass;
};

/**
 * User autocomplete
 */
var UsersAutoComplete = function(input_id, user_id) {
  $('#'+input_id).autocomplete({
    serviceUrl: pyroutes.url('user_autocomplete_data'),
    minChars:2,
    maxHeight:400,
    deferRequestBy: 300, //miliseconds
    showNoSuggestionNotice: true,
    tabDisabled: true,
    autoSelectFirst: true,
    params: { user_id: user_id },
    formatResult: autocompleteFormatResult,
    lookupFilter: autocompleteFilterResult
  });
};

var _showAuthToken = function (authTokenId, showUrl) {

    Swal.fire({
        title: _gettext('Show this authentication token?'),
        showCancelButton: true,
        confirmButtonColor: '#84a5d2',
        cancelButtonColor: '#e85e4d',
        showClass: {
            popup: 'swal2-noanimation',
            backdrop: 'swal2-noanimation'
        },
        hideClass: {
            popup: '',
            backdrop: ''
        },
        confirmButtonText: _gettext('Show'),
        showLoaderOnConfirm: true,
        allowOutsideClick: function () {
            !Swal.isLoading()
        },
        preConfirm: function () {

            var postData = {
                'auth_token_id': authTokenId,
                'csrf_token': CSRF_TOKEN
            };
            return new Promise(function (resolve, reject) {
                $.ajax({
                    type: 'POST',
                    data: postData,
                    url: showUrl,
                    headers: {'X-PARTIAL-XHR': true}
                })
                .done(function (data) {
                    resolve(data);
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    //reject("Failed to fetch Authentication Token")
                    var message = formatErrorMessage(jqXHR, textStatus, errorThrown);
                    ajaxErrorSwal(message);
                });
            })
        }

    })
    .then(function (result) {
        if (result.value) {
            var tmpl = ('<code>{0}</code>' +
                       '<i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="{1}" title="Copy Token"></i>');

            Swal.fire({
                title: _gettext('Authentication Token'),
                html: tmpl.format(result.value.auth_token, result.value.auth_token),
                confirmButtonColor: '#84a5d2',
                cancelButtonColor: '#e85e4d',
                showClass: {
                    popup: 'swal2-noanimation',
                    backdrop: 'swal2-noanimation'
                },
                hideClass: {
                    popup: '',
                    backdrop: ''
                },
            })
        }
    })
}