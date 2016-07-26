# Auto generated configuration for use with the Apache mod_dav_svn module.

# The mod_dav_svn module does not support subversion repositories which are
# organized in subfolders. To support the repository groups of RhodeCode it is
# required to provide a <Location> block for each group pointing to the
# repository group sub folder.

# To ease the configuration RhodeCode auto generates this file whenever a
# repository group is created/changed/deleted. Auto generation can be configured
# in the ini file.

<Location ${location_root}>
    DAV svn
    SVNParentPath ${parent_path_root}
    SVNListParentPath ${'On' if svn_list_parent_path else 'Off'}
    Allow from all
    Order allow,deny
</Location>

% for repo_group in repo_groups:
<Location ${location_root}${repo_group.full_path}>
    DAV svn
    SVNParentPath ${parent_path_root}${repo_group.full_path}
    SVNListParentPath ${'On' if svn_list_parent_path else 'Off'}
    Allow from all
    Order allow,deny
</Location>
% endfor
