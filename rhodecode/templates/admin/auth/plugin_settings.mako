## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('Authentication Settings')}
    %if c.rhodecode_name:
    &middot; ${h.branding(c.rhodecode_name)}}
    %endif
</%def>

<%def name="breadcrumbs_links()">
  ${h.link_to(_('Admin'),h.route_path('admin_home'))}
  &raquo;
  ${h.link_to(_('Authentication Plugins'),request.resource_path(resource.__parent__, route_name='auth_home'))}
  &raquo;
  ${resource.display_name}
</%def>

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
        <div class="panel panel-default">
          <div class="panel-heading">
            <h3 class="panel-title">${_('Plugin')}: ${resource.display_name}</h3>
          </div>
          <div class="panel-body">
            <div class="plugin_form">
              <div class="fields">
                ${h.secure_form(request.resource_path(resource, route_name='auth_home'), request=request)}
                <div class="form">

                  %for node in plugin.get_settings_schema():
                    <%
                      label_to_type = {'label-checkbox': 'bool', 'label-textarea': 'textarea'}
                    %>

                    <div class="field">
                      <div class="label ${label_to_type.get(node.widget)}"><label for="${node.name}">${node.title}</label></div>
                      <div class="input">
                        %if node.widget in ["string", "int", "unicode"]:
                          ${h.text(node.name, defaults.get(node.name), class_="large")}
                        %elif node.widget == "password":
                          ${h.password(node.name, defaults.get(node.name), class_="large")}
                        %elif node.widget == "bool":
                          <div class="checkbox">${h.checkbox(node.name, True, checked=defaults.get(node.name))}</div>
                        %elif node.widget == "select":
                          ${h.select(node.name, defaults.get(node.name), node.validator.choices, class_="select2AuthSetting")}
                        %elif node.widget == "select_with_labels":
                          ${h.select(node.name, defaults.get(node.name), node.choices, class_="select2AuthSetting")}
                        %elif node.widget == "textarea":
                          <div class="textarea" style="margin-left: 0px">${h.textarea(node.name, defaults.get(node.name), rows=10)}</div>
                        %elif node.widget == "readonly":
                          ${node.default}
                        %else:
                          This field is of type ${node.typ}, which cannot be displayed. Must be one of [string|int|bool|select].
                        %endif

                        %if node.name in errors:
                          <span class="error-message">${errors.get(node.name)}</span>
                          <br />
                        %endif
                        <p class="help-block pre-formatting">${node.description}</p>
                      </div>
                    </div>
                  %endfor

                  ## Allow derived templates to add something below the form
                  ## input fields
                  %if hasattr(next, 'below_form_fields'):
                    ${next.below_form_fields()}
                  %endif

                  <div class="buttons">
                    ${h.submit('save',_('Save'),class_="btn")}
                  </div>

                </div>
                ${h.end_form()}
              </div>
            </div>

% if request.GET.get('schema'):
## this is for development and creation of example configurations for documentation
<pre>
    % for node in plugin.get_settings_schema():
    *option*: `${node.name}` => `${defaults.get(node.name)}`${'\n    # '.join(['']+node.description.splitlines())}

    % endfor
</pre>

% endif

          </div>
        </div>
      </div>

    </div>
  </div>


<script>
$(document).ready(function() {
  var select2Options = {
        containerCssClass: 'drop-menu',
        dropdownCssClass: 'drop-menu-dropdown',
        dropdownAutoWidth: true,
        minimumResultsForSearch: -1
  };
  $('.select2AuthSetting').select2(select2Options);

});
</script>
</%def>
