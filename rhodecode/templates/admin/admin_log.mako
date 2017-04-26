## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

%if c.users_log:
<table class="rctable admin_log">
    <tr>
        <th>${_('Username')}</th>
        <th>${_('Action')}</th>
        <th>${_('Action Data')}</th>
        <th>${_('Repository')}</th>
        <th>${_('Date')}</th>
        <th>${_('IP')}</th>
    </tr>

    %for cnt,l in enumerate(c.users_log):
    <tr class="parity${cnt%2}">
        <td class="td-user">
            %if l.user is not None:
              ${base.gravatar_with_user(l.user.email)}
            %else:
              ${l.username}
            %endif
        </td>
        <td class="td-journalaction">
            % if l.version == l.VERSION_1:
                ${h.action_parser(l)[0]()}
            % else:
                ${h.literal(l.action)}
            % endif

            <div class="journal_action_params">
                % if l.version == l.VERSION_1:
                    ${h.literal(h.action_parser(l)[1]())}
                % endif
            </div>
        </td>
        <td>
            % if l.version == l.VERSION_2:
                ${l.action_data}
            % endif
        </td>
        <td class="td-componentname">
            %if l.repository is not None:
              ${h.link_to(l.repository.repo_name,h.url('summary_home',repo_name=l.repository.repo_name))}
            %else:
              ${l.repository_name}
            %endif
        </td>

        <td class="td-time">${h.format_date(l.action_date)}</td>
        <td class="td-ip">${l.user_ip}</td>
    </tr>
    %endfor
</table>

<div class="pagination-wh pagination-left">
${c.users_log.pager('$link_previous ~2~ $link_next')}
</div>
%else:
    ${_('No actions yet')}
%endif

<script type="text/javascript">
    $(function(){
        //because this is loaded on every pjax request, it must run only once
        //therefore the .one method
        $(document).on('pjax:complete',function(){
            show_more_event();
        });

        $(document).pjax('#user_log .pager_link', '#user_log');
    });
</script>

