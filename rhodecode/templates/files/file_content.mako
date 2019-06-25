<%namespace name="sourceblock" file="/codeblocks/source.mako"/>

<%def name="render_lines(lines)">
<table class="cb codehilite">
    %for line_num, tokens in enumerate(lines, 1):
        ${sourceblock.render_line(line_num, tokens)}
    %endfor
</table>
</%def>
