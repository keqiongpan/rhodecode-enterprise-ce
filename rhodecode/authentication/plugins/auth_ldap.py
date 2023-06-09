# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

"""
RhodeCode authentication plugin for LDAP
"""

import logging
import traceback

import colander
from rhodecode.translation import _
from rhodecode.authentication.base import (
    RhodeCodeExternalAuthPlugin, AuthLdapBase, hybrid_property)
from rhodecode.authentication.schema import AuthnPluginSettingsSchemaBase
from rhodecode.authentication.routes import AuthnPluginResourceBase
from rhodecode.lib.colander_utils import strip_whitespace
from rhodecode.lib.exceptions import (
    LdapConnectionError, LdapUsernameError, LdapPasswordError, LdapImportError
)
from rhodecode.lib.utils2 import safe_unicode, safe_str
from rhodecode.model.db import User
from rhodecode.model.validators import Missing

log = logging.getLogger(__name__)

try:
    import ldap
except ImportError:
    # means that python-ldap is not installed, we use Missing object to mark
    # ldap lib is Missing
    ldap = Missing


class LdapError(Exception):
    pass


def plugin_factory(plugin_id, *args, **kwargs):
    """
    Factory function that is called during plugin discovery.
    It returns the plugin instance.
    """
    plugin = RhodeCodeAuthPlugin(plugin_id)
    return plugin


class LdapAuthnResource(AuthnPluginResourceBase):
    pass


class AuthLdap(AuthLdapBase):
    default_tls_cert_dir = '/etc/openldap/cacerts'

    scope_labels = {
        ldap.SCOPE_BASE: 'SCOPE_BASE',
        ldap.SCOPE_ONELEVEL: 'SCOPE_ONELEVEL',
        ldap.SCOPE_SUBTREE: 'SCOPE_SUBTREE',
    }

    def __init__(self, server, base_dn, port=389, bind_dn='', bind_pass='',
                 tls_kind='PLAIN', tls_reqcert='DEMAND', tls_cert_file=None,
                 tls_cert_dir=None, ldap_version=3,
                 search_scope='SUBTREE', attr_login='uid',
                 ldap_filter='', timeout=None):
        if ldap == Missing:
            raise LdapImportError("Missing or incompatible ldap library")

        self.debug = False
        self.timeout = timeout or 60 * 5
        self.ldap_version = ldap_version
        self.ldap_server_type = 'ldap'

        self.TLS_KIND = tls_kind

        if self.TLS_KIND == 'LDAPS':
            port = port or 636
            self.ldap_server_type += 's'

        OPT_X_TLS_DEMAND = 2
        self.TLS_REQCERT = getattr(ldap, 'OPT_X_TLS_%s' % tls_reqcert, OPT_X_TLS_DEMAND)
        self.TLS_CERT_FILE = tls_cert_file or ''
        self.TLS_CERT_DIR = tls_cert_dir or self.default_tls_cert_dir

        # split server into list
        self.SERVER_ADDRESSES = self._get_server_list(server)
        self.LDAP_SERVER_PORT = port

        # USE FOR READ ONLY BIND TO LDAP SERVER
        self.attr_login = attr_login

        self.LDAP_BIND_DN = safe_str(bind_dn)
        self.LDAP_BIND_PASS = safe_str(bind_pass)

        self.SEARCH_SCOPE = getattr(ldap, 'SCOPE_%s' % search_scope)
        self.BASE_DN = safe_str(base_dn)
        self.LDAP_FILTER = safe_str(ldap_filter)

    def _get_ldap_conn(self):

        if self.debug:
            ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)

        if self.TLS_CERT_FILE and hasattr(ldap, 'OPT_X_TLS_CACERTFILE'):
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.TLS_CERT_FILE)

        elif hasattr(ldap, 'OPT_X_TLS_CACERTDIR'):
            ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, self.TLS_CERT_DIR)

        if self.TLS_KIND != 'PLAIN':
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, self.TLS_REQCERT)

        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        ldap.set_option(ldap.OPT_RESTART, ldap.OPT_ON)

        # init connection now
        ldap_servers = self._build_servers(
            self.ldap_server_type,  self.SERVER_ADDRESSES, self.LDAP_SERVER_PORT)
        log.debug('initializing LDAP connection to:%s', ldap_servers)
        ldap_conn = ldap.initialize(ldap_servers)
        ldap_conn.set_option(ldap.OPT_NETWORK_TIMEOUT, self.timeout)
        ldap_conn.set_option(ldap.OPT_TIMEOUT, self.timeout)
        ldap_conn.timeout = self.timeout

        if self.ldap_version == 2:
            ldap_conn.protocol = ldap.VERSION2
        else:
            ldap_conn.protocol = ldap.VERSION3

        if self.TLS_KIND == 'START_TLS':
            ldap_conn.start_tls_s()

        if self.LDAP_BIND_DN and self.LDAP_BIND_PASS:
            log.debug('Trying simple_bind with password and given login DN: %r',
                      self.LDAP_BIND_DN)
            ldap_conn.simple_bind_s(self.LDAP_BIND_DN, self.LDAP_BIND_PASS)
        log.debug('simple_bind successful')
        return ldap_conn

    def fetch_attrs_from_simple_bind(self, ldap_conn, dn, username, password):
        scope = ldap.SCOPE_BASE
        scope_label = self.scope_labels.get(scope)
        ldap_filter = '(objectClass=*)'

        try:
            log.debug('Trying authenticated search bind with dn: %r SCOPE: %s (and filter: %s)',
                      dn, scope_label, ldap_filter)
            ldap_conn.simple_bind_s(dn, safe_str(password))
            response = ldap_conn.search_ext_s(dn, scope, ldap_filter, attrlist=['*', '+'])

            if not response:
                log.error('search bind returned empty results: %r', response)
                return {}
            else:
                _dn, attrs = response[0]
                return attrs

        except ldap.INVALID_CREDENTIALS:
            log.debug("LDAP rejected password for user '%s': %s, org_exc:",
                      username, dn, exc_info=True)

    def authenticate_ldap(self, username, password):
        """
        Authenticate a user via LDAP and return his/her LDAP properties.

        Raises AuthenticationError if the credentials are rejected, or
        EnvironmentError if the LDAP server can't be reached.

        :param username: username
        :param password: password
        """

        uid = self.get_uid(username, self.SERVER_ADDRESSES)
        user_attrs = {}
        dn = ''

        self.validate_password(username, password)
        self.validate_username(username)
        scope_label = self.scope_labels.get(self.SEARCH_SCOPE)

        ldap_conn = None
        try:
            ldap_conn = self._get_ldap_conn()
            filter_ = '(&%s(%s=%s))' % (
                self.LDAP_FILTER, self.attr_login, username)
            log.debug("Authenticating %r filter %s and scope: %s",
                      self.BASE_DN, filter_, scope_label)

            ldap_objects = ldap_conn.search_ext_s(
                self.BASE_DN, self.SEARCH_SCOPE, filter_, attrlist=['*', '+'])

            if not ldap_objects:
                log.debug("No matching LDAP objects for authentication "
                          "of UID:'%s' username:(%s)", uid, username)
                raise ldap.NO_SUCH_OBJECT()

            log.debug('Found %s matching ldap object[s], trying to authenticate on each one now...', len(ldap_objects))
            for (dn, _attrs) in ldap_objects:
                if dn is None:
                    continue

                user_attrs = self.fetch_attrs_from_simple_bind(
                    ldap_conn, dn, username, password)

                if user_attrs:
                    log.debug('Got authenticated user attributes from DN:%s', dn)
                    break
            else:
                raise LdapPasswordError(
                    'Failed to authenticate user `{}` with given password'.format(username))

        except ldap.NO_SUCH_OBJECT:
            log.debug("LDAP says no such user '%s' (%s), org_exc:",
                      uid, username, exc_info=True)
            raise LdapUsernameError('Unable to find user')
        except ldap.SERVER_DOWN:
            org_exc = traceback.format_exc()
            raise LdapConnectionError(
                "LDAP can't access authentication server, org_exc:%s" % org_exc)
        finally:
            if ldap_conn:
                log.debug('ldap: connection release')
                try:
                    ldap_conn.unbind_s()
                except Exception:
                    # for any reason this can raise exception we must catch it
                    # to not crush the server
                    pass

        return dn, user_attrs


class LdapSettingsSchema(AuthnPluginSettingsSchemaBase):
    tls_kind_choices = ['PLAIN', 'LDAPS', 'START_TLS']
    tls_reqcert_choices = ['NEVER', 'ALLOW', 'TRY', 'DEMAND', 'HARD']
    search_scope_choices = ['BASE', 'ONELEVEL', 'SUBTREE']

    host = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('Host[s] of the LDAP Server \n'
                      '(e.g., 192.168.2.154, or ldap-server.domain.com.\n '
                      'Multiple servers can be specified using commas'),
        preparer=strip_whitespace,
        title=_('LDAP Host'),
        widget='string')
    port = colander.SchemaNode(
        colander.Int(),
        default=389,
        description=_('Custom port that the LDAP server is listening on. '
                      'Default value is: 389, use 636 for LDAPS (SSL)'),
        preparer=strip_whitespace,
        title=_('Port'),
        validator=colander.Range(min=0, max=65536),
        widget='int')

    timeout = colander.SchemaNode(
        colander.Int(),
        default=60 * 5,
        description=_('Timeout for LDAP connection'),
        preparer=strip_whitespace,
        title=_('Connection timeout'),
        validator=colander.Range(min=1),
        widget='int')

    dn_user = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('Optional user DN/account to connect to LDAP if authentication is required. \n'
                      'e.g., cn=admin,dc=mydomain,dc=com, or '
                      'uid=root,cn=users,dc=mydomain,dc=com, or admin@mydomain.com'),
        missing='',
        preparer=strip_whitespace,
        title=_('Bind account'),
        widget='string')
    dn_pass = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('Password to authenticate for given user DN.'),
        missing='',
        preparer=strip_whitespace,
        title=_('Bind account password'),
        widget='password')
    tls_kind = colander.SchemaNode(
        colander.String(),
        default=tls_kind_choices[0],
        description=_('TLS Type'),
        title=_('Connection Security'),
        validator=colander.OneOf(tls_kind_choices),
        widget='select')
    tls_reqcert = colander.SchemaNode(
        colander.String(),
        default=tls_reqcert_choices[0],
        description=_('Require Cert over TLS?. Self-signed and custom '
                      'certificates can be used when\n `RhodeCode Certificate` '
                      'found in admin > settings > system info page is extended.'),
        title=_('Certificate Checks'),
        validator=colander.OneOf(tls_reqcert_choices),
        widget='select')
    tls_cert_file = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('This specifies the PEM-format file path containing '
                      'certificates for use in TLS connection.\n'
                      'If not specified `TLS Cert dir` will be used'),
        title=_('TLS Cert file'),
        missing='',
        widget='string')
    tls_cert_dir = colander.SchemaNode(
        colander.String(),
        default=AuthLdap.default_tls_cert_dir,
        description=_('This specifies the path of a directory that contains individual '
                      'CA certificates in separate files.'),
        title=_('TLS Cert dir'),
        widget='string')
    base_dn = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('Base DN to search. Dynamic bind is supported. Add `$login` marker '
                      'in it to be replaced with current user username \n'
                      '(e.g., dc=mydomain,dc=com, or ou=Users,dc=mydomain,dc=com)'),
        missing='',
        preparer=strip_whitespace,
        title=_('Base DN'),
        widget='string')
    filter = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('Filter to narrow results \n'
                      '(e.g., (&(objectCategory=Person)(objectClass=user)), or \n'
                      '(memberof=cn=rc-login,ou=groups,ou=company,dc=mydomain,dc=com)))'),
        missing='',
        preparer=strip_whitespace,
        title=_('LDAP Search Filter'),
        widget='string')

    search_scope = colander.SchemaNode(
        colander.String(),
        default=search_scope_choices[2],
        description=_('How deep to search LDAP. If unsure set to SUBTREE'),
        title=_('LDAP Search Scope'),
        validator=colander.OneOf(search_scope_choices),
        widget='select')
    attr_login = colander.SchemaNode(
        colander.String(),
        default='uid',
        description=_('LDAP Attribute to map to user name (e.g., uid, or sAMAccountName)'),
        preparer=strip_whitespace,
        title=_('Login Attribute'),
        missing_msg=_('The LDAP Login attribute of the CN must be specified'),
        widget='string')
    attr_email = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('LDAP Attribute to map to email address (e.g., mail).\n'
                      'Emails are a crucial part of RhodeCode. \n'
                      'If possible add a valid email attribute to ldap users.'),
        missing='',
        preparer=strip_whitespace,
        title=_('Email Attribute'),
        widget='string')
    attr_firstname = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('LDAP Attribute to map to first name (e.g., givenName)'),
        missing='',
        preparer=strip_whitespace,
        title=_('First Name Attribute'),
        widget='string')
    attr_lastname = colander.SchemaNode(
        colander.String(),
        default='',
        description=_('LDAP Attribute to map to last name (e.g., sn)'),
        missing='',
        preparer=strip_whitespace,
        title=_('Last Name Attribute'),
        widget='string')


class RhodeCodeAuthPlugin(RhodeCodeExternalAuthPlugin):
    uid = 'ldap'
    # used to define dynamic binding in the
    DYNAMIC_BIND_VAR = '$login'
    _settings_unsafe_keys = ['dn_pass']

    def includeme(self, config):
        config.add_authn_plugin(self)
        config.add_authn_resource(self.get_id(), LdapAuthnResource(self))
        config.add_view(
            'rhodecode.authentication.views.AuthnPluginViewBase',
            attr='settings_get',
            renderer='rhodecode:templates/admin/auth/plugin_settings.mako',
            request_method='GET',
            route_name='auth_home',
            context=LdapAuthnResource)
        config.add_view(
            'rhodecode.authentication.views.AuthnPluginViewBase',
            attr='settings_post',
            renderer='rhodecode:templates/admin/auth/plugin_settings.mako',
            request_method='POST',
            route_name='auth_home',
            context=LdapAuthnResource)

    def get_settings_schema(self):
        return LdapSettingsSchema()

    def get_display_name(self, load_from_settings=False):
        return _('LDAP')

    @classmethod
    def docs(cls):
        return "https://docs.rhodecode.com/RhodeCode-Enterprise/auth/auth-ldap.html"

    @hybrid_property
    def name(self):
        return u"ldap"

    def use_fake_password(self):
        return True

    def user_activation_state(self):
        def_user_perms = User.get_default_user().AuthUser().permissions['global']
        return 'hg.extern_activate.auto' in def_user_perms

    def try_dynamic_binding(self, username, password, current_args):
        """
        Detects marker inside our original bind, and uses dynamic auth if
        present
        """

        org_bind = current_args['bind_dn']
        passwd = current_args['bind_pass']

        def has_bind_marker(username):
            if self.DYNAMIC_BIND_VAR in username:
                return True

        # we only passed in user with "special" variable
        if org_bind and has_bind_marker(org_bind) and not passwd:
            log.debug('Using dynamic user/password binding for ldap '
                      'authentication. Replacing `%s` with username',
                      self.DYNAMIC_BIND_VAR)
            current_args['bind_dn'] = org_bind.replace(
                self.DYNAMIC_BIND_VAR, username)
            current_args['bind_pass'] = password

        return current_args

    def auth(self, userobj, username, password, settings, **kwargs):
        """
        Given a user object (which may be null), username, a plaintext password,
        and a settings object (containing all the keys needed as listed in
        settings()), authenticate this user's login attempt.

        Return None on failure. On success, return a dictionary of the form:

            see: RhodeCodeAuthPluginBase.auth_func_attrs
        This is later validated for correctness
        """

        if not username or not password:
            log.debug('Empty username or password skipping...')
            return None

        ldap_args = {
            'server': settings.get('host', ''),
            'base_dn': settings.get('base_dn', ''),
            'port': settings.get('port'),
            'bind_dn': settings.get('dn_user'),
            'bind_pass': settings.get('dn_pass'),
            'tls_kind': settings.get('tls_kind'),
            'tls_reqcert': settings.get('tls_reqcert'),
            'tls_cert_file': settings.get('tls_cert_file'),
            'tls_cert_dir': settings.get('tls_cert_dir'),
            'search_scope': settings.get('search_scope'),
            'attr_login': settings.get('attr_login'),
            'ldap_version': 3,
            'ldap_filter': settings.get('filter'),
            'timeout': settings.get('timeout')
        }

        ldap_attrs = self.try_dynamic_binding(username, password, ldap_args)

        log.debug('Checking for ldap authentication.')

        try:
            aldap = AuthLdap(**ldap_args)
            (user_dn, ldap_attrs) = aldap.authenticate_ldap(username, password)
            log.debug('Got ldap DN response %s', user_dn)

            def get_ldap_attr(k):
                return ldap_attrs.get(settings.get(k), [''])[0]

            # old attrs fetched from RhodeCode database
            admin = getattr(userobj, 'admin', False)
            active = getattr(userobj, 'active', True)
            email = getattr(userobj, 'email', '')
            username = getattr(userobj, 'username', username)
            firstname = getattr(userobj, 'firstname', '')
            lastname = getattr(userobj, 'lastname', '')
            extern_type = getattr(userobj, 'extern_type', '')

            groups = []

            user_attrs = {
                'username': username,
                'firstname': safe_unicode(get_ldap_attr('attr_firstname') or firstname),
                'lastname': safe_unicode(get_ldap_attr('attr_lastname') or lastname),
                'groups': groups,
                'user_group_sync': False,
                'email': get_ldap_attr('attr_email') or email,
                'admin': admin,
                'active': active,
                'active_from_extern': None,
                'extern_name': user_dn,
                'extern_type': extern_type,
            }

            log.debug('ldap user: %s', user_attrs)
            log.info('user `%s` authenticated correctly', user_attrs['username'])

            return user_attrs

        except (LdapUsernameError, LdapPasswordError, LdapImportError):
            log.exception("LDAP related exception")
            return None
        except (Exception,):
            log.exception("Other exception")
            return None


def includeme(config):
    plugin_id = 'egg:rhodecode-enterprise-ce#{}'.format(RhodeCodeAuthPlugin.uid)
    plugin_factory(plugin_id).includeme(config)
