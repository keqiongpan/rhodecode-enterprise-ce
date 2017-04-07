## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>


<div class="panel panel-default">
    <div class="panel-heading">
      <h3 class="panel-title">${_('User Audit Logs')} -
      ${_ungettext('%s entry', '%s entries', c.user_log.item_count) % (c.user_log.item_count)}
      </h3>
    </div>
    <div class="panel-body">

        ${h.form(None, id_="filter_form", method="get")}
            <input class="q_filter_box ${'' if c.filter_term else 'initial'}" id="j_filter" size="15" type="text" name="filter" value="${c.filter_term or ''}" placeholder="${_('audit filter...')}"/>
            <input type='submit' value="${_('filter')}" class="btn" />
        ${h.end_form()}
        <p class="tooltip filterexample" style="position: inherit" title="${h.tooltip(h.journal_filter_help())}">${_('Example Queries')}</p>

        % if c.user_log:
            <table class="rctable admin_log">
                <tr>
                    <th>${_('Username')}</th>
                    <th>${_('Action')}</th>
                    <th>${_('Repository')}</th>
                    <th>${_('Date')}</th>
                    <th>${_('From IP')}</th>
                </tr>

                %for cnt,l in enumerate(c.user_log):
                <tr class="parity${cnt%2}">
                    <td class="td-user">
                        %if l.user is not None:
                          ${base.gravatar_with_user(l.user.email)}
                        %else:
                          ${l.username}
                        %endif
                    </td>
                    <td class="td-journalaction">${h.action_parser(l)[0]()}
                        <div class="journal_action_params">
                            ${h.literal(h.action_parser(l)[1]())}
                        </div>
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
            ${c.user_log.pager('$link_previous ~2~ $link_next')}
            </div>
        % else:
            ${_('No actions yet')}
        % endif

    </div>
</div>
