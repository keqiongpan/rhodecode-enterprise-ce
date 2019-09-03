
<table id="procList">
    <%
        def get_name(proc):
            if 'vcsserver.ini' in proc.cmd:
                return 'VCSServer'
            elif 'rhodecode.ini' in proc.cmd:
                return 'RhodeCode'
            return proc.name
    %>
    <tr>
        <td colspan="8">
            <span id="processTimeStamp">${h.format_date(h.datetime.now())}</span>
        </td>
    </tr>
    % for proc in c.gunicorn_processes:

        % if proc.children:
        <tr>
            <td>
                <code>
                ${proc.pid} - ${get_name(proc)}
                </code>
            </td>
            <td>
                <a href="#showCommand" onclick="$('#pid'+${proc.pid}).toggle();return false"> command </a>
                <code id="pid${proc.pid}" style="display: none">
                ${proc.cmd}
                </code>
            </td>
            <td></td>
            <td>
                RSS:${h.format_byte_size_binary(proc.mem_rss)}
            </td>
            <td>
                VMS:${h.format_byte_size_binary(proc.mem_vms)}
            </td>
            <td>
                AGE: ${h.age_component(h.time_to_utcdatetime(proc.create_time))}
            </td>
            <td>
                MASTER
                % if request.GET.get('dev'):
                    | <a href="#addWorker" onclick="addWorker(${proc.pid}); return false">ADD</a> | <a href="#removeWorker" onclick="removeWorker(${proc.pid}); return false">REMOVE</a>
                % endif
            </td>
        </tr>
        <% mem_sum = 0 %>
        % for proc_child in proc.children:
            % if proc_child:
            <tr>
                <td>
                    <code>
                      | ${proc_child.pid} - ${get_name(proc_child)}
                    </code>
                </td>
                <td>
                    <a href="#showCommand" onclick="$('#pid'+${proc_child.pid}).toggle();return false"> command </a>
                    <code id="pid${proc_child.pid}" style="display: none">
                    ${proc_child.cmd}
                    </code>
                </td>
                <td>
                    CPU: ${proc_child.cpu_percent} %
                </td>
                <td>
                    RSS:${h.format_byte_size_binary(proc_child.mem_rss)}
                    <% mem_sum += proc_child.mem_rss %>
                </td>
                <td>
                    VMS:${h.format_byte_size_binary(proc_child.mem_vms)}
                </td>
                <td>
                    AGE: ${h.age_component(h.time_to_utcdatetime(proc_child.create_time))}
                </td>
                <td>
                    <a href="#restartProcess" onclick="restart(this, ${proc_child.pid});return false">
                        restart
                    </a>
                </td>
            </tr>
            % endif
        % endfor
        <tr>
            <td colspan="2"><code>| total processes: ${len(proc.children)}</code></td>
            <td></td>
            <td><strong>RSS:${h.format_byte_size_binary(mem_sum)}</strong></td>
            <td></td>
        </tr>
        <tr><td> <code> -- </code> </td></tr>
        % endif
    % endfor
</table>
