## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Authentication Settings')}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}}
    %endif
</%def>

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='admin')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.admin_menu(active='authentication')}
</%def>

<%def name="main()">

<div class="box">

  <div class='sidebar-col-wrapper'>

    <div class="sidebar">
        <ul class="nav nav-pills nav-stacked">
          % for item in resource.get_root().get_nav_list():
            <li ${('class=active' if item == resource else '')}>
              <a href="${request.resource_path(item, route_name='auth_home')}">${item.display_name}</a>
            </li>
          % endfor
        </ul>
    </div>

    <div class="main-content-full-width">
      ${h.secure_form(request.resource_path(resource, route_name='auth_home'), request=request)}
        <div class="panel panel-default">

          <div class="panel-heading">
            <h3 class="panel-title">${_("Enabled and Available Plugins")}</h3>
          </div>

          <div class="panel-body">


              <div class="label">${_("Ordered Activated Plugins")}</div>
              <div class="textarea text-area editor">
                  ${h.textarea('auth_plugins',cols=120,rows=20,class_="medium")}
              </div>
              <div class="field">
                <p class="help-block pre-formatting">${_('List of plugins, separated by commas.'
                  '\nThe order of the plugins is also the order in which '
                  'RhodeCode Enterprise will try to authenticate a user.')}
                </p>
              </div>

              <table class="rctable">
                  <th>${_('Activate')}</th>
                  <th>${_('Plugin Name')}</th>
                  <th>${_('Documentation')}</th>
                  <th>${_('Plugin ID')}</th>
                  <th>${_('Enabled')}</th>
                  %for plugin in available_plugins:
                      <tr class="${('inactive' if (not plugin.is_active() and plugin.get_id() in enabled_plugins) else '')}">
                          <td>
                            <span plugin_id="${plugin.get_id()}" class="toggle-plugin btn ${('btn-success' if plugin.get_id() in enabled_plugins else '')}">
                              ${(_('activated') if plugin.get_id() in enabled_plugins else _('not active'))}
                            </span>
                          </td>
                          <td>${plugin.get_display_name()}</td>
                          <td>
                              % if plugin.docs():
                                <a href="${plugin.docs()}">docs</a>
                              % endif
                          </td>
                          <td>${plugin.get_id()}</td>
                          <td>${h.bool2icon(plugin.is_active(),show_at_false=False)}</td>
                      </tr>
                  %endfor
              </table>

            <div class="buttons">
              ${h.submit('save',_('Save'),class_="btn")}
            </div>
          </div>
        </div>
      ${h.end_form()}
    </div>
  </div>
</div>

<script>
  $('.toggle-plugin').click(function(e){
    var auth_plugins_input = $('#auth_plugins');
    var elems = [];

    $.each(auth_plugins_input.val().split(',') , function (index, element) {
        if (element !== "") {
            elems.push(element.strip())
        }
    });

    var cur_button = e.currentTarget;
    var plugin_id = $(cur_button).attr('plugin_id');
    if($(cur_button).hasClass('btn-success')){
      elems.splice(elems.indexOf(plugin_id), 1);
      auth_plugins_input.val(elems.join(',\n'));
      $(cur_button).removeClass('btn-success');
      cur_button.innerHTML = _gettext('not active');
    }
    else{
      if (elems.indexOf(plugin_id) === -1) {
            elems.push(plugin_id);
      }
      auth_plugins_input.val(elems.join(',\n'));
      $(cur_button).addClass('btn-success');
      cur_button.innerHTML = _gettext('activated');
    }
  });
</script>
</%def>
