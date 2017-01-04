
<pre>
SYSTEM INFO
-----------

% for dt, dd, warn in c.data_items:
  ${dt.lower().replace(' ', '_')}${': '+dd if dt else '---'}
  % if warn and warn['message']:
        ALERT_${warn['type'].upper()} ${warn['message']}
  % endif
% endfor

PYTHON PACKAGES
---------------

% for key, value in c.py_modules['human_value']:
${key}: ${value}
% endfor

SYSTEM SETTINGS
---------------

% for key, value in sorted(c.rhodecode_config['human_value'].items()):
  % if isinstance(value, dict):

    % for key2, value2 in value.items():
[${key}]${key2}: ${value2}
    % endfor

  % else:
${key}: ${value}
  % endif
% endfor

</pre>





