## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="title()">
    ${_('%s Commits') % c.repo_name} -
    r${c.commit_ranges[0].idx}:${h.short_id(c.commit_ranges[0].raw_id)}
    ...
    r${c.commit_ranges[-1].idx}:${h.short_id(c.commit_ranges[-1].raw_id)}
    ${_ungettext('(%s commit)','(%s commits)', len(c.commit_ranges)) % len(c.commit_ranges)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Commits')} -
    r${c.commit_ranges[0].idx}:${h.short_id(c.commit_ranges[0].raw_id)}
    ...
    r${c.commit_ranges[-1].idx}:${h.short_id(c.commit_ranges[-1].raw_id)}
    ${_ungettext('(%s commit)','(%s commits)', len(c.commit_ranges)) % len(c.commit_ranges)}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='commits')}
</%def>

<%def name="main()">

    <div class="summary changeset">
        <div class="summary-detail">
          <div class="summary-detail-header">
              <span class="breadcrumbs files_location">
                <h4>
                    ${_('Commit Range')}
                    <code>
                    r${c.commit_ranges[0].idx}:${h.short_id(c.commit_ranges[0].raw_id)}...r${c.commit_ranges[-1].idx}:${h.short_id(c.commit_ranges[-1].raw_id)}
                    </code>
                </h4>
              </span>
          </div>

          <div class="fieldset">
            <div class="left-label">
              ${_('Diff option')}:
            </div>
            <div class="right-content">
              <div class="btn btn-primary">
                <a href="${h.route_path('repo_compare',
                repo_name=c.repo_name,
                source_ref_type='rev',
                source_ref=getattr(c.commit_ranges[0].parents[0] if c.commit_ranges[0].parents else h.EmptyCommit(), 'raw_id'),
                target_ref_type='rev',
                target_ref=c.commit_ranges[-1].raw_id)}"
                >
                    ${_('Show combined compare')}
                </a>
              </div>
            </div>
          </div>

        </div> <!-- end summary-detail -->

    </div> <!-- end summary -->

    <div id="changeset_compare_view_content">
    <div class="pull-left">
      <div class="btn-group">
          <a
              class="btn"
              href="#"
              onclick="$('.compare_select').show();$('.compare_select_hidden').hide(); return false">
              ${_ungettext('Expand %s commit','Expand %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
          </a>
          <a
              class="btn"
              href="#"
              onclick="$('.compare_select').hide();$('.compare_select_hidden').show(); return false">
              ${_ungettext('Collapse %s commit','Collapse %s commits', len(c.commit_ranges)) % len(c.commit_ranges)}
          </a>
      </div>
    </div>
    ## Commit range generated below
    <%include file="../compare/compare_commits.mako"/>
    <div class="cs_files">
      <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>
      <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
      <%namespace name="diff_block" file="/changeset/diff_block.mako"/>
      ${cbdiffs.render_diffset_menu()}
      %for commit in c.commit_ranges:
        ${cbdiffs.render_diffset(
            diffset=c.changes[commit.raw_id],
            collapse_when_files_over=5,
            commit=commit,
         )}
        %endfor
    </div>
  </div>
</%def>
