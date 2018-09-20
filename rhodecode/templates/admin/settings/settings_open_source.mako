<%def name="show_license(license_data)">
    % if isinstance(license_data, dict):
        <a href="${license_data.get('url', "#noUrl")}">${license_data.get('spdxId') or license_data.get('fullName')}</a>
    % else:
        ${license_data}
    % endif
</%def>

<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Licenses of Third Party Packages')}</h3>
    </div>
    <div class="panel-body">
        <p>
            RhodeCode Enterprise uses various third party packages, many of them
            provided by the open source community.
        </p>
        % if c.opensource_licenses:
            <table class="rctable dl-settings">
                <thead>
                    <th>Product</th>
                    <th>License</th>
                </thead>
                % for lib in c.opensource_licenses:
                    <tr>
                        <td>${lib["name"]}</td>
                        <td>
                            <ol>
                            % if isinstance(lib["license"], list):
                                % for license_data in lib["license"]:
                                    <li>${show_license(license_data)}</li>
                                % endfor
                            % else:
                                    <% license_data = lib["license"] %>
                                    <li>${show_license(license_data)}</li>
                            % endif
                            </ol>
                        </td>
                    </tr>
                % endfor
            </table>
        % endif
    </div>
</div>


