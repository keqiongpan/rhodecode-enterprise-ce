## this is a dummy html file for partial rendering on server and sending
## generated output via ajax after comment submit
<%namespace name="comment" file="/changeset/changeset_file_comment.mako"/>
${comment.comment_block(c.co, inline=c.co.is_inline)}
