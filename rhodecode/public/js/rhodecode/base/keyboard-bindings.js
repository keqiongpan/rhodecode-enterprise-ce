// Global keyboard bindings

function setRCMouseBindings(repoName, repoLandingRev) {

    /** custom callback for supressing mousetrap from firing */
    Mousetrap.stopCallback = function(e, element) {
        // if the element has the class "mousetrap" then no need to stop
        if ((' ' + element.className + ' ').indexOf(' mousetrap ') > -1) {
            return false;
        }

        // stop for input, select, and textarea
        return element.tagName == 'INPUT' || element.tagName == 'SELECT' || element.tagName == 'TEXTAREA' || element.isContentEditable;
    };

    // general help "?"
    Mousetrap.bind(['?'], function(e) {
        $('#help_kb').modal({});
    });

    // / open the quick filter
    Mousetrap.bind(['/'], function(e) {
        $('#main_filter').get(0).focus();

        // return false to prevent default browser behavior
        // and stop event from bubbling
        return false;
    });

    // ctrl/command+b, show the the main bar
    Mousetrap.bind(['command+b', 'ctrl+b'], function(e) {
        var $headerInner = $('#header-inner'),
            $content = $('#content');
        if ($headerInner.hasClass('hover') && $content.hasClass('hover')) {
            $headerInner.removeClass('hover');
            $content.removeClass('hover');
        } else {
            $headerInner.addClass('hover');
            $content.addClass('hover');
        }
        return false;
    });

    // general nav g + action
    Mousetrap.bind(['g h'], function(e) {
        window.location = pyroutes.url('home');
    });
    Mousetrap.bind(['g g'], function(e) {
        window.location = pyroutes.url('gists_show', {'private': 1});
    });
    Mousetrap.bind(['g G'], function(e) {
        window.location = pyroutes.url('gists_show', {'public': 1});
    });

    Mousetrap.bind(['g 0'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 0});
    });
    Mousetrap.bind(['g 1'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 1});
    });
    Mousetrap.bind(['g 2'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 2});
    });
    Mousetrap.bind(['g 3'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 3});
    });
    Mousetrap.bind(['g 4'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 4});
    });
    Mousetrap.bind(['g 5'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 5});
    });
    Mousetrap.bind(['g 6'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 6});
    });
    Mousetrap.bind(['g 7'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 7});
    });
    Mousetrap.bind(['g 8'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 8});
    });
    Mousetrap.bind(['g 9'], function(e) {
        window.location = pyroutes.url('my_account_goto_bookmark', {'bookmark_id': 9});
    });

    Mousetrap.bind(['n g'], function(e) {
        window.location = pyroutes.url('gists_new');
    });
    Mousetrap.bind(['n r'], function(e) {
        window.location = pyroutes.url('repo_new');
    });

    if (repoName && repoName !== '') {
        // nav in repo context
        Mousetrap.bind(['g s'], function(e) {
            window.location = pyroutes.url(
                'repo_summary', {'repo_name': repoName});
        });
        Mousetrap.bind(['g c'], function(e) {
            window.location = pyroutes.url(
                'repo_commits', {'repo_name': repoName});
        });
        Mousetrap.bind(['g F'], function(e) {
            window.location = pyroutes.url(
                'repo_files',
                {
                    'repo_name': repoName,
                    'commit_id': repoLandingRev,
                    'f_path': '',
                    'search': '1'
                });
        });
        Mousetrap.bind(['g f'], function(e) {
            window.location = pyroutes.url(
                'repo_files',
                {
                    'repo_name': repoName,
                    'commit_id': repoLandingRev,
                    'f_path': ''
                });
        });
        Mousetrap.bind(['g o'], function(e) {
            window.location = pyroutes.url(
                'edit_repo', {'repo_name': repoName});
        });
        Mousetrap.bind(['g O'], function(e) {
            window.location = pyroutes.url(
                'edit_repo_perms', {'repo_name': repoName});
        });
    }
}

setRCMouseBindings(templateContext.repo_name, templateContext.repo_landing_commit);
