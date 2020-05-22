# Example to trigger a CI call action on specific comment text, e.g chatops and ci
# rebuild on mention of ci bot

@has_kwargs({
    'repo_name': '',
    'repo_type': '',
    'description': '',
    'private': '',
    'created_on': '',
    'enable_downloads': '',
    'repo_id': '',
    'user_id': '',
    'enable_statistics': '',
    'clone_uri': '',
    'fork_id': '',
    'group_id': '',
    'created_by': '',
    'repository': '',
    'comment': '',
    'commit': ''
})
def _comment_commit_repo_hook(*args, **kwargs):
    """
    POST CREATE REPOSITORY COMMENT ON COMMIT HOOK. This function will be executed after
    a comment is made on this repository commit.

    """
    from .helpers import http_call, extra_fields
    from .utils import UrlTemplate
    # returns list of dicts with key-val fetched from extra fields
    repo_extra_fields = extra_fields.run(**kwargs)

    import rhodecode
    from rc_integrations.jenkins_ci import csrf_call, get_auth, requests_retry_call

    endpoint_url = extra_fields.get_field(
        repo_extra_fields, key='ci_endpoint_url',
        default='http://ci.rc.com/job/rc-ce-commits/build?COMMIT_ID=${commit}')
    mention_text = extra_fields.get_field(
        repo_extra_fields, key='ci_mention_text',
        default='@jenkins build')

    endpoint_url = UrlTemplate(endpoint_url).safe_substitute(
        commit=kwargs['commit']['raw_id'])

    trigger_ci = False
    comment = kwargs['comment']['comment_text']
    if mention_text in comment:
        trigger_ci = True

    if trigger_ci is False:
        return HookResponse(0, '')

    # call some CI based on the special coment mention marker
    data = {
        'project': kwargs['repository'],
    }
    response = http_call.run(url=endpoint_url, params=data)

    return HookResponse(0, '')