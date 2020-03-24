## snippet for displaying issue tracker settings
## usage:
##    <%namespace name="its" file="/base/issue_tracker_settings.mako"/>
##    ${its.issue_tracker_settings_table(patterns, form_url, delete_url)}
##    ${its.issue_tracker_settings_test(test_url)}

<%def name="issue_tracker_settings_table(patterns, form_url, delete_url)">
<%
# Name/desc, pattern, issue prefix
examples = [
    (
    ' ',
    ' ',
    ' ',
    ' '
    ),

    (
    'Redmine',
    '(^#|\s#)(?P<issue_id>\d+)',
    'https://myissueserver.com/${repo}/issue/${issue_id}',
    ''
    ),

    (
    'Redmine - Alternative',
    '(?:issue-)(\d+)',
    'https://myissueserver.com/redmine/issue/${id}',
    ''
    ),

    (
    'Redmine - Wiki',
    '(?:wiki-)([a-zA-Z0-9]+)',
    'http://example.org/projects/${repo_name}/wiki/${id}',
    'wiki-'
    ),

    (
    'JIRA - All tickets',
    '(^|\s\w+-\d+)',
    'https://myjira.com/browse/${id}',
    ''
    ),

    (
    'JIRA - Project (JRA)',
    '(?:(^|\s)(?P<issue_id>(?:JRA-|JRA-)(?:\d+)))',
    'https://myjira.com/${issue_id}',
    ''
    ),

    (
    'Confluence WIKI',
    '(?:conf-)([A-Z0-9]+)',
    'https://example.atlassian.net/display/wiki/${id}/${repo_name}',
    'CONF-',
    ),

    (
    'Pivotal Tracker',
    '(?:pivot-)(?P<project_id>\d+)-(?P<story>\d+)',
    'https://www.pivotaltracker.com/s/projects/${project_id}/stories/${story}',
    'PIV-',
    ),

    (
    'Trello',
    '(?:trello-)(?P<card_id>[a-zA-Z0-9]+)',
    'https://trello.com/example.com/${card_id}',
    'TRELLO-',
    ),
]
%>

    <table class="rctable issuetracker">
      <tr>
          <th>${_('Description')}</th>
          <th>${_('Pattern')}</th>
          <th>${_('Url')}</th>
          <th>${_('Extra Prefix')}</th>
          <th ></th>
      </tr>
        % for name, pat, url, pref in examples:
        <tr class="it-examples" style="${'' if loop.index == 0 else 'display:none'}">
          <td class="td-issue-tracker-name issue-tracker-example">${name}</td>
          <td class="td-regex issue-tracker-example">${pat}</td>
          <td class="td-url issue-tracker-example">${url}</td>
          <td class="td-prefix issue-tracker-example">${pref}</td>
          <td>
              % if loop.index == 0:
              <a href="#showMore" onclick="$('.it-examples').toggle(); return false">${_('show examples')}</a>
              % else:
              <a href="#copyToInput" onclick="copyToInput(this, '${h.json.dumps(name)}', '${h.json.dumps(pat)}', '${h.json.dumps(url)}', '${h.json.dumps(pref)}'); return false">copy to input</a>
              % endif
          </td>
        </tr>
        % endfor

      %for uid, entry in patterns:
        <tr id="entry_${uid}">
                <td class="td-issue-tracker-name issuetracker_desc">
                    <span class="entry">
                        ${entry.desc}
                    </span>
                    <span class="edit">
                        ${h.text('new_pattern_description_'+uid, class_='medium-inline', value=entry.desc or '')}
                    </span>
                </td>
                <td class="td-issue-tracker-regex issuetracker_pat">
                    <span class="entry">
                        ${entry.pat}
                    </span>
                    <span class="edit">
                        ${h.text('new_pattern_pattern_'+uid, class_='medium-inline', value=entry.pat or '')}
                    </span>
                </td>
                <td class="td-url issuetracker_url">
                    <span class="entry">
                        ${entry.url}
                    </span>
                    <span class="edit">
                        ${h.text('new_pattern_url_'+uid, class_='medium-inline', value=entry.url or '')}
                    </span>
                </td>
                <td class="td-prefix issuetracker_pref">
                    <span class="entry">
                        ${entry.pref}
                    </span>
                    <span class="edit">
                        ${h.text('new_pattern_prefix_'+uid, class_='medium-inline', value=entry.pref or '')}
                    </span>
                </td>
                <td class="td-action">
                    <div  class="grid_edit">
                        <span class="entry">
                            <a class="edit_issuetracker_entry" href="">${_('Edit')}</a>
                        </span>
                        <span class="edit">
                            <input id="uid_${uid}" name="uid" type="hidden" value="${uid}">
                        </span>
                    </div>
                    <div  class="grid_delete">
                        <span class="entry">
                            <a class="btn btn-link btn-danger delete_issuetracker_entry" data-desc="${entry.desc}" data-uid="${uid}">
                                ${_('Delete')}
                            </a>
                        </span>
                        <span class="edit">
                            <a class="btn btn-link btn-danger edit_issuetracker_cancel" data-uid="${uid}">${_('Cancel')}</a>
                        </span>
                   </div>
                </td>
        </tr>
      %endfor
      <tr id="last-row"></tr>
    </table>
    <p>
      <a id="add_pattern" class="link">
          ${_('Add new')}
      </a>
    </p>

    <script type="text/javascript">
        var newEntryLabel = $('label[for="new_entry"]');

        var resetEntry = function() {
          newEntryLabel.text("${_('New Entry')}:");
        };

        var delete_pattern = function(entry) {
          if (confirm("${_('Confirm to remove this pattern:')} "+$(entry).data('desc'))) {
            $.ajax({
              type: "POST",
              url: "${delete_url}",
              data: {
                'csrf_token': CSRF_TOKEN,
                'uid':$(entry).data('uid')
              },
              success: function(){
                window.location.reload();
              },
              error: function(data, textStatus, errorThrown){
                  alert("Error while deleting entry.\nError code {0} ({1}). URL: {2}".format(data.status,data.statusText,$(entry)[0].url));
              }
            });
          }
        };

        $('.delete_issuetracker_entry').on('click', function(e){
          e.preventDefault();
          delete_pattern(this);
        });

        $('.edit_issuetracker_entry').on('click', function(e){
            e.preventDefault();
            $(this).parents('tr').addClass('editopen');
        });

        $('.edit_issuetracker_cancel').on('click', function(e){
            e.preventDefault();
            $(this).parents('tr').removeClass('editopen');
            // Reset to original value
            var uid = $(this).data('uid');
            $('#'+uid+' input').each(function(e) {
                this.value = this.defaultValue;
            });
        });

        $('input#reset').on('click', function(e) {
            resetEntry();
        });

        $('#add_pattern').on('click', function(e) {
            addNewPatternInput();
        });

        var copied = false;
        copyToInput = function (elem, name, pat, url, pref) {
            if (copied === false) {
                addNewPatternInput();
                copied = true;
            }
            $(elem).hide();
            var load = function(text){
                return text.replace(/["]/g, "")
            };
            $('#description_1').val(load(name));
            $('#pattern_1').val(load(pat));
            $('#url_1').val(load(url));
            $('#prefix_1').val(load(pref));

        }

    </script>    
</%def>

<%def name="issue_tracker_new_row()">
  <table id="add-row-tmpl" style="display: none;">
    <tbody>
    <tr class="new_pattern">
        <td class="td-issue-tracker-name issuetracker_desc">
          <span class="entry">
                <input class="medium-inline" id="description_##UUID##" name="new_pattern_description_##UUID##" value="##DESCRIPTION##" type="text">
          </span>
        </td>
        <td class="td-issue-tracker-regex issuetracker_pat">
          <span class="entry">
                    <input class="medium-inline" id="pattern_##UUID##" name="new_pattern_pattern_##UUID##" placeholder="Pattern" 
                    value="##PATTERN##" type="text">
          </span>
        </td>
        <td class="td-url issuetracker_url">
          <span class="entry">
                  <input class="medium-inline" id="url_##UUID##" name="new_pattern_url_##UUID##" placeholder="Url" value="##URL##" type="text">
          </span>
        </td>
        <td class="td-prefix issuetracker_pref">
            <span class="entry">
                  <input class="medium-inline" id="prefix_##UUID##" name="new_pattern_prefix_##UUID##" placeholder="Prefix" value="##PREFIX##" type="text"> 
            </span>
        </td>
        <td class="td-action">
        </td>
        <input id="uid_##UUID##" name="uid_##UUID##" type="hidden" value="">
    </tr>
    </tbody>
  </table>
</%def>

<%def name="issue_tracker_settings_test(test_url)">
    <div class="form-vertical">
        <div class="fields">
            <div class="field">
                <div class='textarea-full'>
                    <textarea id="test_pattern_data" rows="12">
This is an example text for testing issue tracker patterns.
This commit fixes ticket #451 and ticket #910.
Following tickets will get mentioned:
#123
#456
JRA-123
JRA-456
Open a pull request !101 to contribute !
Added tag v1.3.0 for commit 0f3b629be725

Add a test pattern here and hit preview to see the link.
                    </textarea>
                </div>
            </div>
        </div>
        <div class="test_pattern_preview">
            <div id="test_pattern" class="btn btn-small" >${_('Preview')}</div>
            <p>${_('Test Pattern Preview')}</p>
            <div id="test_pattern_result" style="white-space: pre-wrap"></div>
        </div>
    </div>

    <script type="text/javascript">
        $('#test_pattern').on('click', function(e) {
          $.ajax({
              type: "POST",
              url: "${test_url}",
              data: {
                'test_text': $('#test_pattern_data').val(),
                'csrf_token': CSRF_TOKEN
              },
              success: function(data){
                  $('#test_pattern_result').html(data);
                  tooltipActivate();
              },
              error: function(jqXHR, textStatus, errorThrown){
                  $('#test_pattern_result').html('Error: ' + errorThrown);
              }
          });
          $('#test_pattern_result').show();
        });
    </script>
</%def>


