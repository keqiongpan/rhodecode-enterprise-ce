
% for plugin, config in getattr(request.registry, 'rhodecode_plugins', {}).items():
    <% tmpl = config['template_hooks'].get('plugin_init_template') %>

    % if tmpl:
        <%include file="${tmpl}" args="config=config"/>
    % endif
% endfor
