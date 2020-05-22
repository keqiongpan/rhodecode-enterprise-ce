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

var EJS_TEMPLATES = {};

var renderTemplate = function(tmplName, data) {
    var tmplStr = getTemplate(tmplName);
    var options = {};
    var template = ejs.compile(tmplStr, options);
    return template(data);
};


var registerTemplate = function (name) {
    if (EJS_TEMPLATES[name] !== undefined) {
        return
    }

    var template = $('#ejs_' + name);

    if (template.get(0) !== undefined) {
        EJS_TEMPLATES[name] = template.html();
    } else {
        console.log('Failed to register template', name)
    }
};


var registerTemplates = function () {
    $.each($('.ejsTemplate'), function(idx, value) {
      var id = $(value).attr('id');
      var tmplId = id.substring(0, 4);
      var tmplName = id.substring(4);
      if (tmplId === 'ejs_') {
          registerTemplate(tmplName)
      }
    });
};


var getTemplate = function (name) {
    return EJS_TEMPLATES[name]
};
