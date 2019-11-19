## -*- coding: utf-8 -*-

<%inherit file="/base/base.mako"/>
<%namespace name="base" file="/base/base.mako"/>
<%namespace name="diff_block" file="/changeset/diff_block.mako"/>
<%namespace name="file_base" file="/files/base.mako"/>

<%def name="title()">
    ${_('{} Commit').format(c.repo_name)} - ${h.show_id(c.commit)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='commits')}
</%def>

<%def name="main()">
<script type="text/javascript">
    // TODO: marcink switch this to pyroutes
    AJAX_COMMENT_DELETE_URL = "${h.route_path('repo_commit_comment_delete',repo_name=c.repo_name,commit_id=c.commit.raw_id,comment_id='__COMMENT_ID__')}";
    templateContext.commit_data.commit_id = "${c.commit.raw_id}";
</script>

<div class="box">

  <div class="summary">

      <div class="fieldset">
        <div class="left-content">
          <%
              rc_user = h.discover_user(c.commit.author_email)
          %>
          <div class="left-content-avatar">
            ${base.gravatar(c.commit.author_email, 30, tooltip=(True if rc_user else False), user=rc_user)}
          </div>

          <div class="left-content-message">
          <div class="fieldset collapsable-content no-hide" data-toggle="summary-details">
            <div class="commit truncate-wrap">${h.urlify_commit_message(h.chop_at_smart(c.commit.message, '\n', suffix_if_chopped='...'), c.repo_name)}</div>
          </div>

          <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none">
            <div class="commit">${h.urlify_commit_message(c.commit.message,c.repo_name)}</div>
          </div>

          <div class="fieldset" data-toggle="summary-details">
            <div class="">
                <table>
                <tr class="file_author">

                    <td>
                        <span class="user commit-author">${h.link_to_user(rc_user or c.commit.author)}</span>
                        <span class="commit-date">- ${h.age_component(c.commit.date)}</span>
                    </td>

                    <td>
                    ## second cell for consistency with files
                    </td>
                </tr>
                </table>
            </div>
          </div>

        </div>
        </div>

          <div class="right-content">

          <div data-toggle="summary-details">
              <div class="tags tags-main">
                <code><a href="${h.route_path('repo_commit',repo_name=c.repo_name,commit_id=c.commit.raw_id)}">${h.show_id(c.commit)}</a></code>
                <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${c.commit.raw_id}" title="${_('Copy the full commit id')}"></i>
                ${file_base.refs(c.commit)}

                ## phase
                % if hasattr(c.commit, 'phase') and getattr(c.commit, 'phase') != 'public':
                    <span class="tag phase-${c.commit.phase} tooltip" title="${_('Commit phase')}">
                        <i class="icon-info"></i>${c.commit.phase}
                    </span>
                % endif

                ## obsolete commits
                % if getattr(c.commit, 'obsolete', False):
                    <span class="tag obsolete-${c.commit.obsolete} tooltip" title="${_('Evolve State')}">
                        ${_('obsolete')}
                    </span>
                % endif

                ## hidden commits
                % if getattr(c.commit, 'hidden', False):
                    <span class="tag hidden-${c.commit.hidden} tooltip" title="${_('Evolve State')}">
                        ${_('hidden')}
                    </span>
                % endif
              </div>

              %if c.statuses:
                  <div class="tag status-tag-${c.statuses[0]} pull-right">
                      <i class="icon-circle review-status-${c.statuses[0]}"></i>
                      <div class="pull-right">${h.commit_status_lbl(c.statuses[0])}</div>
                  </div>
              %endif

          </div>

        </div>
      </div>

      <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
        <div class="left-label-summary">
          <p>${_('Commit navigation')}:</p>
          <div class="right-label-summary">
              <span id="parent_link" class="tag tagtag">
                <a href="#parentCommit" title="${_('Parent Commit')}"><i class="icon-left icon-no-margin"></i>${_('parent')}</a>
              </span>

              <span id="child_link" class="tag tagtag">
                <a href="#childCommit" title="${_('Child Commit')}">${_('child')}<i class="icon-right icon-no-margin"></i></a>
              </span>
          </div>
        </div>
      </div>

      <div class="fieldset collapsable-content" data-toggle="summary-details" style="display: none;">
        <div class="left-label-summary">
          <p>${_('Diff options')}:</p>
          <div class="right-label-summary">
            <div class="diff-actions">
              <a href="${h.route_path('repo_commit_raw',repo_name=c.repo_name,commit_id=c.commit.raw_id)}">
                ${_('Raw Diff')}
              </a>
               |
              <a href="${h.route_path('repo_commit_patch',repo_name=c.repo_name,commit_id=c.commit.raw_id)}">
                ${_('Patch Diff')}
              </a>
               |
              <a href="${h.route_path('repo_commit_download',repo_name=c.repo_name,commit_id=c.commit.raw_id,_query=dict(diff='download'))}">
                ${_('Download Diff')}
              </a>
            </div>
          </div>
        </div>
      </div>

      <div class="clear-fix"></div>

      <div  class="btn-collapse" data-toggle="summary-details">
        ${_('Show More')}
      </div>

  </div>

  <div class="cs_files">
    <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>
    ${cbdiffs.render_diffset_menu(c.changes[c.commit.raw_id])}
    ${cbdiffs.render_diffset(
      c.changes[c.commit.raw_id], commit=c.commit, use_comments=True,inline_comments=c.inline_comments )}
  </div>

    ## template for inline comment form
    <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>

    ## comments heading with count
    <div class="comments-heading">
        <i class="icon-comment"></i>
        ${_('Comments')} ${len(c.comments)}
    </div>

    ## render comments
    ${comment.generate_comments(c.comments)}

    ## main comment form and it status
    ${comment.comments(h.route_path('repo_commit_comment_create', repo_name=c.repo_name, commit_id=c.commit.raw_id),
                       h.commit_status(c.rhodecode_db_repo, c.commit.raw_id))}
</div>

    ## FORM FOR MAKING JS ACTION AS CHANGESET COMMENTS
    <script type="text/javascript">

      $(document).ready(function() {

          var boxmax = parseInt($('#trimmed_message_box').css('max-height'), 10);
          if($('#trimmed_message_box').height() === boxmax){
              $('#message_expand').show();
          }

          $('#message_expand').on('click', function(e){
              $('#trimmed_message_box').css('max-height', 'none');
              $(this).hide();
          });

          $('.show-inline-comments').on('click', function(e){
              var boxid = $(this).attr('data-comment-id');
              var button = $(this);

              if(button.hasClass("comments-visible")) {
                $('#{0} .inline-comments'.format(boxid)).each(function(index){
                  $(this).hide();
                });
                button.removeClass("comments-visible");
              } else {
                $('#{0} .inline-comments'.format(boxid)).each(function(index){
                  $(this).show();
                });
                button.addClass("comments-visible");
              }
          });

          // next links
          $('#child_link').on('click', function(e){
              // fetch via ajax what is going to be the next link, if we have
              // >1 links show them to user to choose
              if(!$('#child_link').hasClass('disabled')){
                  $.ajax({
                    url: '${h.route_path('repo_commit_children',repo_name=c.repo_name, commit_id=c.commit.raw_id)}',
                    success: function(data) {
                      if(data.results.length === 0){
                          $('#child_link').html("${_('No Child Commits')}").addClass('disabled');
                      }
                      if(data.results.length === 1){
                          var commit = data.results[0];
                          window.location = pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': commit.raw_id});
                      }
                      else if(data.results.length === 2){
                          $('#child_link').addClass('disabled');
                          $('#child_link').addClass('double');

                          var _html = '';
                          _html +='<a title="__title__" href="__url__"><span class="tag branchtag"><i class="icon-code-fork"></i>__branch__</span> __rev__</a> '
                                  .replace('__branch__', data.results[0].branch)
                                  .replace('__rev__','r{0}:{1}'.format(data.results[0].revision, data.results[0].raw_id.substr(0,6)))
                                  .replace('__title__', data.results[0].message)
                                  .replace('__url__', pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': data.results[0].raw_id}));
                          _html +=' | ';
                          _html +='<a title="__title__" href="__url__"><span class="tag branchtag"><i class="icon-code-fork"></i>__branch__</span> __rev__</a> '
                                  .replace('__branch__', data.results[1].branch)
                                  .replace('__rev__','r{0}:{1}'.format(data.results[1].revision, data.results[1].raw_id.substr(0,6)))
                                  .replace('__title__', data.results[1].message)
                                  .replace('__url__', pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': data.results[1].raw_id}));
                          $('#child_link').html(_html);
                      }
                    }
                  });
                  e.preventDefault();
              }
          });

          // prev links
          $('#parent_link').on('click', function(e){
              // fetch via ajax what is going to be the next link, if we have
              // >1 links show them to user to choose
              if(!$('#parent_link').hasClass('disabled')){
                  $.ajax({
                    url: '${h.route_path("repo_commit_parents",repo_name=c.repo_name, commit_id=c.commit.raw_id)}',
                    success: function(data) {
                      if(data.results.length === 0){
                          $('#parent_link').html('${_('No Parent Commits')}').addClass('disabled');
                      }
                      if(data.results.length === 1){
                          var commit = data.results[0];
                          window.location = pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': commit.raw_id});
                      }
                      else if(data.results.length === 2){
                          $('#parent_link').addClass('disabled');
                          $('#parent_link').addClass('double');

                          var _html = '';
                          _html +='<a title="__title__" href="__url__"><span class="tag branchtag"><i class="icon-code-fork"></i>__branch__</span> __rev__</a>'
                                  .replace('__branch__', data.results[0].branch)
                                  .replace('__rev__','r{0}:{1}'.format(data.results[0].revision, data.results[0].raw_id.substr(0,6)))
                                  .replace('__title__', data.results[0].message)
                                  .replace('__url__', pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': data.results[0].raw_id}));
                          _html +=' | ';
                          _html +='<a title="__title__" href="__url__"><span class="tag branchtag"><i class="icon-code-fork"></i>__branch__</span> __rev__</a>'
                                  .replace('__branch__', data.results[1].branch)
                                  .replace('__rev__','r{0}:{1}'.format(data.results[1].revision, data.results[1].raw_id.substr(0,6)))
                                  .replace('__title__', data.results[1].message)
                                  .replace('__url__', pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': data.results[1].raw_id}));
                          $('#parent_link').html(_html);
                      }
                    }
                  });
                  e.preventDefault();
              }
          });

          // browse tree @ revision
          $('#files_link').on('click', function(e){
              window.location = '${h.route_path('repo_files:default_path',repo_name=c.repo_name, commit_id=c.commit.raw_id)}';
              e.preventDefault();
          });

      })
    </script>

</%def>
