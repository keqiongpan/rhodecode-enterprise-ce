# Example to validate commit message or author using some sort of rules


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'repo_store_path': 'full path to where repositories are stored',
    'commit_ids': 'pre transaction metadata for commit ids',
    'hook_type': '',
    'user_agent': 'Client user agent, e.g git or mercurial CLI version',
})
def _pre_push_hook(*args, **kwargs):
    """
    Post push hook
    To stop version control from storing the transaction and send a message to user
    use non-zero HookResponse with a message, e.g return HookResponse(1, 'Not allowed')

    This message will be shown back to client during PUSH operation

    Commit ids might look like that::

    [{u'hg_env|git_env': ...,
      u'multiple_heads': [],
      u'name': u'default',
      u'new_rev': u'd0befe0692e722e01d5677f27a104631cf798b69',
      u'old_rev': u'd0befe0692e722e01d5677f27a104631cf798b69',
      u'ref': u'',
      u'total_commits': 2,
      u'type': u'branch'}]
    """
    import re
    from .helpers import extra_fields, extract_pre_commits
    from .utils import str2bool

    # returns list of dicts with key-val fetched from extra fields
    repo_extra_fields = extra_fields.run(**kwargs)

    # optionally use 'extra fields' to control the logic per repo
    validate_author = extra_fields.get_field(
        repo_extra_fields, key='validate_author', default=False)
    should_validate = str2bool(validate_author)

    # optionally store validation regex into extra fields
    validation_regex = extra_fields.get_field(
        repo_extra_fields, key='validation_regex', default='')

    def validate_commit_message(commit_message, message_regex=None):
        """
        This function validates commit_message against some sort of rules.
        It should return a valid boolean, and a reason for failure
        """

        if "secret_string" in commit_message:
            msg = "!!Push forbidden: secret string found in commit messages"
            return False, msg

        if validation_regex:
            regexp = re.compile(validation_regex)
            if not regexp.match(message):
                msg = "!!Push forbidden: commit message does not match regexp"
                return False, msg

        return True, ''

    if should_validate:
        # returns list of dicts with key-val fetched from extra fields
        commit_list = extract_pre_commits.run(**kwargs)

        for commit_data in commit_list:
            message = commit_data['message']

            message_valid, reason = validate_commit_message(message, validation_regex)
            if not message_valid:
                return HookResponse(1, reason)

    return HookResponse(0, '')
