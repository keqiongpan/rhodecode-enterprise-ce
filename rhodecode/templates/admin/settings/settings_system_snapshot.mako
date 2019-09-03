
<pre>
SYSTEM INFO
-----------

% for dt, dd, warn in c.data_items:
${'{:<60}'.format(dt.lower().replace(' ', '_'))}${': {}'.format(dd if dt else '')}
  % if warn and warn['message']:
${'{:<60}'.format('ALERT')} ${warn['type'].upper()} ${warn['message']}
  % endif
% endfor

SYSTEM SETTINGS
---------------

% for key, value in sorted(c.rhodecode_config['human_value'].items()):
  % if isinstance(value, dict):
    <%
        conf_file = value.pop('__file__', {})
        server_main = value.pop('server:main', {})
    %>
[${key}]
${'{:<60}'.format('__file__')}: ${conf_file}

    % for key2, value2 in sorted(server_main.items()):
${'{:<60}'.format(key2)}: ${value2}
    % endfor

    % for key2, value2 in sorted(value.items()):
${'{:<60}'.format(key2)}: ${value2}
    % endfor

  % else:
[${key}]
${value}
  % endif

% endfor

PYTHON PACKAGES
---------------

% for key, value in c.py_modules['human_value']:
${'{:<60}'.format(key)}: ${value}
% endfor

</pre>





