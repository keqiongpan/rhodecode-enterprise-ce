<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Labs Settings')}</h3>
    </div>
    <div class="panel-body">
        ${h.secure_form(h.route_path('admin_settings_labs_update'), request=request)}
          <div class="form">
            <div class="fields">
              % if not c.lab_settings:
                ${_('There are no Labs settings currently')}
              % else:
                  % for lab_setting in c.lab_settings:
                  <div class="field">
                    <div class="label">
                      <label>${lab_setting.group}:</label>
                    </div>
                    % if lab_setting.type == 'bool':
                      <div class="checkboxes">
                        <div class="checkbox">
                          ${h.checkbox(lab_setting.key, 'True')}
                          % if lab_setting.label:
                            <label for="${lab_setting.key}">${lab_setting.label}</label>
                          % endif
                        </div>
                        % if lab_setting.help:
                          <p class="help-block">${lab_setting.help}</p>
                        % endif
                      </div>
                    % else:
                      <div class="input">
                        ${h.text(lab_setting.key, size=60)}

                        ## TODO: johbo: This style does not yet exist for our forms,
                        ## the lab settings seem not to adhere to the structure which
                        ## we use in other places.
                        % if lab_setting.label:
                          <label for="${lab_setting.key}">${lab_setting.label}</label>
                        % endif

                        % if lab_setting.help:
                          <p class="help-block">${lab_setting.help}</p>
                        % endif
                      </div>
                    % endif
                  </div>
                  % endfor
                  <div class="buttons">
                    ${h.submit('save', _('Save settings'), class_='btn')}
                    ${h.reset('reset', _('Reset'), class_='btn')}
                  </div>
              % endif
            </div>
          </div>
        ${h.end_form()}
    </div>
</div>


