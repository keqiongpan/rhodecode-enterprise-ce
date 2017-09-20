## -*- coding: utf-8 -*-

<%inherit file="/base/base.mako"/>
<%namespace name="diff_block" file="/changeset/diff_block.mako"/>

<%def name="title()">
    ${_('%s Commit') % c.repo_name} - ${h.show_id(c.commit)}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='repositories')}
</%def>

<%def name="menu_bar_subnav()">
    ${self.repo_menu(active='changelog')}
</%def>

<%def name="main()">
<script>
    // TODO: marcink switch this to pyroutes
    AJAX_COMMENT_DELETE_URL = "${h.route_path('repo_commit_comment_delete',repo_name=c.repo_name,commit_id=c.commit.raw_id,comment_id='__COMMENT_ID__')}";
    templateContext.commit_data.commit_id = "${c.commit.raw_id}";
</script>
<div class="box">
    <div class="title">
        ${self.repo_page_title(c.rhodecode_db_repo)}
    </div>

  <div id="changeset_compare_view_content"  class="summary changeset">
    <div class="summary-detail">
      <div class="summary-detail-header">
          <span class="breadcrumbs files_location">
            <h4>${_('Commit')}
              <code>
                ${h.show_id(c.commit)}
                <i class="tooltip icon-clipboard clipboard-action" data-clipboard-text="${c.commit.raw_id}" title="${_('Copy the full commit id')}"></i>
                % if hasattr(c.commit, 'phase'):
                      <span class="tag phase-${c.commit.phase} tooltip" title="${_('Commit phase')}">${c.commit.phase}</span>
                % endif

                ## obsolete commits
                % if hasattr(c.commit, 'obsolete'):
                  % if c.commit.obsolete:
                      <span class="tag obsolete-${c.commit.obsolete} tooltip" title="${_('Evolve State')}">${_('obsolete')}</span>
                  % endif
                % endif

                ## hidden commits
                % if hasattr(c.commit, 'hidden'):
                  % if c.commit.hidden:
                      <span class="tag hidden-${c.commit.hidden} tooltip" title="${_('Evolve State')}">${_('hidden')}</span>
                  % endif
                % endif

              </code>
            </h4>
          </span>
          <div class="pull-right">
              <span id="parent_link">
                <a href="#parentCommit" title="${_('Parent Commit')}">${_('Parent')}</a>
              </span>
               |
              <span id="child_link">
                <a href="#childCommit" title="${_('Child Commit')}">${_('Child')}</a>
              </span>
          </div>
      </div>

      <div class="fieldset">
        <div class="left-label">
          ${_('Description')}:
        </div>
        <div class="right-content">
          <div id="trimmed_message_box" class="commit">${h.urlify_commit_message(c.commit.message,c.repo_name)}</div>
          <div id="message_expand" style="display:none;">
            ${_('Expand')}
          </div>
        </div>
      </div>

      %if c.statuses:
      <div class="fieldset">
        <div class="left-label">
          ${_('Commit status')}:
        </div>
        <div class="right-content">
          <div class="changeset-status-ico">
            <div class="${'flag_status %s' % c.statuses[0]} pull-left"></div>
          </div>
          <div title="${_('Commit status')}" class="changeset-status-lbl">[${h.commit_status_lbl(c.statuses[0])}]</div>
        </div>
      </div>
      %endif

      <div class="fieldset">
        <div class="left-label">
          ${_('References')}:
        </div>
        <div class="right-content">
          <div class="tags">

            %if c.commit.merge:
              <span class="mergetag tag">
               <i class="icon-merge"></i>${_('merge')}
              </span>
            %endif

            %if h.is_hg(c.rhodecode_repo):
              %for book in c.commit.bookmarks:
              <span class="booktag tag" title="${h.tooltip(_('Bookmark %s') % book)}">
                <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=c.commit.raw_id,_query=dict(at=book))}"><i class="icon-bookmark"></i>${h.shorter(book)}</a>
              </span>
              %endfor
            %endif

            %for tag in c.commit.tags:
             <span class="tagtag tag"  title="${h.tooltip(_('Tag %s') % tag)}">
              <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=c.commit.raw_id,_query=dict(at=tag))}"><i class="icon-tag"></i>${tag}</a>
             </span>
            %endfor

            %if c.commit.branch:
              <span class="branchtag tag" title="${h.tooltip(_('Branch %s') % c.commit.branch)}">
                <a href="${h.route_path('repo_files:default_path',repo_name=c.repo_name,commit_id=c.commit.raw_id,_query=dict(at=c.commit.branch))}"><i class="icon-code-fork"></i>${h.shorter(c.commit.branch)}</a>
              </span>
            %endif
            </div>
          </div>
        </div>

      <div class="fieldset">
        <div class="left-label">
          ${_('Diff options')}:
        </div>
        <div class="right-content">
            <div class="diff-actions">
              <a href="${h.route_path('repo_commit_raw',repo_name=c.repo_name,commit_id=c.commit.raw_id)}"  class="tooltip" title="${h.tooltip(_('Raw diff'))}">
                ${_('Raw Diff')}
              </a>
               |
              <a href="${h.route_path('repo_commit_patch',repo_name=c.repo_name,commit_id=c.commit.raw_id)}"  class="tooltip" title="${h.tooltip(_('Patch diff'))}">
                ${_('Patch Diff')}
              </a>
               |
              <a href="${h.route_path('repo_commit_download',repo_name=c.repo_name,commit_id=c.commit.raw_id,_query=dict(diff='download'))}" class="tooltip" title="${h.tooltip(_('Download diff'))}">
                ${_('Download Diff')}
              </a>
               |
              ${c.ignorews_url(request)}
               |
              ${c.context_url(request)}
            </div>
        </div>
      </div>

      <div class="fieldset">
        <div class="left-label">
          ${_('Comments')}:
        </div>
        <div class="right-content">
            <div class="comments-number">
                %if c.comments:
                    <a href="#comments">${_ungettext("%d Commit comment", "%d Commit comments", len(c.comments)) % len(c.comments)}</a>,
                %else:
                    ${_ungettext("%d Commit comment", "%d Commit comments", len(c.comments)) % len(c.comments)}
                %endif
                %if c.inline_cnt:
                    <a href="#" onclick="return Rhodecode.comments.nextComment();" id="inline-comments-counter">${_ungettext("%d Inline Comment", "%d Inline Comments", c.inline_cnt) % c.inline_cnt}</a>
                %else:
                    ${_ungettext("%d Inline Comment", "%d Inline Comments", c.inline_cnt) % c.inline_cnt}
                %endif
            </div>
        </div>
      </div>

      <div class="fieldset">
        <div class="left-label">
          ${_('Unresolved TODOs')}:
        </div>
        <div class="right-content">
            <div class="comments-number">
                % if c.unresolved_comments:
                    % for co in c.unresolved_comments:
                        <a class="permalink" href="#comment-${co.comment_id}" onclick="Rhodecode.comments.scrollToComment($('#comment-${co.comment_id}'))"> #${co.comment_id}</a>${'' if loop.last else ','}
                    % endfor
                % else:
                    ${_('There are no unresolved TODOs')}
                % endif
            </div>
        </div>
      </div>

    </div> <!-- end summary-detail -->

    <div id="commit-stats" class="sidebar-right">
      <div class="summary-detail-header">
        <h4 class="item">
          ${_('Author')}
        </h4>
      </div>
        <div class="sidebar-right-content">
            ${self.gravatar_with_user(c.commit.author)}
            <div class="user-inline-data">- ${h.age_component(c.commit.date)}</div>
        </div>
    </div><!-- end sidebar -->
  </div> <!-- end summary -->
  <div class="cs_files">
    <%namespace name="cbdiffs" file="/codeblocks/diffs.mako"/>
    ${cbdiffs.render_diffset_menu()}
    ${cbdiffs.render_diffset(
      c.changes[c.commit.raw_id], commit=c.commit, use_comments=True)}
  </div>

    ## template for inline comment form
    <%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>

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
                          _html +='<a title="__title__" href="__url__">__rev__</a> '
                                  .replace('__rev__','r{0}:{1}'.format(data.results[0].revision, data.results[0].raw_id.substr(0,6)))
                                  .replace('__title__', data.results[0].message)
                                  .replace('__url__', pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': data.results[0].raw_id}));
                          _html +=' | ';
                          _html +='<a title="__title__" href="__url__">__rev__</a> '
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
                          _html +='<a title="__title__" href="__url__">Parent __rev__</a>'
                                  .replace('__rev__','r{0}:{1}'.format(data.results[0].revision, data.results[0].raw_id.substr(0,6)))
                                  .replace('__title__', data.results[0].message)
                                  .replace('__url__', pyroutes.url('repo_commit', {'repo_name': '${c.repo_name}','commit_id': data.results[0].raw_id}));
                          _html +=' | ';
                          _html +='<a title="__title__" href="__url__">Parent __rev__</a>'
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

          if (location.hash) {
            var result = splitDelimitedHash(location.hash);
            var line = $('html').find(result.loc);
              if (line.length > 0){
                  offsetScroll(line, 70);
              }
          }

          // browse tree @ revision
          $('#files_link').on('click', function(e){
              window.location = '${h.route_path('repo_files:default_path',repo_name=c.repo_name, commit_id=c.commit.raw_id)}';
              e.preventDefault();
          });

          // inject comments into their proper positions
          var file_comments = $('.inline-comment-placeholder');
      })
    </script>

</%def>
