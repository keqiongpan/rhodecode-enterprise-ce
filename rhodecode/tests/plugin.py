# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

import collections
import datetime
import hashlib
import os
import re
import pprint
import shutil
import socket
import subprocess32
import time
import uuid
import dateutil.tz

import mock
import pyramid.testing
import pytest
import colander
import requests
import pyramid.paster

import rhodecode
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (
    PullRequest, Repository, RhodeCodeSetting, ChangesetStatus, RepoGroup,
    UserGroup, RepoRhodeCodeUi, RepoRhodeCodeSetting, RhodeCodeUi)
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.user import UserModel
from rhodecode.model.settings import VcsSettingsModel
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.integration import IntegrationModel
from rhodecode.integrations import integration_type_registry
from rhodecode.integrations.types.base import IntegrationTypeBase
from rhodecode.lib.utils import repo2db_mapper
from rhodecode.lib.vcs.backends import get_backend
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.tests import (
    login_user_session, get_new_dir, utils, TESTS_TMP_PATH,
    TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR2_LOGIN,
    TEST_USER_REGULAR_PASS)
from rhodecode.tests.utils import CustomTestApp, set_anonymous_access
from rhodecode.tests.fixture import Fixture
from rhodecode.config import utils as config_utils


def _split_comma(value):
    return value.split(',')


def pytest_addoption(parser):
    parser.addoption(
        '--keep-tmp-path', action='store_true',
        help="Keep the test temporary directories")
    parser.addoption(
        '--backends', action='store', type=_split_comma,
        default=['git', 'hg', 'svn'],
        help="Select which backends to test for backend specific tests.")
    parser.addoption(
        '--dbs', action='store', type=_split_comma,
        default=['sqlite'],
        help="Select which database to test for database specific tests. "
             "Possible options are sqlite,postgres,mysql")
    parser.addoption(
        '--appenlight', '--ae', action='store_true',
        help="Track statistics in appenlight.")
    parser.addoption(
        '--appenlight-api-key', '--ae-key',
        help="API key for Appenlight.")
    parser.addoption(
        '--appenlight-url', '--ae-url',
        default="https://ae.rhodecode.com",
        help="Appenlight service URL, defaults to https://ae.rhodecode.com")
    parser.addoption(
        '--sqlite-connection-string', action='store',
        default='', help="Connection string for the dbs tests with SQLite")
    parser.addoption(
        '--postgres-connection-string', action='store',
        default='', help="Connection string for the dbs tests with Postgres")
    parser.addoption(
        '--mysql-connection-string', action='store',
        default='', help="Connection string for the dbs tests with MySQL")
    parser.addoption(
        '--repeat', type=int, default=100,
        help="Number of repetitions in performance tests.")


def pytest_configure(config):
    from rhodecode.config import patches


def pytest_collection_modifyitems(session, config, items):
    # nottest marked, compare nose, used for transition from nose to pytest
    remaining = [
        i for i in items if getattr(i.obj, '__test__', True)]
    items[:] = remaining


def pytest_generate_tests(metafunc):

    # Support test generation based on --backend parameter
    if 'backend_alias' in metafunc.fixturenames:
        backends = get_backends_from_metafunc(metafunc)
        scope = None
        if not backends:
            pytest.skip("Not enabled for any of selected backends")

        metafunc.parametrize('backend_alias', backends, scope=scope)

    backend_mark = metafunc.definition.get_closest_marker('backends')
    if backend_mark:
        backends = get_backends_from_metafunc(metafunc)
        if not backends:
            pytest.skip("Not enabled for any of selected backends")


def get_backends_from_metafunc(metafunc):
    requested_backends = set(metafunc.config.getoption('--backends'))
    backend_mark = metafunc.definition.get_closest_marker('backends')
    if backend_mark:
        # Supported backends by this test function, created from
        # pytest.mark.backends
        backends = backend_mark.args
    elif hasattr(metafunc.cls, 'backend_alias'):
        # Support class attribute "backend_alias", this is mainly
        # for legacy reasons for tests not yet using pytest.mark.backends
        backends = [metafunc.cls.backend_alias]
    else:
        backends = metafunc.config.getoption('--backends')
    return requested_backends.intersection(backends)


@pytest.fixture(scope='session', autouse=True)
def activate_example_rcextensions(request):
    """
    Patch in an example rcextensions module which verifies passed in kwargs.
    """
    from rhodecode.config import rcextensions

    old_extensions = rhodecode.EXTENSIONS
    rhodecode.EXTENSIONS = rcextensions
    rhodecode.EXTENSIONS.calls = collections.defaultdict(list)

    @request.addfinalizer
    def cleanup():
        rhodecode.EXTENSIONS = old_extensions


@pytest.fixture()
def capture_rcextensions():
    """
    Returns the recorded calls to entry points in rcextensions.
    """
    calls = rhodecode.EXTENSIONS.calls
    calls.clear()
    # Note: At this moment, it is still the empty dict, but that will
    # be filled during the test run and since it is a reference this
    # is enough to make it work.
    return calls


@pytest.fixture(scope='session')
def http_environ_session():
    """
    Allow to use "http_environ" in session scope.
    """
    return plain_http_environ()


def plain_http_host_stub():
    """
    Value of HTTP_HOST in the test run.
    """
    return 'example.com:80'


@pytest.fixture()
def http_host_stub():
    """
    Value of HTTP_HOST in the test run.
    """
    return plain_http_host_stub()


def plain_http_host_only_stub():
    """
    Value of HTTP_HOST in the test run.
    """
    return plain_http_host_stub().split(':')[0]


@pytest.fixture()
def http_host_only_stub():
    """
    Value of HTTP_HOST in the test run.
    """
    return plain_http_host_only_stub()


def plain_http_environ():
    """
    HTTP extra environ keys.

    User by the test application and as well for setting up the pylons
    environment. In the case of the fixture "app" it should be possible
    to override this for a specific test case.
    """
    return {
        'SERVER_NAME': plain_http_host_only_stub(),
        'SERVER_PORT': plain_http_host_stub().split(':')[1],
        'HTTP_HOST': plain_http_host_stub(),
        'HTTP_USER_AGENT': 'rc-test-agent',
        'REQUEST_METHOD': 'GET'
    }


@pytest.fixture()
def http_environ():
    """
    HTTP extra environ keys.

    User by the test application and as well for setting up the pylons
    environment. In the case of the fixture "app" it should be possible
    to override this for a specific test case.
    """
    return plain_http_environ()


@pytest.fixture(scope='session')
def baseapp(ini_config, vcsserver, http_environ_session):
    from rhodecode.lib.pyramid_utils import get_app_config
    from rhodecode.config.middleware import make_pyramid_app

    print("Using the RhodeCode configuration:{}".format(ini_config))
    pyramid.paster.setup_logging(ini_config)

    settings = get_app_config(ini_config)
    app = make_pyramid_app({'__file__': ini_config}, **settings)

    return app


@pytest.fixture(scope='function')
def app(request, config_stub, baseapp, http_environ):
    app = CustomTestApp(
        baseapp,
        extra_environ=http_environ)
    if request.cls:
        request.cls.app = app
    return app


@pytest.fixture(scope='session')
def app_settings(baseapp, ini_config):
    """
    Settings dictionary used to create the app.

    Parses the ini file and passes the result through the sanitize and apply
    defaults mechanism in `rhodecode.config.middleware`.
    """
    return baseapp.config.get_settings()


@pytest.fixture(scope='session')
def db_connection(ini_settings):
    # Initialize the database connection.
    config_utils.initialize_database(ini_settings)


LoginData = collections.namedtuple('LoginData', ('csrf_token', 'user'))


def _autologin_user(app, *args):
    session = login_user_session(app, *args)
    csrf_token = rhodecode.lib.auth.get_csrf_token(session)
    return LoginData(csrf_token, session['rhodecode_user'])


@pytest.fixture()
def autologin_user(app):
    """
    Utility fixture which makes sure that the admin user is logged in
    """
    return _autologin_user(app)


@pytest.fixture()
def autologin_regular_user(app):
    """
    Utility fixture which makes sure that the regular user is logged in
    """
    return _autologin_user(
        app, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)


@pytest.fixture(scope='function')
def csrf_token(request, autologin_user):
    return autologin_user.csrf_token


@pytest.fixture(scope='function')
def xhr_header(request):
    return {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


@pytest.fixture()
def real_crypto_backend(monkeypatch):
    """
    Switch the production crypto backend on for this test.

    During the test run the crypto backend is replaced with a faster
    implementation based on the MD5 algorithm.
    """
    monkeypatch.setattr(rhodecode, 'is_test', False)


@pytest.fixture(scope='class')
def index_location(request, baseapp):
    index_location = baseapp.config.get_settings()['search.location']
    if request.cls:
        request.cls.index_location = index_location
    return index_location


@pytest.fixture(scope='session', autouse=True)
def tests_tmp_path(request):
    """
    Create temporary directory to be used during the test session.
    """
    if not os.path.exists(TESTS_TMP_PATH):
        os.makedirs(TESTS_TMP_PATH)

    if not request.config.getoption('--keep-tmp-path'):
        @request.addfinalizer
        def remove_tmp_path():
            shutil.rmtree(TESTS_TMP_PATH)

    return TESTS_TMP_PATH


@pytest.fixture()
def test_repo_group(request):
    """
    Create a temporary repository group, and destroy it after
    usage automatically
    """
    fixture = Fixture()
    repogroupid = 'test_repo_group_%s' % str(time.time()).replace('.', '')
    repo_group = fixture.create_repo_group(repogroupid)

    def _cleanup():
        fixture.destroy_repo_group(repogroupid)

    request.addfinalizer(_cleanup)
    return repo_group


@pytest.fixture()
def test_user_group(request):
    """
    Create a temporary user group, and destroy it after
    usage automatically
    """
    fixture = Fixture()
    usergroupid = 'test_user_group_%s' % str(time.time()).replace('.', '')
    user_group = fixture.create_user_group(usergroupid)

    def _cleanup():
        fixture.destroy_user_group(user_group)

    request.addfinalizer(_cleanup)
    return user_group


@pytest.fixture(scope='session')
def test_repo(request):
    container = TestRepoContainer()
    request.addfinalizer(container._cleanup)
    return container


class TestRepoContainer(object):
    """
    Container for test repositories which are used read only.

    Repositories will be created on demand and re-used during the lifetime
    of this object.

    Usage to get the svn test repository "minimal"::

       test_repo = TestContainer()
       repo = test_repo('minimal', 'svn')

    """

    dump_extractors = {
        'git': utils.extract_git_repo_from_dump,
        'hg': utils.extract_hg_repo_from_dump,
        'svn': utils.extract_svn_repo_from_dump,
    }

    def __init__(self):
        self._cleanup_repos = []
        self._fixture = Fixture()
        self._repos = {}

    def __call__(self, dump_name, backend_alias, config=None):
        key = (dump_name, backend_alias)
        if key not in self._repos:
            repo = self._create_repo(dump_name, backend_alias, config)
            self._repos[key] = repo.repo_id
        return Repository.get(self._repos[key])

    def _create_repo(self, dump_name, backend_alias, config):
        repo_name = '%s-%s' % (backend_alias, dump_name)
        backend = get_backend(backend_alias)
        dump_extractor = self.dump_extractors[backend_alias]
        repo_path = dump_extractor(dump_name, repo_name)

        vcs_repo = backend(repo_path, config=config)
        repo2db_mapper({repo_name: vcs_repo})

        repo = RepoModel().get_by_repo_name(repo_name)
        self._cleanup_repos.append(repo_name)
        return repo

    def _cleanup(self):
        for repo_name in reversed(self._cleanup_repos):
            self._fixture.destroy_repo(repo_name)


def backend_base(request, backend_alias, baseapp, test_repo):
    if backend_alias not in request.config.getoption('--backends'):
        pytest.skip("Backend %s not selected." % (backend_alias, ))

    utils.check_xfail_backends(request.node, backend_alias)
    utils.check_skip_backends(request.node, backend_alias)

    repo_name = 'vcs_test_%s' % (backend_alias, )
    backend = Backend(
        alias=backend_alias,
        repo_name=repo_name,
        test_name=request.node.name,
        test_repo_container=test_repo)
    request.addfinalizer(backend.cleanup)
    return backend


@pytest.fixture()
def backend(request, backend_alias, baseapp, test_repo):
    """
    Parametrized fixture which represents a single backend implementation.

    It respects the option `--backends` to focus the test run on specific
    backend implementations.

    It also supports `pytest.mark.xfail_backends` to mark tests as failing
    for specific backends. This is intended as a utility for incremental
    development of a new backend implementation.
    """
    return backend_base(request, backend_alias, baseapp, test_repo)


@pytest.fixture()
def backend_git(request, baseapp, test_repo):
    return backend_base(request, 'git', baseapp, test_repo)


@pytest.fixture()
def backend_hg(request, baseapp, test_repo):
    return backend_base(request, 'hg', baseapp, test_repo)


@pytest.fixture()
def backend_svn(request, baseapp, test_repo):
    return backend_base(request, 'svn', baseapp, test_repo)


@pytest.fixture()
def backend_random(backend_git):
    """
    Use this to express that your tests need "a backend.

    A few of our tests need a backend, so that we can run the code. This
    fixture is intended to be used for such cases. It will pick one of the
    backends and run the tests.

    The fixture `backend` would run the test multiple times for each
    available backend which is a pure waste of time if the test is
    independent of the backend type.
    """
    # TODO: johbo: Change this to pick a random backend
    return backend_git


@pytest.fixture()
def backend_stub(backend_git):
    """
    Use this to express that your tests need a backend stub

    TODO: mikhail: Implement a real stub logic instead of returning
    a git backend
    """
    return backend_git


@pytest.fixture()
def repo_stub(backend_stub):
    """
    Use this to express that your tests need a repository stub
    """
    return backend_stub.create_repo()


class Backend(object):
    """
    Represents the test configuration for one supported backend

    Provides easy access to different test repositories based on
    `__getitem__`. Such repositories will only be created once per test
    session.
    """

    invalid_repo_name = re.compile(r'[^0-9a-zA-Z]+')
    _master_repo = None
    _commit_ids = {}

    def __init__(self, alias, repo_name, test_name, test_repo_container):
        self.alias = alias
        self.repo_name = repo_name
        self._cleanup_repos = []
        self._test_name = test_name
        self._test_repo_container = test_repo_container
        # TODO: johbo: Used as a delegate interim. Not yet sure if Backend or
        # Fixture will survive in the end.
        self._fixture = Fixture()

    def __getitem__(self, key):
        return self._test_repo_container(key, self.alias)

    def create_test_repo(self, key, config=None):
        return self._test_repo_container(key, self.alias, config)

    @property
    def repo(self):
        """
        Returns the "current" repository. This is the vcs_test repo or the
        last repo which has been created with `create_repo`.
        """
        from rhodecode.model.db import Repository
        return Repository.get_by_repo_name(self.repo_name)

    @property
    def default_branch_name(self):
        VcsRepository = get_backend(self.alias)
        return VcsRepository.DEFAULT_BRANCH_NAME

    @property
    def default_head_id(self):
        """
        Returns the default head id of the underlying backend.

        This will be the default branch name in case the backend does have a
        default branch. In the other cases it will point to a valid head
        which can serve as the base to create a new commit on top of it.
        """
        vcsrepo = self.repo.scm_instance()
        head_id = (
            vcsrepo.DEFAULT_BRANCH_NAME or
            vcsrepo.commit_ids[-1])
        return head_id

    @property
    def commit_ids(self):
        """
        Returns the list of commits for the last created repository
        """
        return self._commit_ids

    def create_master_repo(self, commits):
        """
        Create a repository and remember it as a template.

        This allows to easily create derived repositories to construct
        more complex scenarios for diff, compare and pull requests.

        Returns a commit map which maps from commit message to raw_id.
        """
        self._master_repo = self.create_repo(commits=commits)
        return self._commit_ids

    def create_repo(
            self, commits=None, number_of_commits=0, heads=None,
            name_suffix=u'', bare=False, **kwargs):
        """
        Create a repository and record it for later cleanup.

        :param commits: Optional. A sequence of dict instances.
           Will add a commit per entry to the new repository.
        :param number_of_commits: Optional. If set to a number, this number of
           commits will be added to the new repository.
        :param heads: Optional. Can be set to a sequence of of commit
           names which shall be pulled in from the master repository.
        :param name_suffix: adds special suffix to generated repo name
        :param bare: set a repo as bare (no checkout)
        """
        self.repo_name = self._next_repo_name() + name_suffix
        repo = self._fixture.create_repo(
            self.repo_name, repo_type=self.alias, bare=bare, **kwargs)
        self._cleanup_repos.append(repo.repo_name)

        commits = commits or [
            {'message': 'Commit %s of %s' % (x, self.repo_name)}
            for x in range(number_of_commits)]
        vcs_repo = repo.scm_instance()
        vcs_repo.count()
        self._add_commits_to_repo(vcs_repo, commits)
        if heads:
            self.pull_heads(repo, heads)

        return repo

    def pull_heads(self, repo, heads):
        """
        Make sure that repo contains all commits mentioned in `heads`
        """
        vcsmaster = self._master_repo.scm_instance()
        vcsrepo = repo.scm_instance()
        vcsrepo.config.clear_section('hooks')
        commit_ids = [self._commit_ids[h] for h in heads]
        vcsrepo.pull(vcsmaster.path, commit_ids=commit_ids)

    def create_fork(self):
        repo_to_fork = self.repo_name
        self.repo_name = self._next_repo_name()
        repo = self._fixture.create_fork(repo_to_fork, self.repo_name)
        self._cleanup_repos.append(self.repo_name)
        return repo

    def new_repo_name(self, suffix=u''):
        self.repo_name = self._next_repo_name() + suffix
        self._cleanup_repos.append(self.repo_name)
        return self.repo_name

    def _next_repo_name(self):
        return u"%s_%s" % (
            self.invalid_repo_name.sub(u'_', self._test_name), len(self._cleanup_repos))

    def ensure_file(self, filename, content='Test content\n'):
        assert self._cleanup_repos, "Avoid writing into vcs_test repos"
        commits = [
            {'added': [
                FileNode(filename, content=content),
            ]},
        ]
        self._add_commits_to_repo(self.repo.scm_instance(), commits)

    def enable_downloads(self):
        repo = self.repo
        repo.enable_downloads = True
        Session().add(repo)
        Session().commit()

    def cleanup(self):
        for repo_name in reversed(self._cleanup_repos):
            self._fixture.destroy_repo(repo_name)

    def _add_commits_to_repo(self, repo, commits):
        commit_ids = _add_commits_to_repo(repo, commits)
        if not commit_ids:
            return
        self._commit_ids = commit_ids

        # Creating refs for Git to allow fetching them from remote repository
        if self.alias == 'git':
            refs = {}
            for message in self._commit_ids:
                # TODO: mikhail: do more special chars replacements
                ref_name = 'refs/test-refs/{}'.format(
                    message.replace(' ', ''))
                refs[ref_name] = self._commit_ids[message]
            self._create_refs(repo, refs)

    def _create_refs(self, repo, refs):
        for ref_name in refs:
            repo.set_refs(ref_name, refs[ref_name])


def vcsbackend_base(request, backend_alias, tests_tmp_path, baseapp, test_repo):
    if backend_alias not in request.config.getoption('--backends'):
        pytest.skip("Backend %s not selected." % (backend_alias, ))

    utils.check_xfail_backends(request.node, backend_alias)
    utils.check_skip_backends(request.node, backend_alias)

    repo_name = 'vcs_test_%s' % (backend_alias, )
    repo_path = os.path.join(tests_tmp_path, repo_name)
    backend = VcsBackend(
        alias=backend_alias,
        repo_path=repo_path,
        test_name=request.node.name,
        test_repo_container=test_repo)
    request.addfinalizer(backend.cleanup)
    return backend


@pytest.fixture()
def vcsbackend(request, backend_alias, tests_tmp_path, baseapp, test_repo):
    """
    Parametrized fixture which represents a single vcs backend implementation.

    See the fixture `backend` for more details. This one implements the same
    concept, but on vcs level. So it does not provide model instances etc.

    Parameters are generated dynamically, see :func:`pytest_generate_tests`
    for how this works.
    """
    return vcsbackend_base(request, backend_alias, tests_tmp_path, baseapp, test_repo)


@pytest.fixture()
def vcsbackend_git(request, tests_tmp_path, baseapp, test_repo):
    return vcsbackend_base(request, 'git', tests_tmp_path, baseapp, test_repo)


@pytest.fixture()
def vcsbackend_hg(request, tests_tmp_path, baseapp, test_repo):
    return vcsbackend_base(request, 'hg', tests_tmp_path, baseapp, test_repo)


@pytest.fixture()
def vcsbackend_svn(request, tests_tmp_path, baseapp, test_repo):
    return vcsbackend_base(request, 'svn', tests_tmp_path, baseapp, test_repo)


@pytest.fixture()
def vcsbackend_stub(vcsbackend_git):
    """
    Use this to express that your test just needs a stub of a vcsbackend.

    Plan is to eventually implement an in-memory stub to speed tests up.
    """
    return vcsbackend_git


class VcsBackend(object):
    """
    Represents the test configuration for one supported vcs backend.
    """

    invalid_repo_name = re.compile(r'[^0-9a-zA-Z]+')

    def __init__(self, alias, repo_path, test_name, test_repo_container):
        self.alias = alias
        self._repo_path = repo_path
        self._cleanup_repos = []
        self._test_name = test_name
        self._test_repo_container = test_repo_container

    def __getitem__(self, key):
        return self._test_repo_container(key, self.alias).scm_instance()

    @property
    def repo(self):
        """
        Returns the "current" repository. This is the vcs_test repo of the last
        repo which has been created.
        """
        Repository = get_backend(self.alias)
        return Repository(self._repo_path)

    @property
    def backend(self):
        """
        Returns the backend implementation class.
        """
        return get_backend(self.alias)

    def create_repo(self, commits=None, number_of_commits=0, _clone_repo=None,
                    bare=False):
        repo_name = self._next_repo_name()
        self._repo_path = get_new_dir(repo_name)
        repo_class = get_backend(self.alias)
        src_url = None
        if _clone_repo:
            src_url = _clone_repo.path
        repo = repo_class(self._repo_path, create=True, src_url=src_url, bare=bare)
        self._cleanup_repos.append(repo)

        commits = commits or [
            {'message': 'Commit %s of %s' % (x, repo_name)}
            for x in xrange(number_of_commits)]
        _add_commits_to_repo(repo, commits)
        return repo

    def clone_repo(self, repo):
        return self.create_repo(_clone_repo=repo)

    def cleanup(self):
        for repo in self._cleanup_repos:
            shutil.rmtree(repo.path)

    def new_repo_path(self):
        repo_name = self._next_repo_name()
        self._repo_path = get_new_dir(repo_name)
        return self._repo_path

    def _next_repo_name(self):
        return "%s_%s" % (
            self.invalid_repo_name.sub('_', self._test_name),
            len(self._cleanup_repos))

    def add_file(self, repo, filename, content='Test content\n'):
        imc = repo.in_memory_commit
        imc.add(FileNode(filename, content=content))
        imc.commit(
            message=u'Automatic commit from vcsbackend fixture',
            author=u'Automatic <automatic@rhodecode.com>')

    def ensure_file(self, filename, content='Test content\n'):
        assert self._cleanup_repos, "Avoid writing into vcs_test repos"
        self.add_file(self.repo, filename, content)


def _add_commits_to_repo(vcs_repo, commits):
    commit_ids = {}
    if not commits:
        return commit_ids

    imc = vcs_repo.in_memory_commit
    commit = None

    for idx, commit in enumerate(commits):
        message = unicode(commit.get('message', 'Commit %s' % idx))

        for node in commit.get('added', []):
            imc.add(FileNode(node.path, content=node.content))
        for node in commit.get('changed', []):
            imc.change(FileNode(node.path, content=node.content))
        for node in commit.get('removed', []):
            imc.remove(FileNode(node.path))

        parents = [
            vcs_repo.get_commit(commit_id=commit_ids[p])
            for p in commit.get('parents', [])]

        operations = ('added', 'changed', 'removed')
        if not any((commit.get(o) for o in operations)):
            imc.add(FileNode('file_%s' % idx, content=message))

        commit = imc.commit(
            message=message,
            author=unicode(commit.get('author', 'Automatic <automatic@rhodecode.com>')),
            date=commit.get('date'),
            branch=commit.get('branch'),
            parents=parents)

        commit_ids[commit.message] = commit.raw_id

    return commit_ids


@pytest.fixture()
def reposerver(request):
    """
    Allows to serve a backend repository
    """

    repo_server = RepoServer()
    request.addfinalizer(repo_server.cleanup)
    return repo_server


class RepoServer(object):
    """
    Utility to serve a local repository for the duration of a test case.

    Supports only Subversion so far.
    """

    url = None

    def __init__(self):
        self._cleanup_servers = []

    def serve(self, vcsrepo):
        if vcsrepo.alias != 'svn':
            raise TypeError("Backend %s not supported" % vcsrepo.alias)

        proc = subprocess32.Popen(
            ['svnserve', '-d', '--foreground', '--listen-host', 'localhost',
             '--root', vcsrepo.path])
        self._cleanup_servers.append(proc)
        self.url = 'svn://localhost'

    def cleanup(self):
        for proc in self._cleanup_servers:
            proc.terminate()


@pytest.fixture()
def pr_util(backend, request, config_stub):
    """
    Utility for tests of models and for functional tests around pull requests.

    It gives an instance of :class:`PRTestUtility` which provides various
    utility methods around one pull request.

    This fixture uses `backend` and inherits its parameterization.
    """

    util = PRTestUtility(backend)
    request.addfinalizer(util.cleanup)

    return util


class PRTestUtility(object):

    pull_request = None
    pull_request_id = None
    mergeable_patcher = None
    mergeable_mock = None
    notification_patcher = None

    def __init__(self, backend):
        self.backend = backend

    def create_pull_request(
            self, commits=None, target_head=None, source_head=None,
            revisions=None, approved=False, author=None, mergeable=False,
            enable_notifications=True, name_suffix=u'', reviewers=None,
            title=u"Test", description=u"Description"):
        self.set_mergeable(mergeable)
        if not enable_notifications:
            # mock notification side effect
            self.notification_patcher = mock.patch(
                'rhodecode.model.notification.NotificationModel.create')
            self.notification_patcher.start()

        if not self.pull_request:
            if not commits:
                commits = [
                    {'message': 'c1'},
                    {'message': 'c2'},
                    {'message': 'c3'},
                ]
                target_head = 'c1'
                source_head = 'c2'
                revisions = ['c2']

            self.commit_ids = self.backend.create_master_repo(commits)
            self.target_repository = self.backend.create_repo(
                heads=[target_head], name_suffix=name_suffix)
            self.source_repository = self.backend.create_repo(
                heads=[source_head], name_suffix=name_suffix)
            self.author = author or UserModel().get_by_username(
                TEST_USER_ADMIN_LOGIN)

            model = PullRequestModel()
            self.create_parameters = {
                'created_by': self.author,
                'source_repo': self.source_repository.repo_name,
                'source_ref': self._default_branch_reference(source_head),
                'target_repo': self.target_repository.repo_name,
                'target_ref': self._default_branch_reference(target_head),
                'revisions': [self.commit_ids[r] for r in revisions],
                'reviewers': reviewers or self._get_reviewers(),
                'title': title,
                'description': description,
            }
            self.pull_request = model.create(**self.create_parameters)
            assert model.get_versions(self.pull_request) == []

            self.pull_request_id = self.pull_request.pull_request_id

            if approved:
                self.approve()

            Session().add(self.pull_request)
            Session().commit()

        return self.pull_request

    def approve(self):
        self.create_status_votes(
            ChangesetStatus.STATUS_APPROVED,
            *self.pull_request.reviewers)

    def close(self):
        PullRequestModel().close_pull_request(self.pull_request, self.author)

    def _default_branch_reference(self, commit_message):
        reference = '%s:%s:%s' % (
            'branch',
            self.backend.default_branch_name,
            self.commit_ids[commit_message])
        return reference

    def _get_reviewers(self):
        return [
            (TEST_USER_REGULAR_LOGIN, ['default1'], False, []),
            (TEST_USER_REGULAR2_LOGIN, ['default2'], False, []),
        ]

    def update_source_repository(self, head=None):
        heads = [head or 'c3']
        self.backend.pull_heads(self.source_repository, heads=heads)

    def add_one_commit(self, head=None):
        self.update_source_repository(head=head)
        old_commit_ids = set(self.pull_request.revisions)
        PullRequestModel().update_commits(self.pull_request)
        commit_ids = set(self.pull_request.revisions)
        new_commit_ids = commit_ids - old_commit_ids
        assert len(new_commit_ids) == 1
        return new_commit_ids.pop()

    def remove_one_commit(self):
        assert len(self.pull_request.revisions) == 2
        source_vcs = self.source_repository.scm_instance()
        removed_commit_id = source_vcs.commit_ids[-1]

        # TODO: johbo: Git and Mercurial have an inconsistent vcs api here,
        # remove the if once that's sorted out.
        if self.backend.alias == "git":
            kwargs = {'branch_name': self.backend.default_branch_name}
        else:
            kwargs = {}
        source_vcs.strip(removed_commit_id, **kwargs)

        PullRequestModel().update_commits(self.pull_request)
        assert len(self.pull_request.revisions) == 1
        return removed_commit_id

    def create_comment(self, linked_to=None):
        comment = CommentsModel().create(
            text=u"Test comment",
            repo=self.target_repository.repo_name,
            user=self.author,
            pull_request=self.pull_request)
        assert comment.pull_request_version_id is None

        if linked_to:
            PullRequestModel()._link_comments_to_version(linked_to)

        return comment

    def create_inline_comment(
            self, linked_to=None, line_no=u'n1', file_path='file_1'):
        comment = CommentsModel().create(
            text=u"Test comment",
            repo=self.target_repository.repo_name,
            user=self.author,
            line_no=line_no,
            f_path=file_path,
            pull_request=self.pull_request)
        assert comment.pull_request_version_id is None

        if linked_to:
            PullRequestModel()._link_comments_to_version(linked_to)

        return comment

    def create_version_of_pull_request(self):
        pull_request = self.create_pull_request()
        version = PullRequestModel()._create_version_from_snapshot(
            pull_request)
        return version

    def create_status_votes(self, status, *reviewers):
        for reviewer in reviewers:
            ChangesetStatusModel().set_status(
                repo=self.pull_request.target_repo,
                status=status,
                user=reviewer.user_id,
                pull_request=self.pull_request)

    def set_mergeable(self, value):
        if not self.mergeable_patcher:
            self.mergeable_patcher = mock.patch.object(
                VcsSettingsModel, 'get_general_settings')
            self.mergeable_mock = self.mergeable_patcher.start()
        self.mergeable_mock.return_value = {
            'rhodecode_pr_merge_enabled': value}

    def cleanup(self):
        # In case the source repository is already cleaned up, the pull
        # request will already be deleted.
        pull_request = PullRequest().get(self.pull_request_id)
        if pull_request:
            PullRequestModel().delete(pull_request, pull_request.author)
            Session().commit()

        if self.notification_patcher:
            self.notification_patcher.stop()

        if self.mergeable_patcher:
            self.mergeable_patcher.stop()


@pytest.fixture()
def user_admin(baseapp):
    """
    Provides the default admin test user as an instance of `db.User`.
    """
    user = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
    return user


@pytest.fixture()
def user_regular(baseapp):
    """
    Provides the default regular test user as an instance of `db.User`.
    """
    user = UserModel().get_by_username(TEST_USER_REGULAR_LOGIN)
    return user


@pytest.fixture()
def user_util(request, db_connection):
    """
    Provides a wired instance of `UserUtility` with integrated cleanup.
    """
    utility = UserUtility(test_name=request.node.name)
    request.addfinalizer(utility.cleanup)
    return utility


# TODO: johbo: Split this up into utilities per domain or something similar
class UserUtility(object):

    def __init__(self, test_name="test"):
        self._test_name = self._sanitize_name(test_name)
        self.fixture = Fixture()
        self.repo_group_ids = []
        self.repos_ids = []
        self.user_ids = []
        self.user_group_ids = []
        self.user_repo_permission_ids = []
        self.user_group_repo_permission_ids = []
        self.user_repo_group_permission_ids = []
        self.user_group_repo_group_permission_ids = []
        self.user_user_group_permission_ids = []
        self.user_group_user_group_permission_ids = []
        self.user_permissions = []

    def _sanitize_name(self, name):
        for char in ['[', ']']:
            name = name.replace(char, '_')
        return name

    def create_repo_group(
            self, owner=TEST_USER_ADMIN_LOGIN, auto_cleanup=True):
        group_name = "{prefix}_repogroup_{count}".format(
            prefix=self._test_name,
            count=len(self.repo_group_ids))
        repo_group = self.fixture.create_repo_group(
            group_name, cur_user=owner)
        if auto_cleanup:
            self.repo_group_ids.append(repo_group.group_id)
        return repo_group

    def create_repo(self, owner=TEST_USER_ADMIN_LOGIN, parent=None,
                    auto_cleanup=True, repo_type='hg', bare=False):
        repo_name = "{prefix}_repository_{count}".format(
            prefix=self._test_name,
            count=len(self.repos_ids))

        repository = self.fixture.create_repo(
            repo_name, cur_user=owner, repo_group=parent, repo_type=repo_type, bare=bare)
        if auto_cleanup:
            self.repos_ids.append(repository.repo_id)
        return repository

    def create_user(self, auto_cleanup=True, **kwargs):
        user_name = "{prefix}_user_{count}".format(
            prefix=self._test_name,
            count=len(self.user_ids))
        user = self.fixture.create_user(user_name, **kwargs)
        if auto_cleanup:
            self.user_ids.append(user.user_id)
        return user

    def create_additional_user_email(self, user, email):
        uem = self.fixture.create_additional_user_email(user=user, email=email)
        return uem

    def create_user_with_group(self):
        user = self.create_user()
        user_group = self.create_user_group(members=[user])
        return user, user_group

    def create_user_group(self, owner=TEST_USER_ADMIN_LOGIN, members=None,
                          auto_cleanup=True, **kwargs):
        group_name = "{prefix}_usergroup_{count}".format(
            prefix=self._test_name,
            count=len(self.user_group_ids))
        user_group = self.fixture.create_user_group(
            group_name, cur_user=owner, **kwargs)

        if auto_cleanup:
            self.user_group_ids.append(user_group.users_group_id)
        if members:
            for user in members:
                UserGroupModel().add_user_to_group(user_group, user)
        return user_group

    def grant_user_permission(self, user_name, permission_name):
        self.inherit_default_user_permissions(user_name, False)
        self.user_permissions.append((user_name, permission_name))

    def grant_user_permission_to_repo_group(
            self, repo_group, user, permission_name):
        permission = RepoGroupModel().grant_user_permission(
            repo_group, user, permission_name)
        self.user_repo_group_permission_ids.append(
            (repo_group.group_id, user.user_id))
        return permission

    def grant_user_group_permission_to_repo_group(
            self, repo_group, user_group, permission_name):
        permission = RepoGroupModel().grant_user_group_permission(
            repo_group, user_group, permission_name)
        self.user_group_repo_group_permission_ids.append(
            (repo_group.group_id, user_group.users_group_id))
        return permission

    def grant_user_permission_to_repo(
            self, repo, user, permission_name):
        permission = RepoModel().grant_user_permission(
            repo, user, permission_name)
        self.user_repo_permission_ids.append(
            (repo.repo_id, user.user_id))
        return permission

    def grant_user_group_permission_to_repo(
            self, repo, user_group, permission_name):
        permission = RepoModel().grant_user_group_permission(
            repo, user_group, permission_name)
        self.user_group_repo_permission_ids.append(
            (repo.repo_id, user_group.users_group_id))
        return permission

    def grant_user_permission_to_user_group(
            self, target_user_group, user, permission_name):
        permission = UserGroupModel().grant_user_permission(
            target_user_group, user, permission_name)
        self.user_user_group_permission_ids.append(
            (target_user_group.users_group_id, user.user_id))
        return permission

    def grant_user_group_permission_to_user_group(
            self, target_user_group, user_group, permission_name):
        permission = UserGroupModel().grant_user_group_permission(
            target_user_group, user_group, permission_name)
        self.user_group_user_group_permission_ids.append(
            (target_user_group.users_group_id, user_group.users_group_id))
        return permission

    def revoke_user_permission(self, user_name, permission_name):
        self.inherit_default_user_permissions(user_name, True)
        UserModel().revoke_perm(user_name, permission_name)

    def inherit_default_user_permissions(self, user_name, value):
        user = UserModel().get_by_username(user_name)
        user.inherit_default_permissions = value
        Session().add(user)
        Session().commit()

    def cleanup(self):
        self._cleanup_permissions()
        self._cleanup_repos()
        self._cleanup_repo_groups()
        self._cleanup_user_groups()
        self._cleanup_users()

    def _cleanup_permissions(self):
        if self.user_permissions:
            for user_name, permission_name in self.user_permissions:
                self.revoke_user_permission(user_name, permission_name)

        for permission in self.user_repo_permission_ids:
            RepoModel().revoke_user_permission(*permission)

        for permission in self.user_group_repo_permission_ids:
            RepoModel().revoke_user_group_permission(*permission)

        for permission in self.user_repo_group_permission_ids:
            RepoGroupModel().revoke_user_permission(*permission)

        for permission in self.user_group_repo_group_permission_ids:
            RepoGroupModel().revoke_user_group_permission(*permission)

        for permission in self.user_user_group_permission_ids:
            UserGroupModel().revoke_user_permission(*permission)

        for permission in self.user_group_user_group_permission_ids:
            UserGroupModel().revoke_user_group_permission(*permission)

    def _cleanup_repo_groups(self):
        def _repo_group_compare(first_group_id, second_group_id):
            """
            Gives higher priority to the groups with the most complex paths
            """
            first_group = RepoGroup.get(first_group_id)
            second_group = RepoGroup.get(second_group_id)
            first_group_parts = (
                len(first_group.group_name.split('/')) if first_group else 0)
            second_group_parts = (
                len(second_group.group_name.split('/')) if second_group else 0)
            return cmp(second_group_parts, first_group_parts)

        sorted_repo_group_ids = sorted(
            self.repo_group_ids, cmp=_repo_group_compare)
        for repo_group_id in sorted_repo_group_ids:
            self.fixture.destroy_repo_group(repo_group_id)

    def _cleanup_repos(self):
        sorted_repos_ids = sorted(self.repos_ids)
        for repo_id in sorted_repos_ids:
            self.fixture.destroy_repo(repo_id)

    def _cleanup_user_groups(self):
        def _user_group_compare(first_group_id, second_group_id):
            """
            Gives higher priority to the groups with the most complex paths
            """
            first_group = UserGroup.get(first_group_id)
            second_group = UserGroup.get(second_group_id)
            first_group_parts = (
                len(first_group.users_group_name.split('/'))
                if first_group else 0)
            second_group_parts = (
                len(second_group.users_group_name.split('/'))
                if second_group else 0)
            return cmp(second_group_parts, first_group_parts)

        sorted_user_group_ids = sorted(
            self.user_group_ids, cmp=_user_group_compare)
        for user_group_id in sorted_user_group_ids:
            self.fixture.destroy_user_group(user_group_id)

    def _cleanup_users(self):
        for user_id in self.user_ids:
            self.fixture.destroy_user(user_id)


# TODO: Think about moving this into a pytest-pyro package and make it a
# pytest plugin
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Adding the remote traceback if the exception has this information.

    VCSServer attaches this information as the attribute `_vcs_server_traceback`
    to the exception instance.
    """
    outcome = yield
    report = outcome.get_result()
    if call.excinfo:
        _add_vcsserver_remote_traceback(report, call.excinfo.value)


def _add_vcsserver_remote_traceback(report, exc):
    vcsserver_traceback = getattr(exc, '_vcs_server_traceback', None)

    if vcsserver_traceback:
        section = 'VCSServer remote traceback ' + report.when
        report.sections.append((section, vcsserver_traceback))


@pytest.fixture(scope='session')
def testrun():
    return {
        'uuid': uuid.uuid4(),
        'start': datetime.datetime.utcnow().isoformat(),
        'timestamp': int(time.time()),
    }


class AppenlightClient(object):

    url_template = '{url}?protocol_version=0.5'

    def __init__(
            self, url, api_key, add_server=True, add_timestamp=True,
            namespace=None, request=None, testrun=None):
        self.url = self.url_template.format(url=url)
        self.api_key = api_key
        self.add_server = add_server
        self.add_timestamp = add_timestamp
        self.namespace = namespace
        self.request = request
        self.server = socket.getfqdn(socket.gethostname())
        self.tags_before = {}
        self.tags_after = {}
        self.stats = []
        self.testrun = testrun or {}

    def tag_before(self, tag, value):
        self.tags_before[tag] = value

    def tag_after(self, tag, value):
        self.tags_after[tag] = value

    def collect(self, data):
        if self.add_server:
            data.setdefault('server', self.server)
        if self.add_timestamp:
            data.setdefault('date', datetime.datetime.utcnow().isoformat())
        if self.namespace:
            data.setdefault('namespace', self.namespace)
        if self.request:
            data.setdefault('request', self.request)
        self.stats.append(data)

    def send_stats(self):
        tags = [
            ('testrun', self.request),
            ('testrun.start', self.testrun['start']),
            ('testrun.timestamp', self.testrun['timestamp']),
            ('test', self.namespace),
        ]
        for key, value in self.tags_before.items():
            tags.append((key + '.before', value))
            try:
                delta = self.tags_after[key] - value
                tags.append((key + '.delta', delta))
            except Exception:
                pass
        for key, value in self.tags_after.items():
            tags.append((key + '.after', value))
        self.collect({
            'message': "Collected tags",
            'tags': tags,
        })

        response = requests.post(
            self.url,
            headers={
                'X-appenlight-api-key': self.api_key},
            json=self.stats,
        )

        if not response.status_code == 200:
            pprint.pprint(self.stats)
            print(response.headers)
            print(response.text)
            raise Exception('Sending to appenlight failed')


@pytest.fixture()
def gist_util(request, db_connection):
    """
    Provides a wired instance of `GistUtility` with integrated cleanup.
    """
    utility = GistUtility()
    request.addfinalizer(utility.cleanup)
    return utility


class GistUtility(object):
    def __init__(self):
        self.fixture = Fixture()
        self.gist_ids = []

    def create_gist(self, **kwargs):
        gist = self.fixture.create_gist(**kwargs)
        self.gist_ids.append(gist.gist_id)
        return gist

    def cleanup(self):
        for id_ in self.gist_ids:
            self.fixture.destroy_gists(str(id_))


@pytest.fixture()
def enabled_backends(request):
    backends = request.config.option.backends
    return backends[:]


@pytest.fixture()
def settings_util(request, db_connection):
    """
    Provides a wired instance of `SettingsUtility` with integrated cleanup.
    """
    utility = SettingsUtility()
    request.addfinalizer(utility.cleanup)
    return utility


class SettingsUtility(object):
    def __init__(self):
        self.rhodecode_ui_ids = []
        self.rhodecode_setting_ids = []
        self.repo_rhodecode_ui_ids = []
        self.repo_rhodecode_setting_ids = []

    def create_repo_rhodecode_ui(
            self, repo, section, value, key=None, active=True, cleanup=True):
        key = key or hashlib.sha1(
            '{}{}{}'.format(section, value, repo.repo_id)).hexdigest()

        setting = RepoRhodeCodeUi()
        setting.repository_id = repo.repo_id
        setting.ui_section = section
        setting.ui_value = value
        setting.ui_key = key
        setting.ui_active = active
        Session().add(setting)
        Session().commit()

        if cleanup:
            self.repo_rhodecode_ui_ids.append(setting.ui_id)
        return setting

    def create_rhodecode_ui(
            self, section, value, key=None, active=True, cleanup=True):
        key = key or hashlib.sha1('{}{}'.format(section, value)).hexdigest()

        setting = RhodeCodeUi()
        setting.ui_section = section
        setting.ui_value = value
        setting.ui_key = key
        setting.ui_active = active
        Session().add(setting)
        Session().commit()

        if cleanup:
            self.rhodecode_ui_ids.append(setting.ui_id)
        return setting

    def create_repo_rhodecode_setting(
            self, repo, name, value, type_, cleanup=True):
        setting = RepoRhodeCodeSetting(
            repo.repo_id, key=name, val=value, type=type_)
        Session().add(setting)
        Session().commit()

        if cleanup:
            self.repo_rhodecode_setting_ids.append(setting.app_settings_id)
        return setting

    def create_rhodecode_setting(self, name, value, type_, cleanup=True):
        setting = RhodeCodeSetting(key=name, val=value, type=type_)
        Session().add(setting)
        Session().commit()

        if cleanup:
            self.rhodecode_setting_ids.append(setting.app_settings_id)

        return setting

    def cleanup(self):
        for id_ in self.rhodecode_ui_ids:
            setting = RhodeCodeUi.get(id_)
            Session().delete(setting)

        for id_ in self.rhodecode_setting_ids:
            setting = RhodeCodeSetting.get(id_)
            Session().delete(setting)

        for id_ in self.repo_rhodecode_ui_ids:
            setting = RepoRhodeCodeUi.get(id_)
            Session().delete(setting)

        for id_ in self.repo_rhodecode_setting_ids:
            setting = RepoRhodeCodeSetting.get(id_)
            Session().delete(setting)

        Session().commit()


@pytest.fixture()
def no_notifications(request):
    notification_patcher = mock.patch(
        'rhodecode.model.notification.NotificationModel.create')
    notification_patcher.start()
    request.addfinalizer(notification_patcher.stop)


@pytest.fixture(scope='session')
def repeat(request):
    """
    The number of repetitions is based on this fixture.

    Slower calls may divide it by 10 or 100. It is chosen in a way so that the
    tests are not too slow in our default test suite.
    """
    return request.config.getoption('--repeat')


@pytest.fixture()
def rhodecode_fixtures():
    return Fixture()


@pytest.fixture()
def context_stub():
    """
    Stub context object.
    """
    context = pyramid.testing.DummyResource()
    return context


@pytest.fixture()
def request_stub():
    """
    Stub request object.
    """
    from rhodecode.lib.base import bootstrap_request
    request = bootstrap_request(scheme='https')
    return request


@pytest.fixture()
def config_stub(request, request_stub):
    """
    Set up pyramid.testing and return the Configurator.
    """
    from rhodecode.lib.base import bootstrap_config
    config = bootstrap_config(request=request_stub)

    @request.addfinalizer
    def cleanup():
        pyramid.testing.tearDown()

    return config


@pytest.fixture()
def StubIntegrationType():
    class _StubIntegrationType(IntegrationTypeBase):
        """ Test integration type class """

        key = 'test'
        display_name = 'Test integration type'
        description = 'A test integration type for testing'

        @classmethod
        def icon(cls):
            return 'test_icon_html_image'

        def __init__(self, settings):
            super(_StubIntegrationType, self).__init__(settings)
            self.sent_events = []  # for testing

        def send_event(self, event):
            self.sent_events.append(event)

        def settings_schema(self):
            class SettingsSchema(colander.Schema):
                test_string_field = colander.SchemaNode(
                    colander.String(),
                    missing=colander.required,
                    title='test string field',
                )
                test_int_field = colander.SchemaNode(
                    colander.Int(),
                    title='some integer setting',
                )
            return SettingsSchema()


    integration_type_registry.register_integration_type(_StubIntegrationType)
    return _StubIntegrationType

@pytest.fixture()
def stub_integration_settings():
    return {
        'test_string_field': 'some data',
        'test_int_field': 100,
    }


@pytest.fixture()
def repo_integration_stub(request, repo_stub, StubIntegrationType,
        stub_integration_settings):
    integration = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings, enabled=True,
        name='test repo integration',
        repo=repo_stub, repo_group=None, child_repos_only=None)

    @request.addfinalizer
    def cleanup():
        IntegrationModel().delete(integration)

    return integration


@pytest.fixture()
def repogroup_integration_stub(request, test_repo_group, StubIntegrationType,
    stub_integration_settings):
    integration = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings, enabled=True,
        name='test repogroup integration',
        repo=None, repo_group=test_repo_group, child_repos_only=True)

    @request.addfinalizer
    def cleanup():
        IntegrationModel().delete(integration)

    return integration


@pytest.fixture()
def repogroup_recursive_integration_stub(request, test_repo_group,
    StubIntegrationType, stub_integration_settings):
    integration = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings, enabled=True,
        name='test recursive repogroup integration',
        repo=None, repo_group=test_repo_group, child_repos_only=False)

    @request.addfinalizer
    def cleanup():
        IntegrationModel().delete(integration)

    return integration


@pytest.fixture()
def global_integration_stub(request, StubIntegrationType,
    stub_integration_settings):
    integration = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings, enabled=True,
        name='test global integration',
        repo=None, repo_group=None, child_repos_only=None)

    @request.addfinalizer
    def cleanup():
        IntegrationModel().delete(integration)

    return integration


@pytest.fixture()
def root_repos_integration_stub(request, StubIntegrationType,
    stub_integration_settings):
    integration = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings, enabled=True,
        name='test global integration',
        repo=None, repo_group=None, child_repos_only=True)

    @request.addfinalizer
    def cleanup():
        IntegrationModel().delete(integration)

    return integration


@pytest.fixture()
def local_dt_to_utc():
    def _factory(dt):
        return dt.replace(tzinfo=dateutil.tz.tzlocal()).astimezone(
            dateutil.tz.tzutc()).replace(tzinfo=None)
    return _factory


@pytest.fixture()
def disable_anonymous_user(request, baseapp):
    set_anonymous_access(False)

    @request.addfinalizer
    def cleanup():
        set_anonymous_access(True)


@pytest.fixture(scope='module')
def rc_fixture(request):
    return Fixture()


@pytest.fixture()
def repo_groups(request):
    fixture = Fixture()

    session = Session()
    zombie_group = fixture.create_repo_group('zombie')
    parent_group = fixture.create_repo_group('parent')
    child_group = fixture.create_repo_group('parent/child')
    groups_in_db = session.query(RepoGroup).all()
    assert len(groups_in_db) == 3
    assert child_group.group_parent_id == parent_group.group_id

    @request.addfinalizer
    def cleanup():
        fixture.destroy_repo_group(zombie_group)
        fixture.destroy_repo_group(child_group)
        fixture.destroy_repo_group(parent_group)

    return zombie_group, parent_group, child_group
