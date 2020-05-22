# Example to trigger a CI call via an HTTP helper via post_push hook


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'repo_store_path': 'full path to where repositories are stored',
    'commit_ids': '',
    'hook_type': '',
    'user_agent': '',
})
def _push_hook(*args, **kwargs):
    """
    POST PUSH HOOK, this function will be executed after each push it's
    executed after the build-in hook that RhodeCode uses for logging pushes
    """

    from .helpers import http_call, extra_fields
    # returns list of dicts with key-val fetched from extra fields
    repo_extra_fields = extra_fields.run(**kwargs)

    endpoint_url = extra_fields.get_field(repo_extra_fields, key='endpoint_url', default='')
    if endpoint_url:
        data = {
            'some_key': 'val'
        }
        response = http_call.run(url=endpoint_url, json_data=data)
        return HookResponse(0, 'Called endpoint {}, with response {}'.format(endpoint_url, response))

    return HookResponse(0, '')
