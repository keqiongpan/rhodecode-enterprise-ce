
<pre>
SYSTEM INFO
-----------

% for dt, dd, warn in c.data_items:
${'{:<60}'.format(dt.lower().replace(' ', '_'))}${': '+dd if dt else ''}
  % if warn and warn['message']:
        ALERT_${warn['type'].upper()} ${warn['message']}
  % endif
% endfor

PYTHON PACKAGES
---------------

% for key, value in c.py_modules['human_value']:
${'{:<60}'.format(key)}: ${value}
% endfor

SYSTEM SETTINGS
---------------

% for key, value in sorted(c.rhodecode_config['human_value'].items()):
[${key}]
  % if isinstance(value, dict):
    <% server_main = value.pop('server:main', {}) %>

    % for key2, value2 in sorted(server_main.items()):
${'{:<60}'.format('server:main')}: ${value2}
    % endfor

    % for key2, value2 in sorted(value.items()):
${'{:<60}'.format(key2)}: ${value2}
    % endfor

  % else:
${value}
  % endif

% endfor

</pre>





