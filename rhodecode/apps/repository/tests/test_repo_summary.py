# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

import re

import mock
import pytest

from rhodecode.apps.repository.views.repo_summary import RepoSummaryView
from rhodecode.lib import helpers as h
from rhodecode.lib.compat import OrderedDict
from rhodecode.lib.utils2 import AttributeDict, safe_str
from rhodecode.lib.vcs.exceptions import RepositoryRequirementError
from rhodecode.model.db import Repository
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import ScmModel
from rhodecode.tests import assert_session_flash
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse, repo_on_filesystem


fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_summary': '/{repo_name}',
        'repo_stats': '/{repo_name}/repo_stats/{commit_id}',
        'repo_refs_data': '/{repo_name}/refs-data',
        'repo_refs_changelog_data': '/{repo_name}/refs-data-changelog',
        'repo_creating_check': '/{repo_name}/repo_creating_check',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('app')
class TestSummaryView(object):
    def test_index(self, autologin_user, backend, http_host_only_stub):
        repo_id = backend.repo.repo_id
        repo_name = backend.repo_name
        with mock.patch('rhodecode.lib.helpers.is_svn_without_proxy',
                        return_value=False):
            response = self.app.get(
                route_path('repo_summary', repo_name=repo_name))

        # repo type
        response.mustcontain(
            '<i class="icon-%s">' % (backend.alias, )
        )
        # public/private
        response.mustcontain(
            """<i class="icon-unlock-alt">"""
        )

        # clone url...
        response.mustcontain(
            'id="clone_url" readonly="readonly"'
            ' value="http://test_admin@%s/%s"' % (http_host_only_stub, repo_name, ))
        response.mustcontain(
            'id="clone_url_id" readonly="readonly"'
            ' value="http://test_admin@%s/_%s"' % (http_host_only_stub, repo_id, ))

    def test_index_svn_without_proxy(
            self, autologin_user, backend_svn, http_host_only_stub):
        repo_id = backend_svn.repo.repo_id
        repo_name = backend_svn.repo_name
        response = self.app.get(route_path('repo_summary', repo_name=repo_name))
        # clone url...
        response.mustcontain(
            'id="clone_url" disabled'
            ' value="http://test_admin@%s/%s"' % (http_host_only_stub, repo_name, ))
        response.mustcontain(
            'id="clone_url_id" disabled'
            ' value="http://test_admin@%s/_%s"' % (http_host_only_stub, repo_id, ))

    def test_index_with_trailing_slash(
            self, autologin_user, backend, http_host_only_stub):

        repo_id = backend.repo.repo_id
        repo_name = backend.repo_name
        with mock.patch('rhodecode.lib.helpers.is_svn_without_proxy',
                        return_value=False):
            response = self.app.get(
                route_path('repo_summary', repo_name=repo_name) + '/',
                status=200)

        # clone url...
        response.mustcontain(
            'id="clone_url" readonly="readonly"'
            ' value="http://test_admin@%s/%s"' % (http_host_only_stub, repo_name, ))
        response.mustcontain(
            'id="clone_url_id" readonly="readonly"'
            ' value="http://test_admin@%s/_%s"' % (http_host_only_stub, repo_id, ))

    def test_index_by_id(self, autologin_user, backend):
        repo_id = backend.repo.repo_id
        response = self.app.get(
            route_path('repo_summary', repo_name='_%s' % (repo_id,)))

        # repo type
        response.mustcontain(
            '<i class="icon-%s">' % (backend.alias, )
        )
        # public/private
        response.mustcontain(
            """<i class="icon-unlock-alt">"""
        )

    def test_index_by_repo_having_id_path_in_name_hg(self, autologin_user):
        fixture.create_repo(name='repo_1')
        response = self.app.get(route_path('repo_summary', repo_name='repo_1'))

        try:
            response.mustcontain("repo_1")
        finally:
            RepoModel().delete(Repository.get_by_repo_name('repo_1'))
            Session().commit()

    def test_index_with_anonymous_access_disabled(
            self, backend, disable_anonymous_user):
        response = self.app.get(
            route_path('repo_summary', repo_name=backend.repo_name), status=302)
        assert 'login' in response.location

    def _enable_stats(self, repo):
        r = Repository.get_by_repo_name(repo)
        r.enable_statistics = True
        Session().add(r)
        Session().commit()

    expected_trending = {
        'hg': {
            "py": {"count": 68, "desc": ["Python"]},
            "rst": {"count": 16, "desc": ["Rst"]},
            "css": {"count": 2, "desc": ["Css"]},
            "sh": {"count": 2, "desc": ["Bash"]},
            "bat": {"count": 1, "desc": ["Batch"]},
            "cfg": {"count": 1, "desc": ["Ini"]},
            "html": {"count": 1, "desc": ["EvoqueHtml", "Html"]},
            "ini": {"count": 1, "desc": ["Ini"]},
            "js": {"count": 1, "desc": ["Javascript"]},
            "makefile": {"count": 1, "desc": ["Makefile", "Makefile"]}
        },
        'git': {
            "py": {"count": 68, "desc": ["Python"]},
            "rst": {"count": 16, "desc": ["Rst"]},
            "css": {"count": 2, "desc": ["Css"]},
            "sh": {"count": 2, "desc": ["Bash"]},
            "bat": {"count": 1, "desc": ["Batch"]},
            "cfg": {"count": 1, "desc": ["Ini"]},
            "html": {"count": 1, "desc": ["EvoqueHtml", "Html"]},
            "ini": {"count": 1, "desc": ["Ini"]},
            "js": {"count": 1, "desc": ["Javascript"]},
            "makefile": {"count": 1, "desc": ["Makefile", "Makefile"]}
        },
        'svn': {
            "py": {"count": 75, "desc": ["Python"]},
            "rst": {"count": 16, "desc": ["Rst"]},
            "html": {"count": 11, "desc": ["EvoqueHtml", "Html"]},
            "css": {"count": 2, "desc": ["Css"]},
            "bat": {"count": 1, "desc": ["Batch"]},
            "cfg": {"count": 1, "desc": ["Ini"]},
            "ini": {"count": 1, "desc": ["Ini"]},
            "js": {"count": 1, "desc": ["Javascript"]},
            "makefile": {"count": 1, "desc": ["Makefile", "Makefile"]},
            "sh": {"count": 1, "desc": ["Bash"]}
        },
    }

    def test_repo_stats(self, autologin_user, backend, xhr_header):
        response = self.app.get(
            route_path(
                'repo_stats', repo_name=backend.repo_name, commit_id='tip'),
            extra_environ=xhr_header,
            status=200)
        assert re.match(r'6[\d\.]+ KiB', response.json['size'])

    def test_repo_stats_code_stats_enabled(self, autologin_user, backend, xhr_header):
        repo_name = backend.repo_name

        # codes stats
        self._enable_stats(repo_name)
        ScmModel().mark_for_invalidation(repo_name)

        response = self.app.get(
            route_path(
                'repo_stats', repo_name=backend.repo_name, commit_id='tip'),
            extra_environ=xhr_header,
            status=200)

        expected_data = self.expected_trending[backend.alias]
        returned_stats = response.json['code_stats']
        for k, v in expected_data.items():
            assert v == returned_stats[k]

    def test_repo_refs_data(self, backend):
        response = self.app.get(
            route_path('repo_refs_data', repo_name=backend.repo_name),
            status=200)

        # Ensure that there is the correct amount of items in the result
        repo = backend.repo.scm_instance()
        data = response.json['results']
        items = sum(len(section['children']) for section in data)
        repo_refs = len(repo.branches) + len(repo.tags) + len(repo.bookmarks)
        assert items == repo_refs

    def test_index_shows_missing_requirements_message(
            self, backend, autologin_user):
        repo_name = backend.repo_name
        scm_patcher = mock.patch.object(
            Repository, 'scm_instance', side_effect=RepositoryRequirementError)

        with scm_patcher:
            response = self.app.get(route_path('repo_summary', repo_name=repo_name))
        assert_response = AssertResponse(response)
        assert_response.element_contains(
            '.main .alert-warning strong', 'Missing requirements')
        assert_response.element_contains(
            '.main .alert-warning',
            'Commits cannot be displayed, because this repository '
            'uses one or more extensions, which was not enabled.')

    def test_missing_requirements_page_does_not_contains_switch_to(
            self, autologin_user, backend):
        repo_name = backend.repo_name
        scm_patcher = mock.patch.object(
            Repository, 'scm_instance', side_effect=RepositoryRequirementError)

        with scm_patcher:
            response = self.app.get(route_path('repo_summary', repo_name=repo_name))
        response.mustcontain(no='Switch To')


@pytest.mark.usefixtures('app')
class TestRepoLocation(object):

    @pytest.mark.parametrize("suffix", [u'', u'ąęł'], ids=['', 'non-ascii'])
    def test_missing_filesystem_repo(
            self, autologin_user, backend, suffix, csrf_token):
        repo = backend.create_repo(name_suffix=suffix)
        repo_name = repo.repo_name

        # delete from file system
        RepoModel()._delete_filesystem_repo(repo)

        # test if the repo is still in the database
        new_repo = RepoModel().get_by_repo_name(repo_name)
        assert new_repo.repo_name == repo_name

        # check if repo is not in the filesystem
        assert not repo_on_filesystem(repo_name)

        response = self.app.get(
            route_path('repo_summary', repo_name=safe_str(repo_name)), status=302)

        msg = 'The repository `%s` cannot be loaded in filesystem. ' \
              'Please check if it exist, or is not damaged.' % repo_name
        assert_session_flash(response, msg)

    @pytest.mark.parametrize("suffix", [u'', u'ąęł'], ids=['', 'non-ascii'])
    def test_missing_filesystem_repo_on_repo_check(
            self, autologin_user, backend, suffix, csrf_token):
        repo = backend.create_repo(name_suffix=suffix)
        repo_name = repo.repo_name

        # delete from file system
        RepoModel()._delete_filesystem_repo(repo)

        # test if the repo is still in the database
        new_repo = RepoModel().get_by_repo_name(repo_name)
        assert new_repo.repo_name == repo_name

        # check if repo is not in the filesystem
        assert not repo_on_filesystem(repo_name)

        # flush the session
        self.app.get(
            route_path('repo_summary', repo_name=safe_str(repo_name)),
            status=302)

        response = self.app.get(
            route_path('repo_creating_check', repo_name=safe_str(repo_name)),
            status=200)
        msg = 'The repository `%s` cannot be loaded in filesystem. ' \
              'Please check if it exist, or is not damaged.' % repo_name
        assert_session_flash(response, msg )


@pytest.fixture()
def summary_view(context_stub, request_stub, user_util):
    """
    Bootstrap view to test the view functions
    """
    request_stub.matched_route = AttributeDict(name='test_view')

    request_stub.user = user_util.create_user().AuthUser()
    request_stub.db_repo = user_util.create_repo()

    view = RepoSummaryView(context=context_stub, request=request_stub)
    return view


@pytest.mark.usefixtures('app')
class TestCreateReferenceData(object):

    @pytest.fixture
    def example_refs(self):
        section_1_refs = OrderedDict((('a', 'a_id'), ('b', 'b_id')))
        example_refs = [
            ('section_1', section_1_refs, 't1'),
            ('section_2', {'c': 'c_id'}, 't2'),
        ]
        return example_refs

    def test_generates_refs_based_on_commit_ids(self, example_refs, summary_view):
        repo = mock.Mock()
        repo.name = 'test-repo'
        repo.alias = 'git'
        full_repo_name = 'pytest-repo-group/' + repo.name

        result = summary_view._create_reference_data(
            repo, full_repo_name, example_refs)

        expected_files_url = '/{}/files/'.format(full_repo_name)
        expected_result = [
            {
                'children': [
                    {
                        'id': 'a', 'raw_id': 'a_id', 'text': 'a', 'type': 't1',
                        'files_url': expected_files_url + 'a/?at=a',
                    },
                    {
                        'id': 'b', 'raw_id': 'b_id', 'text': 'b', 'type': 't1',
                        'files_url': expected_files_url + 'b/?at=b',
                    }
                ],
                'text': 'section_1'
            },
            {
                'children': [
                    {
                        'id': 'c', 'raw_id': 'c_id', 'text': 'c', 'type': 't2',
                        'files_url': expected_files_url + 'c/?at=c',
                    }
                ],
                'text': 'section_2'
            }]
        assert result == expected_result

    def test_generates_refs_with_path_for_svn(self, example_refs, summary_view):
        repo = mock.Mock()
        repo.name = 'test-repo'
        repo.alias = 'svn'
        full_repo_name = 'pytest-repo-group/' + repo.name

        result = summary_view._create_reference_data(
            repo, full_repo_name, example_refs)

        expected_files_url = '/{}/files/'.format(full_repo_name)
        expected_result = [
            {
                'children': [
                    {
                        'id': 'a@a_id', 'raw_id': 'a_id',
                        'text': 'a', 'type': 't1',
                        'files_url': expected_files_url + 'a_id/a?at=a',
                    },
                    {
                        'id': 'b@b_id', 'raw_id': 'b_id',
                        'text': 'b', 'type': 't1',
                        'files_url': expected_files_url + 'b_id/b?at=b',
                    }
                ],
                'text': 'section_1'
            },
            {
                'children': [
                    {
                        'id': 'c@c_id', 'raw_id': 'c_id',
                        'text': 'c', 'type': 't2',
                        'files_url': expected_files_url + 'c_id/c?at=c',
                    }
                ],
                'text': 'section_2'
            }
        ]
        assert result == expected_result


class TestCreateFilesUrl(object):

    def test_creates_non_svn_url(self, app, summary_view):
        repo = mock.Mock()
        repo.name = 'abcde'
        full_repo_name = 'test-repo-group/' + repo.name
        ref_name = 'branch1'
        raw_id = 'deadbeef0123456789'
        is_svn = False

        with mock.patch('rhodecode.lib.helpers.route_path') as url_mock:
            result = summary_view._create_files_url(
                repo, full_repo_name, ref_name, raw_id, is_svn)
        url_mock.assert_called_once_with(
            'repo_files', repo_name=full_repo_name, commit_id=ref_name,
            f_path='', _query=dict(at=ref_name))
        assert result == url_mock.return_value

    def test_creates_svn_url(self, app, summary_view):
        repo = mock.Mock()
        repo.name = 'abcde'
        full_repo_name = 'test-repo-group/' + repo.name
        ref_name = 'branch1'
        raw_id = 'deadbeef0123456789'
        is_svn = True

        with mock.patch('rhodecode.lib.helpers.route_path') as url_mock:
            result = summary_view._create_files_url(
                repo, full_repo_name, ref_name, raw_id, is_svn)
        url_mock.assert_called_once_with(
            'repo_files', repo_name=full_repo_name, f_path=ref_name,
            commit_id=raw_id, _query=dict(at=ref_name))
        assert result == url_mock.return_value

    def test_name_has_slashes(self, app, summary_view):
        repo = mock.Mock()
        repo.name = 'abcde'
        full_repo_name = 'test-repo-group/' + repo.name
        ref_name = 'branch1/branch2'
        raw_id = 'deadbeef0123456789'
        is_svn = False

        with mock.patch('rhodecode.lib.helpers.route_path') as url_mock:
            result = summary_view._create_files_url(
                repo, full_repo_name, ref_name, raw_id, is_svn)
        url_mock.assert_called_once_with(
            'repo_files', repo_name=full_repo_name, commit_id=raw_id,
            f_path='', _query=dict(at=ref_name))
        assert result == url_mock.return_value


class TestReferenceItems(object):
    repo = mock.Mock()
    repo.name = 'pytest-repo'
    repo_full_name = 'pytest-repo-group/' + repo.name
    ref_type = 'branch'
    fake_url = '/abcde/'

    @staticmethod
    def _format_function(name, id_):
        return 'format_function_{}_{}'.format(name, id_)

    def test_creates_required_amount_of_items(self, summary_view):
        amount = 100
        refs = {
            'ref{}'.format(i): '{0:040d}'.format(i)
            for i in range(amount)
        }

        url_patcher = mock.patch.object(summary_view, '_create_files_url')
        svn_patcher = mock.patch('rhodecode.lib.helpers.is_svn',
                                 return_value=False)

        with url_patcher as url_mock, svn_patcher:
            result = summary_view._create_reference_items(
                self.repo, self.repo_full_name, refs, self.ref_type,
                self._format_function)
        assert len(result) == amount
        assert url_mock.call_count == amount

    def test_single_item_details(self, summary_view):
        ref_name = 'ref1'
        ref_id = 'deadbeef'
        refs = {
            ref_name: ref_id
        }

        svn_patcher = mock.patch('rhodecode.lib.helpers.is_svn',
                                 return_value=False)

        url_patcher = mock.patch.object(
            summary_view, '_create_files_url', return_value=self.fake_url)

        with url_patcher as url_mock, svn_patcher:
            result = summary_view._create_reference_items(
                self.repo, self.repo_full_name, refs, self.ref_type,
                self._format_function)

        url_mock.assert_called_once_with(
            self.repo, self.repo_full_name, ref_name, ref_id, False)
        expected_result = [
            {
                'text': ref_name,
                'id': self._format_function(ref_name, ref_id),
                'raw_id': ref_id,
                'type': self.ref_type,
                'files_url': self.fake_url
            }
        ]
        assert result == expected_result
