# Auto generated configuration for use with the Apache mod_dav_svn module.
#
# WARNING: Make sure your Apache instance which runs the mod_dav_svn module is
#          only accessible by RhodeCode. Otherwise everyone is able to browse
#          the repositories or run subversion operations (checkout/commit/etc.).
#
# The mod_dav_svn module does not support subversion repositories which are
# organized in subfolders. To support the repository groups of RhodeCode it is
# required to provide a <Location> block for each group pointing to the
# repository group sub folder. To ease the configuration RhodeCode auto
# generates this file whenever a repository group is created/changed/deleted.
# Auto generation can be configured in the ini file. Settings are prefixed with
# ``svn.proxy``.
#
# To include this configuration into your apache config you can use the
# `Include` directive. See the following example snippet of a virtual host how
# to include this configuration file.
#
#     <VirtualHost *:8090>
#         ServerAdmin webmaster@localhost
#         DocumentRoot /var/www/html
#         ErrorLog ${'${APACHE_LOG_DIR}'}/error.log
#         CustomLog ${'${APACHE_LOG_DIR}'}/access.log combined
#         LogLevel info
#         # allows custom host names, prevents 400 errors on checkout
#         HttpProtocolOptions Unsafe
#         # Most likely this will be: /home/user/.rccontrol/enterprise-1/mod_dav_svn.conf
#         Include /path/to/generated/mod_dav_svn.conf
#     </VirtualHost>
#
# Depending on the apache configuration you may encounter the following error if
# you are using special characters in your repository or repository group
# names.
#
#    ``Error converting entry in directory '/path/to/repo' to UTF-8``
#
# In this case you have to change the LANG environment variable in the apache
# configuration. This setting is typically located at ``/etc/apache2/envvars``.
# You have to change it to an UTF-8 value like ``export LANG="en_US.UTF-8"``.
# After changing this a stop and start of Apache is required (using restart
# doesn't work).

# fix https -> http downgrade with DAV. It requires an header downgrade for
# https -> http reverse proxy to work properly
% if use_https:
RequestHeader edit Destination ^https: http: early
% else:
#RequestHeader edit Destination ^https: http: early
% endif

<Location "${location_root|n}">
    # The mod_dav_svn module takes the username from the apache request object.
    # Without authorization this will be empty and no username is logged for the
    # transactions. This will result in "(no author)" for each revision. The
    # following directives implement a fake authentication that allows every
    # username/password combination.
    AuthType Basic
    AuthName "${rhodecode_realm|n}"
    AuthBasicProvider anon
    Anonymous *
    Anonymous_LogEmail off
    Require valid-user

    DAV svn
    SVNParentPath "${parent_path_root|n}"
    SVNListParentPath ${"On" if svn_list_parent_path else "Off"|n}

    # use specific SVN conf/authz file for each repository
    #AuthzSVNReposRelativeAccessFile authz

    Allow from all
    Order allow,deny
</Location>

% for location, parent_path in repo_group_paths:

<Location "${location|n}">
    AuthType Basic
    AuthName "${rhodecode_realm|n}"
    AuthBasicProvider anon
    Anonymous *
    Anonymous_LogEmail off
    Require valid-user

    DAV svn
    SVNParentPath "${parent_path|n}"
    SVNListParentPath ${"On" if svn_list_parent_path else "Off"|n}

    # use specific SVN conf/authz file for each repository
    #AuthzSVNReposRelativeAccessFile authz

    Allow from all
    Order allow,deny
</Location>
% endfor
