# Example to validate pushed files names and size using some sort of rules



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
      u'new_rev': u'd0b2ae0692e722e01d5677f27a104631cf798b69',
      u'old_rev': u'd0b1ae0692e722e01d5677f27a104631cf798b69',
      u'ref': u'',
      u'total_commits': 2,
      u'type': u'branch'}]
    """
    import fnmatch
    from .helpers import extra_fields, extract_pre_files
    from .utils import str2bool, aslist
    from rhodecode.lib.helpers import format_byte_size_binary

    # returns list of dicts with key-val fetched from extra fields
    repo_extra_fields = extra_fields.run(**kwargs)

    # optionally use 'extra fields' to control the logic per repo
    # e.g store a list of patterns to be forbidden e.g `*.exe, *.dump`
    forbid_files = extra_fields.get_field(repo_extra_fields, key='forbid_files_glob',
                                          convert_type=False, default=[])
    forbid_files = aslist(forbid_files)

    # forbid_files = ['*']  # example pattern

    # optionally get bytes limit for a single file, e.g 1024 for 1KB
    forbid_size_over = extra_fields.get_field(repo_extra_fields, key='forbid_size_over',
                                              convert_type=False, default=0)

    forbid_size_over = int(forbid_size_over or 0)

    # forbid_size_over = 1024  # example 1024

    def validate_file_name_and_size(file_data, forbidden_files=None, size_limit=None):
        """
        This function validates comited files against some sort of rules.
        It should return a valid boolean, and a reason for failure

        file_data =[
            'raw_diff', 'old_revision', 'stats', 'original_filename', 'is_limited_diff',
            'chunks', 'new_revision', 'operation', 'exceeds_limit', 'filename'
            ]
        file_data['ops'] = {
        # is file binary
        'binary': False,

        # lines
        'added': 32,
        'deleted': 0

        'ops': {3: 'modified file'},
        'new_mode': '100644',
        'old_mode': None
        }
        """
        file_name = file_data['filename']
        operation = file_data['operation']  # can be A(dded), M(odified), D(eleted)

        # check files names
        if forbidden_files:
            reason = 'File {} is forbidden to be pushed'.format(file_name)
            for forbidden_pattern in forbid_files:
                # here we can also filter for operation, e.g if check for only ADDED files
                # if operation == 'A':
                if fnmatch.fnmatch(file_name, forbidden_pattern):
                    return False, reason

        # validate A(dded) files and size
        if size_limit and operation == 'A':
            if 'file_size' in file_data:
                size = file_data['file_size']
            else:
                size = len(file_data['raw_diff'])

            reason = 'File {} size of {} bytes exceeds limit {}'.format(
                file_name, format_byte_size_binary(size),
                format_byte_size_binary(size_limit))
            if size > size_limit:
                return False, reason

        return True, ''

    if forbid_files or forbid_size_over:
        # returns list of dicts with key-val fetched from extra fields
        file_list = extract_pre_files.run(**kwargs)

        for file_data in file_list:
            file_valid, reason = validate_file_name_and_size(
                file_data, forbid_files, forbid_size_over)
            if not file_valid:
                return HookResponse(1, reason)

    return HookResponse(0, '')
