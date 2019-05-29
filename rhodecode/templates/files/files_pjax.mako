<%def name="title(*args)">
    ${_('{} Files').format(c.repo_name)}
    %if hasattr(c,'file'):
        &middot; ${(h.safe_unicode(c.file.path) or '\\')}
    %endif

    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<div>

    <div class="summary-detail">
        <div class="summary-detail-header">

        </div><!--end summary-detail-header-->

        % if c.file.is_submodule():
            <span class="submodule-dir">Submodule ${h.escape(c.file.name)}</span>
        % elif c.file.is_dir():
            <%include file='files_tree_header.mako'/>
        % else:
            <%include file='files_source_header.mako'/>
        % endif

    </div> <!--end summary-detail-->
    % if c.file.is_dir():
        <%include file='files_browser.mako'/>
    % else:
        <%include file='files_source.mako'/>
    % endif

</div>
