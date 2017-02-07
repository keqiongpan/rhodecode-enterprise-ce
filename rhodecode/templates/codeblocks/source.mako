<%def name="render_line(line_num, tokens,
                        annotation=None,
                        bgcolor=None, show_annotation=None)">
    <%
    from rhodecode.lib.codeblocks import render_tokenstream
    # avoid module lookup for performance
    html_escape = h.html_escape
    %>
    <tr class="cb-line cb-line-fresh ${'cb-annotate' if show_annotation else ''}"
    %if annotation:
    data-revision="${annotation.revision}"
    %endif
    >

    % if annotation:
        % if show_annotation:
            <td class="cb-annotate-info tooltip"
                title="Author: ${annotation.author | entity}<br>Date: ${annotation.date}<br>Message: ${annotation.message | entity}"
            >
              ${h.gravatar_with_user(annotation.author, 16) | n}
              <div class="cb-annotate-message truncate-wrap">${h.chop_at_smart(annotation.message, '\n', suffix_if_chopped='...')}</div>
            </td>
            <td class="cb-annotate-message-spacer"></td>
            <td
              class="cb-annotate-revision"
              data-revision="${annotation.revision}"
              onclick="$('[data-revision=${annotation.revision}]').toggleClass('cb-line-fresh')"
              style="background: ${bgcolor}">
            <a class="cb-annotate" href="${h.url('changeset_home',repo_name=c.repo_name,revision=annotation.raw_id)}">
              r${annotation.revision}
            </a>
            </td>
        % else:
            <td></td>
            <td class="cb-annotate-message-spacer"></td>
            <td
              class="cb-annotate-revision"
              data-revision="${annotation.revision}"
              onclick="$('[data-revision=${annotation.revision}]').toggleClass('cb-line-fresh')"
              style="background: ${bgcolor}">
            </td>
        % endif
    % else:
        <td colspan="3"></td>
    % endif


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
  % for line_num, tokens in lines:
    ${render_line(line_num, tokens,
      bgcolor=color_hasher(annotation and annotation.raw_id or ''),
      annotation=annotation, show_annotation=loop.first
      )}
  % endfor

</%def>
