## -*- coding: utf-8 -*-
<%namespace name="base" file="/base/base.mako"/>

%if c.journal_day_aggreagate:
    %for day,items in c.journal_day_aggreagate:
     <div class="journal_day">${day}</div>
        % for user,entries in items:
            <div class="journal_container">
                ${base.gravatar(user.email if user else '', 30)}
                %if user:
                   <div class="journal_user user">${h.link_to_user(user.username)}</div>
                %else:
                    <div class="journal_user user deleted">${entries[0].username}</div>
                %endif
                <div class="journal_action_container">
                % for entry in entries:
                    <div class="journal_icon"> ${h.action_parser(request, entry)[2]()}</div>
                    <div class="journal_action">${h.action_parser(request, entry)[0]()}</div>
                    <div class="journal_repo">
                        <span class="journal_repo_name">
                        %if entry.repository is not None:
                          ${h.link_to(entry.repository.repo_name,
                                      h.route_path('repo_summary',repo_name=entry.repository.repo_name))}
                        %else:
                          ${entry.repository_name}
                        %endif
                        </span>
                    </div>
                    <div class="journal_action_params">${h.literal(h.action_parser(request, entry)[1]())}</div>
                    <div class="date">
                        ${h.age_component(entry.action_date, time_is_local=True)}
                    </div>
                %endfor
                </div>
            </div>
        %endfor
    %endfor

  <div class="pagination-wh pagination-left">
  ${c.journal_pager.render()}
  </div>

%else:
  <div>
      ${_('No entries yet')}
  </div>
%endif
