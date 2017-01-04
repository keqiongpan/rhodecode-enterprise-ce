<%def name="render_line(line_num, tokens,
                        annotation=None,
                        bgcolor=None)">
    <%
    from rhodecode.lib.codeblocks import render_tokenstream
    # avoid module lookup for performance
    html_escape = h.html_escape
    %>
    <tr class="cb-line cb-line-fresh"
    %if annotation:
    data-revision="${annotation.revision}"
    %endif
    >
    <td class="cb-lineno" id="L${line_num}">
      <a data-line-no="${line_num}" href="#L${line_num}"></a>
    </td>
    <td class="cb-content cb-content-fresh"
    %if bgcolor:
    style="background: ${bgcolor}"
    %endif
    >
    ## newline at end is necessary for highlight to work when line is empty
    ## and for copy pasting code to work as expected
      <span class="cb-code">${render_tokenstream(tokens)|n}${'\n'}</span>
    </td>
  </tr>
</%def>

<%def name="render_annotation_lines(annotation, lines, color_hasher)">
  <%
  rowspan = len(lines) + 1 # span the line's <tr> and annotation <tr>
  %>
  %if not annotation:
  <tr class="cb-annotate">
    <td class="cb-annotate-message" rowspan="${rowspan}"></td>
    <td class="cb-annotate-revision" rowspan="${rowspan}"></td>
  </tr>
  %else:
  <tr class="cb-annotate">
    <td class="cb-annotate-info tooltip"
        rowspan="${rowspan}"
        title="Author: ${annotation.author | entity}<br>Date: ${annotation.date}<br>Message: ${annotation.message | entity}"
    >
      ${h.gravatar_with_user(annotation.author, 16) | n}
      <strong class="cb-annotate-message">${h.truncate(annotation.message, len(lines) * 30)}</strong>
    </td>
    <td
      class="cb-annotate-revision"
      rowspan="${rowspan}"
      data-revision="${annotation.revision}"
      onclick="$('[data-revision=${annotation.revision}]').toggleClass('cb-line-fresh')"
      style="background: ${color_hasher(annotation.raw_id)}">
    <a href="${h.url('changeset_home',repo_name=c.repo_name,revision=annotation.raw_id)}">
      r${annotation.revision}
    </a>
    </td>
  </tr>
  %endif

  %for line_num, tokens in lines:
    ${render_line(line_num, tokens,
      bgcolor=color_hasher(annotation and annotation.raw_id or ''),
      annotation=annotation,
      )}
  %endfor
</%def>
