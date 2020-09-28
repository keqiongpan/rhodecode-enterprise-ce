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

<%def name="breadcrumbs_links()"></%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='commits')}
</%def>

<%def name="main()">

    <div class="box">
        <div class="summary changeset">
            <div class="summary-detail">
              <div class="summary-detail-header">
                  <span class="breadcrumbs files_location">
                    <h4>
                        ${_('Commit Range')}
                    </h4>
                  </span>

                  <div class="clear-fix"></div>
              </div>

              <div class="fieldset">
                <div class="left-label-summary">
                    <p class="spacing">${_('Range')}:</p>
                    <div class="right-label-summary">
                        <div class="code-header" >
                            <div class="compare_header">
                                <code class="fieldset-text-line">
                                r${c.commit_ranges[0].idx}:${h.short_id(c.commit_ranges[0].raw_id)}
                                ...
                                r${c.commit_ranges[-1].idx}:${h.short_id(c.commit_ranges[-1].raw_id)}
                                ${_ungettext('(%s commit)','(%s commits)', len(c.commit_ranges)) % len(c.commit_ranges)}
                                </code>
                            </div>
                        </div>
                    </div>
                </div>
              </div>

              <div class="fieldset">
                <div class="left-label-summary">
                    <p class="spacing">${_('Diff Option')}:</p>
                    <div class="right-label-summary">
                        <div class="code-header" >
                            <div class="compare_header">
                                <a class="btn btn-primary" href="${h.route_path('repo_compare',
                                repo_name=c.repo_name,
                                source_ref_type='rev',
                                source_ref=getattr(c.commit_ranges[0].parents[0] if c.commit_ranges[0].parents else h.EmptyCommit(), 'raw_id'),
                                target_ref_type='rev',
                                target_ref=c.commit_ranges[-1].raw_id)}"
                                >
                                    ${_('Show combined diff')}
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
              </div>

              <div class="clear-fix"></div>
            </div> <!-- end summary-detail -->
        </div> <!-- end summary -->

        <div id="changeset_compare_view_content">
    <div class="pull-left">
      <div class="btn-group">
          <a class="${('collapsed' if c.collapse_all_commits else '')}" href="#expand-commits" onclick="toggleCommitExpand(this); return false" data-toggle-commits-cnt=${len(c.commit_ranges)} >
              % if c.collapse_all_commits:
                <i class="icon-plus-squared-alt icon-no-margin"></i>
                ${_ungettext('Expand {} commit', 'Expand {} commits', len(c.commit_ranges)).format(len(c.commit_ranges))}
              % else:
                <i class="icon-minus-squared-alt icon-no-margin"></i>
                ${_ungettext('Collapse {} commit', 'Collapse {} commits', len(c.commit_ranges)).format(len(c.commit_ranges))}
              % endif
          </a>
      </div>
    </div>
    ## Commit range generated below
    <%include file="../compare/compare_commits.mako"/>
    <div class="cs_files">
      <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>
      <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
      <%namespace name="diff_block" file="/changeset/diff_block.mako"/>

      %for commit in c.commit_ranges:
        ## commit range header for each individual diff
        <h3>
            <a class="tooltip revision" title="${h.tooltip(commit.message)}" href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=commit.raw_id)}">${('r%s:%s' % (commit.idx,h.short_id(commit.raw_id)))}</a>
        </h3>

        ${cbdiffs.render_diffset_menu(c.changes[commit.raw_id])}
        ${cbdiffs.render_diffset(
            diffset=c.changes[commit.raw_id],
            collapse_when_files_over=5,
            commit=commit,
         )}
        %endfor
    </div>
  </div>
    </div>

</%def>
