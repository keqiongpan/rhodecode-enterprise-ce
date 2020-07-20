<%namespace name="base" file="/base/base.mako"/>

<%
    active_pattern_entries = h.get_active_pattern_entries(getattr(c, 'repo_name', None))
%>

## NOTE, inline styles are here to override the default rendering of
## the swal JS dialog which this template is displayed

<div style="text-align: left;">

    <div style="border-bottom: 1px solid #dbd9da; padding-bottom: 5px; height: 20px">

        <div class="pull-left">
            ${base.gravatar_with_user(c.comment_history.author.email, 16, tooltip=True)}
        </div>

        <div class="pull-right">
            <code>edited: ${h.age_component(c.comment_history.created_on)}</code>
        </div>

    </div>

    <div style="margin: 5px 0px">
        <code>comment body at v${c.comment_history.version}:</code>
    </div>
    <div class="text" style="padding-top: 20px; border: 1px solid #dbd9da">
      ${h.render(c.comment_history.text, renderer=c.comment_history.comment.renderer, mentions=True, repo_name=getattr(c, 'repo_name', None), active_pattern_entries=active_pattern_entries)}
    </div>

</div>