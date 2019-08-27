## -*- coding: utf-8 -*-
<%inherit file="/base/base.mako"/>

<%def name="robots()">
    %if c.gist.gist_type != 'public':
      <meta name="robots" content="noindex, nofollow">
    %else:
      ${parent.robots()}
    %endif
</%def>

<%def name="title()">
    ${_('Gist')} &middot; ${c.gist.gist_access_id}
    %if c.rhodecode_name:
        &middot; ${h.branding(c.rhodecode_name)}
    %endif
</%def>

<%def name="breadcrumbs_links()">
    ${_('Gist')} &middot; ${c.gist.gist_access_id}
</%def>

<%def name="menu_bar_nav()">
    ${self.menu_items(active='gists')}
</%def>

<%def name="main()">
<div class="box">
    <!-- box / title -->
    <div class="title">
        ${self.breadcrumbs()}
    </div>

    <div class="table">
        <div id="files_data">
            <div id="codeblock" class="codeblock">
                <div class="code-header">
                    <div class="gist_url">
                        <code>
                            ${c.gist.gist_url()} <span class="icon-clipboard clipboard-action" data-clipboard-text="${c.gist.gist_url()}" title="${_('Copy the url')}"></span>
                        </code>
                    </div>
                    <div class="stats">
                       %if c.is_super_admin or c.gist.gist_owner == c.rhodecode_user.user_id:
                        <div class="remove_gist">
                            ${h.secure_form(h.route_path('gist_delete', gist_id=c.gist.gist_access_id), request=request)}
                                ${h.submit('remove_gist', _('Delete'),class_="btn btn-mini btn-danger",onclick="return confirm('"+_('Confirm to delete this Gist')+"');")}
                            ${h.end_form()}
                        </div>
                       %endif
                        <div class="buttons">
                          ## only owner should see that
                          <a href="#copySource" onclick="return false;" class="btn btn-mini icon-clipboard clipboard-action" data-clipboard-text="${c.files[0].content}">${_('Copy content')}</a>

                          %if c.is_super_admin or c.gist.gist_owner == c.rhodecode_user.user_id:
                            ${h.link_to(_('Edit'), h.route_path('gist_edit', gist_id=c.gist.gist_access_id), class_="btn btn-mini")}
                          %endif
                          ${h.link_to(_('Show as Raw'), h.route_path('gist_show_formatted', gist_id=c.gist.gist_access_id, revision='tip', format='raw'), class_="btn btn-mini")}
                        </div>
                        <div class="left" >
                          %if c.gist.gist_type != 'public':
                            <span class="tag tag-ok disabled">${_('Private Gist')}</span>
                          %endif
                          <span> ${c.gist.gist_description}</span>
                           <span>${_('Expires')}:
                           %if c.gist.gist_expires == -1:
                             ${_('never')}
                           %else:
                              ${h.age_component(h.time_to_utcdatetime(c.gist.gist_expires))}
                          %endif
                          </span>

                       </div>
                    </div>

                    <div class="author">
                        <div title="${h.tooltip(c.file_last_commit.author)}">
                          ${self.gravatar_with_user(c.file_last_commit.author, 16)} - ${_('created')} ${h.age_component(c.file_last_commit.date)}
                        </div>

                    </div>
                    <div class="commit">${h.urlify_commit_message(c.file_last_commit.message, None)}</div>
                </div>

               ## iterate over the files
               % for file in c.files:
                <% renderer = c.render and h.renderer_from_filename(file.path, exclude=['.txt', '.TXT'])%>
                <!--
                <div id="${h.FID('G', file.path)}" class="stats" >
                    <a href="${c.gist.gist_url()}">¶</a>
                    <b >${file.path}</b>
                    <div>
                       ${h.link_to(_('Show as raw'), h.route_path('gist_show_formatted_path', gist_id=c.gist.gist_access_id, revision=file.commit.raw_id, format='raw', f_path=file.path), class_="btn btn-mini")}
                    </div>
                </div>
                -->
                <div class="code-body textarea text-area editor">
                    %if renderer:
                        ${h.render(file.content, renderer=renderer)}
                    %else:
                        ${h.pygmentize(file,linenos=True,anchorlinenos=True,lineanchors='L',cssclass="code-highlight")}
                    %endif
                </div>
               %endfor
            </div>
        </div>
    </div>


</div>
</%def>
