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
 * QUICK REPO MENU, used on repositories to show shortcuts to files, history
 * etc.
 */

var quick_repo_menu = function() {
  var hide_quick_repo_menus = function() {
    $('.menu_items_container').hide();
    $('.active_quick_repo').removeClass('active_quick_repo');
  };
  $('.quick_repo_menu').hover(function() {
    hide_quick_repo_menus();
    if (!$(this).hasClass('active_quick_repo')) {
      $('.menu_items_container', this).removeClass("hidden").show();
      $(this).addClass('active_quick_repo');
    }
  }, function() {
    hide_quick_repo_menus();
  });
};


window.toggleElement = function (elem, target) {
  var $elem = $(elem);
  var $target = $(target);

  if (target !== undefined) {
      var show = $target.is(':visible') || $target.length === 0;
  } else {
      var show = $elem.hasClass('toggle-off')
  }

  if (show) {
    $target.hide();
    $elem.html($elem.data('toggleOn'))
    $elem.addClass('toggle-on')
    $elem.removeClass('toggle-off')
  } else {
    $target.show();
    $elem.html($elem.data('toggleOff'))
    $elem.addClass('toggle-off')
    $elem.removeClass('toggle-on')
  }

  return false
}

var marginExpVal = '300' // needs a sync with `.right-sidebar.right-sidebar-expanded` value
var marginColVal = '40'  // needs a sync with `.right-sidebar.right-sidebar-collapsed` value

var marginExpanded = {'margin': '0 {0}px 0 0'.format(marginExpVal)};
var marginCollapsed = {'margin': '0 {0}px 0 0'.format(marginColVal)};

var updateStickyHeader = function () {
    if (window.updateSticky !== undefined) {
        // potentially our comments change the active window size, so we
        // notify sticky elements
        updateSticky()
    }
}

var expandSidebar = function () {
    var $sideBar = $('.right-sidebar');
    $('.outerwrapper').css(marginExpanded);
    $('.sidebar-toggle a').html('<i class="icon-right" style="margin-right: -10px"></i><i class="icon-right"></i>');
    $('.right-sidebar-collapsed-state').hide();
    $('.right-sidebar-expanded-state').show();
    $('.branding').addClass('display-none');
    $sideBar.addClass('right-sidebar-expanded')
    $sideBar.removeClass('right-sidebar-collapsed')
}

var collapseSidebar = function () {
    var $sideBar = $('.right-sidebar');
    $('.outerwrapper').css(marginCollapsed);
    $('.sidebar-toggle a').html('<i class="icon-left" style="margin-right: -10px"></i><i class="icon-left"></i>');
    $('.right-sidebar-collapsed-state').show();
    $('.right-sidebar-expanded-state').hide();
    $('.branding').removeClass('display-none');
    $sideBar.removeClass('right-sidebar-expanded')
    $sideBar.addClass('right-sidebar-collapsed')
}

window.toggleSidebar = function () {
    var $sideBar = $('.right-sidebar');

    if ($sideBar.hasClass('right-sidebar-expanded')) {
        // expanded -> collapsed transition
        collapseSidebar();
        var sidebarState = 'collapsed';

    } else {
        // collapsed -> expanded
        expandSidebar();
        var sidebarState = 'expanded';
    }

    // update our other sticky header in same context
    updateStickyHeader();
    storeUserSessionAttr('rc_user_session_attr.sidebarState', sidebarState);
}
