<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">${_('Strip')}</h3>
    </div>
    <div class="panel-body">
        %if c.repo_info.repo_type != 'svn':
            <p>
               <h4>${_('Please provide up to %s commits commits to strip')%c.strip_limit}</h4>
            </p>
            <p>
                ${_('In the first step commits will be verified for existance in the repository')}. </br>
                ${_('In the second step, correct commits will be available for stripping')}.
            </p>
            ${h.secure_form(h.route_path('strip_check', repo_name=c.repo_info.repo_name), method='post')}
                <div id="change_body" class="field">
                    <div id="box-1" class="inputx locked_input">
                        <input class="text" id="changeset_id-1" name="changeset_id-1"  size="59"
                              placeholder="${_('Enter full 40 character commit sha')}"  type="text" value="">
                                        <div id = "plus_icon-1" class="btn btn-default plus_input_button">
                                            <i class="icon-plus" onclick="addNew(1);return false">${_('Add another commit')}</i>
                                        </div>
                    </div>
                </div>
            <div id="results" style="display:none; padding: 10px 0px;"></div>
                <div class="buttons">
                    <button class="btn btn-small btn-primary" onclick="check_changsets();return false">
                   ${_('Check commits')}
                   </button>
                </div>
                <div id="results" style="display:none; padding: 10px 0px;"></div>

            ${h.end_form()}
        %else:
            <p>
               <h4>${_('Sorry this functionality is not available for SVN repository')}</h4>
            </p>


        %endif

    </div>
</div>


<script>
var plus_leaf = 1;

addNew = function(number){
    if (number >= ${c.strip_limit}){
        return;
    }
    var minus = '<i id="i_minus_icon-'+(number+1)+'" class="icon-minus" onclick="delOld('+(number+1)+');return false">${_('Remove')}</i>';
    $('#plus_icon-'+number).detach();
    number++;
    var input = '<div id="box-'+number+'" class="inputx locked_input">'+
               '<input class="text" id="changeset_id-'+number+'" name="changeset_id-'+number+'"  size="59" type="text" value="">'+
                '<div  id="plus_icon-'+number+'" class="btn btn-default plus_input_button">'+
                   '<i id="i_plus_icon-'+(number)+'" class="icon-plus" onclick="addNew('+number+');return false">${_('Add another commit')}</i>'+
               '</div>'+
                '<div  id="minus_icon-'+number+'" class="btn btn-default minus_input_button">'+
                minus +
               '</div>' +
            '</div>';
    $('#change_body').append(input);
    plus_leaf++;
}

function re_index(number){
    for(var i=number;i<=plus_leaf;i++){
        var check = $('#box-'+i);
        if (check.length == 0){
            var change = $('#box-'+(i+1));

            change.attr('id','box-'+i);
            var plus = $('#plus_icon-'+(i+1));
            var i_plus = $('#i_plus_icon-'+(i+1));
            if (plus.length != 0){
                plus.attr('id','plus_icon-'+i);
                i_plus.attr('id','i_plus_icon-'+i);
                i_plus.attr('onclick','addNew('+i+');return false');
                plus_leaf--;
            }
            var minus = $('#minus_icon-'+(i+1));
            var i_minus = $('#i_minus_icon-'+(i+1));
            minus.attr('id','minus_icon-'+i);
            i_minus.attr('id','i_minus_icon-'+i);
            i_minus.attr('onclick','delOld('+i+');return false');
        }
    }
}

delOld = function(number){
    $('#box-'+number).remove();
    number = number - 1;
    var box = $('#box-'+number);
    var plus =  '<div  id="plus_icon-'+number+'" class="btn btn-default plus_input_button">'+
            '<i id="i_plus_icon-'+number+'" class="icon-plus" onclick="addNew('+number +');return false">${_('Add another commit')}</i></div>';
    var minus = $('#minus_icon-'+number);
    if(number +1 == plus_leaf){
        minus.detach();
        box.append(plus);
        box.append(minus);
    }
    re_index(number+1);

}

var result_data;

check_changsets = function() {
    var postData = $('form').serialize();
    $('#results').show();
    $('#results').html('<h4>${_('Checking commits')}...</h4>');
    var url = "${h.route_path('strip_check', repo_name=c.repo_info.repo_name)}";
    var btn = $('button');
    btn.attr('disabled', 'disabled');
    btn.addClass('disabled');

    var success = function (data) {
        result_data = {};
        var i = 0;
        result ='';
        $.each(data, function(index, value){
            i= index;
            var box = $('#box-'+index);
            if (value.rev){
                result_data[index] = JSON.stringify(value);
                msg = '${_("author")}: ' + value.author + ' ${_("comment")}: ' + value.comment;
                result += '<h4>' +value.rev+ '${_(' commit verified positive')}</br> '+ msg + '</h4>';
            }
            else{
                result += '<h4>' +value.commit+ '${_('commit verified negative')}' + '</h4>';
            }
            box.remove();
        });
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

strip = function(){
    var url = "${h.route_path('strip_execute', repo_name=c.repo_info.repo_name)}";
    var success = function(data){
        result = '';
        $.each(data, function(index, value){
             if(data[index]){
                 result += '<h4>' +index+ '${_(' commit striped successful')}' + '</h4>';
             }
             else{
                 result += '<h4>' +index+ '${_(' commit striped failed')}' + '</h4>';
             }
        });
        $('#results').html(result);

    };
    ajaxPOST(url, result_data, success, null);
    var btn = $('button');
    btn.attr('disabled', 'disabled');
    btn.addClass('disabled');

};
</script>
