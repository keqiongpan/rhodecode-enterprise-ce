## -*- coding: utf-8 -*-
##usage:
## <%namespace name="diff_block" file="/changeset/diff_block.mako"/>
## ${diff_block.diff_block_changeset_table(change)}
##
<%def name="changeset_message()">
    <h5>${_('The requested commit is too big and content was truncated.')} <a href="${h.url.current(fulldiff=1, **request.GET.mixed())}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a></h5>
</%def>
<%def name="file_message()">
    <h5>${_('The requested file is too big and its content is not shown.')} <a href="${h.url.current(fulldiff=1, **request.GET.mixed())}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a></h5>
</%def>

<%def name="diff_block_changeset_table(change)">
 <div class="diff-container" id="${'diff-container-%s' % (id(change))}">
  %for FID,(cs1, cs2, change, filenode_path, diff, stats, file_data) in change.iteritems():
    <div id="${h.FID('',filenode_path)}_target" ></div>
    <div id="${h.FID('',filenode_path)}" class="diffblock margined comm">
      <div class="code-body">
        <div class="full_f_path" path="${h.safe_unicode(filenode_path)}" style="display: none"></div>
        ${diff|n}
          % if file_data["is_limited_diff"]:
            % if file_data["exceeds_limit"]:
                ${self.file_message()}
              % else:
                <h5>${_('Diff was truncated. File content available only in full diff.')} <a href="${h.url.current(fulldiff=1, **request.GET.mixed())}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a></h5>
            % endif
          % endif
      </div>
    </div>
  %endfor
  </div>
</%def>

<%def name="diff_block_simple(change)">
 <div class="diff-container" id="${'diff-container-%s' % (id(change))}">
  %for op,filenode_path,diff,file_data in change:
    <div id="${h.FID('',filenode_path)}_target" ></div>
    <div id="${h.FID('',filenode_path)}" class="diffblock margined comm" >
        <div class="code-body">
            <div class="full_f_path" path="${h.safe_unicode(filenode_path)}" style="display: none;"></div>
            ${diff|n}
           % if file_data["is_limited_diff"]:
              % if file_data["exceeds_limit"]:
                  ${self.file_message()}
                % else:
                  <h5>${_('Diff was truncated. File content available only in full diff.')} <a href="${h.url.current(fulldiff=1, **request.GET.mixed())}" onclick="return confirm('${_("Showing a big diff might take some time and resources, continue?")}')">${_('Show full diff')}</a></h5>
                % endif
              % endif
        </div>
    </div>
  %endfor
  </div>
</%def>


<%def name="diff_summary_text(changed_files, lines_added, lines_deleted, limited_diff=False)">
    % if limited_diff:
        ${_ungettext('%(num)s file changed', '%(num)s files changed', changed_files) % {'num': changed_files}}
    % else:
        ${_ungettext('%(num)s file changed: %(linesadd)s inserted, ''%(linesdel)s deleted',
                    '%(num)s files changed: %(linesadd)s inserted, %(linesdel)s deleted', changed_files) % {'num': changed_files, 'linesadd': lines_added, 'linesdel': lines_deleted}}
    %endif
</%def>

