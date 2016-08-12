# Auto generated configuration for use with the Apache mod_dav_svn module.
#
# WARNING: Make sure your Apache instance which runs the mod_dav_svn module is
#          only accessible by RhodeCode. Otherwise everyone is able to browse
#          the repositories or run subversion operations (checkout/commit/etc.).
#
# The mod_dav_svn module does not support subversion repositories which are
# organized in subfolders. To support the repository groups of RhodeCode it is
# required to provide a <Location> block for each group pointing to the
# repository group sub folder.
#
# To ease the configuration RhodeCode auto generates this file whenever a
# repository group is created/changed/deleted. Auto generation can be configured
# in the ini file.
#
# To include this configuration into your apache config you can use the
# `Include` directive. See the following example snippet of a virtual host how
# to include this configuration file.
#
#     <VirtualHost *:8080>
#         ServerAdmin webmaster@localhost
#         DocumentRoot /var/www/html
#         ErrorLog ${'${APACHE_LOG_DIR}'}/error.log
#         CustomLog ${'${APACHE_LOG_DIR}'}/access.log combined
#         Include /path/to/generated/mod_dav_svn.conf
#     </VirtualHost>


<Location ${location_root}>
    # The mod_dav_svn module takes the username from the apache request object.
    # Without authorization this will be empty and no username is logged for the
    # transactions. This will result in "(no author)" for each revision. The
    # following directives implement a fake authentication that allows every
    # username/password combination.
    AuthType Basic
    AuthName ${rhodecode_realm}
    AuthBasicProvider anon
    Anonymous *
    Require valid-user

    DAV svn
    SVNParentPath ${parent_path_root}
    SVNListParentPath ${'On' if svn_list_parent_path else 'Off'}

    Allow from all
    Order allow,deny
</Location>

% for location, parent_path in repo_group_paths:

<Location ${location}>
    AuthType Basic
    AuthName ${rhodecode_realm}
    AuthBasicProvider anon
    Anonymous *
    Require valid-user

    DAV svn
    SVNParentPath ${parent_path}
    SVNListParentPath ${'On' if svn_list_parent_path else 'Off'}

    Allow from all
    Order allow,deny
</Location>
% endfor
