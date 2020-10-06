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

/**
* turns objects into GET query string
*/
var toQueryString = function(o) {
  if(typeof o === 'string') {
    return o;
  }
  if(typeof o !== 'object') {
    return false;
  }
  var _p, _qs = [];
  for(_p in o) {
    _qs.push(encodeURIComponent(_p) + '=' + encodeURIComponent(o[_p]));
  }
  return _qs.join('&');
};

/**
* ajax call wrappers
*/

var ajaxGET = function (url, success, failure) {
    var sUrl = url;
    var request = $.ajax({
        url: sUrl,
        headers: {'X-PARTIAL-XHR': true}
        })
        .done(function (data) {
            success(data);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            if (failure) {
                failure(jqXHR, textStatus, errorThrown);
            } else {
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown);
                ajaxErrorSwal(message);
            }
        });
    return request;
};

var ajaxPOST = function (url, postData, success, failure, options) {

    var ajaxSettings = $.extend({
        type: 'POST',
        url: url,
        data: toQueryString(postData),
        headers: {'X-PARTIAL-XHR': true}
    }, options);

    var request = $.ajax(
        ajaxSettings
        )
        .done(function (data) {
            success(data);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            if (failure) {
                failure(jqXHR, textStatus, errorThrown);
            } else {
                var message = formatErrorMessage(jqXHR, textStatus, errorThrown);
                ajaxErrorSwal(message);
            }
        });
    return request;
};


SwalNoAnimation = Swal.mixin({
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


/* Example usage:
*
  error: function(jqXHR, textStatus, errorThrown) {
    var prefix = "Error while fetching entries.\n"
    var message = formatErrorMessage(jqXHR, textStatus, errorThrown, prefix);
    ajaxErrorSwal(message);
   }
*
* */
function formatErrorMessage(jqXHR, textStatus, errorThrown, prefix) {
    if(typeof prefix === "undefined") {
        prefix = ''
    }

    if (jqXHR.status === 0) {
        return (prefix + 'Not connected.\nPlease verify your network connection.');
    } else if (jqXHR.status == 401) {
        return (prefix + 'Unauthorized access. [401]');
    } else if (jqXHR.status == 404) {
        return (prefix + 'The requested page not found. [404]');
    } else if (jqXHR.status == 500) {
        return (prefix + 'Internal Server Error [500].');
    } else if (jqXHR.status == 503) {
        return (prefix + 'Service unavailable [503].');
    } else if (errorThrown === 'parsererror') {
        return (prefix + 'Requested JSON parse failed.');
    } else if (errorThrown === 'timeout') {
        return (prefix + 'Time out error.');
    } else if (errorThrown === 'abort') {
        return (prefix + 'Ajax request aborted.');
    } else {
        var errInfo = 'Uncaught Error. code: {0}\n'.format(jqXHR.status)
        return (prefix + errInfo + jqXHR.responseText);
    }
}

function ajaxErrorSwal(message, title) {

    var title = (typeof title !== 'undefined') ? title : _gettext('Ajax Request Error');

    SwalNoAnimation.fire({
        icon: 'error',
        title: title,
        html: '<span style="white-space: pre-line">{0}</span>'.format(message),
        showClass: {
            popup: 'swal2-noanimation',
            backdrop: 'swal2-noanimation'
        },
        hideClass: {
            popup: '',
            backdrop: ''
        }
    })
}

/*
* use in onclick attributes e.g
* onclick="submitConfirm(event, this, _gettext('Confirm to delete '), _gettext('Confirm Delete'), 'what we delete')">
* */
function submitConfirm(event, self, question, confirmText, htmlText) {
    if (htmlText === "undefined") {
        htmlText = null;
    }
    if (confirmText === "undefined") {
        confirmText = _gettext('Delete')
    }
    event.preventDefault();

    SwalNoAnimation.fire({
      title: question,
      icon: 'warning',
      html: htmlText,

      showCancelButton: true,

      confirmButtonText: confirmText
    }).then(function(result) {
      if (result.value) {
          $(self).closest("form").submit();
      }
    })
}