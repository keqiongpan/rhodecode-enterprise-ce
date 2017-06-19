<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Strip commits from repository')}</h3>
    </div>
    <div class="panel-body">
        %if c.repo_info.repo_type != 'svn':
            <h4>${_('Please provide up to %d commits commits to strip') % c.strip_limit}</h4>
            <p>
                ${_('In the first step commits will be verified for existance in the repository')}. </br>
                ${_('In the second step, correct commits will be available for stripping')}.
            </p>
            ${h.secure_form(h.route_path('strip_check', repo_name=c.repo_info.repo_name), method='post')}
                <div id="change_body" class="field">
                    <div id="box-1" class="inputx locked_input">
                        <input class="text" id="changeset_id-1" name="changeset_id-1" size="59"
                              placeholder="${_('Enter full 40 character commit sha')}" type="text" value="">
                        <div id="plus_icon-1" class="btn btn-default plus_input_button" onclick="addNew(1);return false">
                            <i class="icon-plus">${_('Add another commit')}</i>
                        </div>
                    </div>
                </div>

                <div id="results" style="display:none; padding: 10px 0px;"></div>

                <div class="buttons">
                   <button id="strip_action" class="btn btn-small btn-primary" onclick="checkCommits();return false">
                   ${_('Check commits')}
                   </button>
                </div>

            ${h.end_form()}
        %else:
           <h4>${_('Sorry this functionality is not available for SVN repository')}</h4>
        %endif
    </div>
</div>


<script>
var plus_leaf = 1;

addNew = function(number){
    if (number >= ${c.strip_limit}){
        return;
    }
    var minus = '<i class="icon-minus">${_('Remove')}</i>';
    $('#plus_icon-'+number).detach();
    number++;

    var input = '<div id="box-'+number+'" class="inputx locked_input">'+
               '<input class="text" id="changeset_id-'+number+'" name="changeset_id-'+number+'"  size="59" type="text" value=""' +
            'placeholder="${_('Enter full 40 character commit sha')}">'+
               '<div  id="plus_icon-'+number+'" class="btn btn-default plus_input_button" onclick="addNew('+number+');return false">'+
                   '<i class="icon-plus">${_('Add another commit')}</i>'+
               '</div>'+
               '<div  id="minus_icon-'+number+'" class="btn btn-default minus_input_button" onclick="delOld('+(number)+');return false">'+
                minus +
               '</div>' +
            '</div>';
    $('#change_body').append(input);
    plus_leaf++;
};

reIndex = function(number){
    for(var i=number;i<=plus_leaf;i++){
        var check = $('#box-'+i);
        if (check.length == 0){
            var change = $('#box-'+(i+1));
            change.attr('id','box-'+i);
            var plus = $('#plus_icon-'+(i+1));

            if (plus.length != 0){
                plus.attr('id','plus_icon-'+i);
                plus.attr('onclick','addNew('+i+');return false');
                plus_leaf--;
            }
            var minus = $('#minus_icon-'+(i+1));

            minus.attr('id','minus_icon-'+i);

            minus.attr('onclick','delOld('+i+');re' +
            'turn false');
            var input = $('input#changeset_id-'+(i+1));
            input.attr('name','changeset_id-'+i);
            input.attr('id','changeset_id-'+i);
        }
    }
};

delOld = function(number){
    $('#box-'+number).remove();
    number = number - 1;
    var box = $('#box-'+number);
    var plus =  '<div  id="plus_icon-'+number+'" class="btn btn-default plus_input_button" onclick="addNew('+number +');return false">'+
            '<i id="i_plus_icon-'+number+'" class="icon-plus">${_('Add another commit')}</i></div>';
    var minus = $('#minus_icon-'+number);
    if(number +1 == plus_leaf){
        minus.detach();
        box.append(plus);
        box.append(minus);
        plus_leaf --;
    }
    reIndex(number+1);

};

var resultData = {
    'csrf_token': CSRF_TOKEN
};

checkCommits = function() {
    var postData = $('form').serialize();
    $('#results').show();
    $('#results').html('<h4>${_('Checking commits')}...</h4>');
    var url = "${h.route_path('strip_check', repo_name=c.repo_info.repo_name)}";
    var btn = $('#strip_action');
    btn.attr('disabled', 'disabled');
    btn.addClass('disabled');

    var success = function (data) {
        resultData = {
            'csrf_token': CSRF_TOKEN
        };
        var i = 0;
        var result = '<ol>';
        $.each(data, function(index, value){
            i= index;
            var box = $('#box-'+index);
            if (value.rev){
                resultData[index] = JSON.stringify(value);

                var verifiedHtml = (
                        '<li style="line-height:1.2em">' +
                            '<code>{0}</code>' +
                            '{1}' +
                            '<div style="white-space:pre">' +
                            'author: {2}\n' +
                            'description: {3}' +
                            '</div>' +
                        '</li>').format(
                            value.rev,
                            "${_(' commit verified positive')}",
                            value.author, value.comment
                            );
                result += verifiedHtml;
            }
            else {
                var verifiedHtml = (
                        '<li style="line-height:1.2em">' +
                            '<code><strike>{0}</strike></code>' +
                            '{1}' +
                        '</li>').format(
                            value.commit,
                            "${_(' commit verified negative')}"
                            );
                result += verifiedHtml;
            }
            box.remove();
        });
        result += '</ol>';
        var box = $('#box-'+(parseInt(i)+1));
        box.remove();
        $('#results').html(result);
    };

    btn.html('Strip');
    btn.removeAttr('disabled');
    btn.removeClass('disabled');
    btn.attr('onclick','strip();return false;');
    ajaxPOST(url, postData, success, null);
};

strip = function() {
    var url = "${h.route_path('strip_execute', repo_name=c.repo_info.repo_name)}";
    var success = function(data) {
        var result = '<h4>Strip executed</h4><ol>';
        $.each(data, function(index, value){
             if(data[index]) {
                 result += '<li><code>' +index+ '</code> ${_(' commit striped successfully')}' + '</li>';
             }
             else {
                 result += '<li><code>' +index+ '</code> ${_(' commit strip failed')}' + '</li>';
             }
        });
        if ($.isEmptyObject(data)) {
            result += '<li>Nothing done...</li>'
        }
        result += '</ol>';
        $('#results').html(result);

    };
    ajaxPOST(url, resultData, success, null);
    var btn = $('#strip_action');
    btn.remove();

};
</script>
