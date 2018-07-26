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

import os

import mock
import pytest

from rhodecode.apps.repository.views.repo_files import RepoFilesView
from rhodecode.lib import helpers as h
from rhodecode.lib.compat import OrderedDict
from rhodecode.lib.ext_json import json
from rhodecode.lib.vcs import nodes

from rhodecode.lib.vcs.conf import settings
from rhodecode.tests import assert_session_flash
from rhodecode.tests.fixture import Fixture
from rhodecode.model.db import Session

fixture = Fixture()


def get_node_history(backend_type):
    return {
        'hg': json.loads(fixture.load_resource('hg_node_history_response.json')),
        'git': json.loads(fixture.load_resource('git_node_history_response.json')),
        'svn': json.loads(fixture.load_resource('svn_node_history_response.json')),
    }[backend_type]


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_summary': '/{repo_name}',
        'repo_archivefile': '/{repo_name}/archive/{fname}',
        'repo_files_diff': '/{repo_name}/diff/{f_path}',
        'repo_files_diff_2way_redirect':  '/{repo_name}/diff-2way/{f_path}',
        'repo_files': '/{repo_name}/files/{commit_id}/{f_path}',
        'repo_files:default_path': '/{repo_name}/files/{commit_id}/',
        'repo_files:default_commit': '/{repo_name}/files',
        'repo_files:rendered': '/{repo_name}/render/{commit_id}/{f_path}',
        'repo_files:annotated': '/{repo_name}/annotate/{commit_id}/{f_path}',
        'repo_files:annotated_previous': '/{repo_name}/annotate-previous/{commit_id}/{f_path}',
        'repo_files_nodelist': '/{repo_name}/nodelist/{commit_id}/{f_path}',
        'repo_file_raw': '/{repo_name}/raw/{commit_id}/{f_path}',
        'repo_file_download': '/{repo_name}/download/{commit_id}/{f_path}',
        'repo_file_history': '/{repo_name}/history/{commit_id}/{f_path}',
        'repo_file_authors': '/{repo_name}/authors/{commit_id}/{f_path}',
        'repo_files_remove_file': '/{repo_name}/remove_file/{commit_id}/{f_path}',
        'repo_files_delete_file': '/{repo_name}/delete_file/{commit_id}/{f_path}',
        'repo_files_edit_file': '/{repo_name}/edit_file/{commit_id}/{f_path}',
        'repo_files_update_file': '/{repo_name}/update_file/{commit_id}/{f_path}',
        'repo_files_add_file': '/{repo_name}/add_file/{commit_id}/{f_path}',
        'repo_files_create_file': '/{repo_name}/create_file/{commit_id}/{f_path}',
        'repo_nodetree_full': '/{repo_name}/nodetree_full/{commit_id}/{f_path}',
        'repo_nodetree_full:default_path': '/{repo_name}/nodetree_full/{commit_id}/',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


def assert_files_in_response(response, files, params):
    template = (
        'href="/%(repo_name)s/files/%(commit_id)s/%(name)s"')
    _assert_items_in_response(response, files, template, params)


def assert_dirs_in_response(response, dirs, params):
    template = (
        'href="/%(repo_name)s/files/%(commit_id)s/%(name)s"')
    _assert_items_in_response(response, dirs, template, params)


def _assert_items_in_response(response, items, template, params):
    for item in items:
        item_params = {'name': item}
        item_params.update(params)
        response.mustcontain(template % item_params)


def assert_timeago_in_response(response, items, params):
    for item in items:
        response.mustcontain(h.age_component(params['date']))


@pytest.mark.usefixtures("app")
class TestFilesViews(object):

    def test_show_files(self, backend):
        response = self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'))
        commit = backend.repo.get_commit()

        params = {
            'repo_name': backend.repo_name,
            'commit_id': commit.raw_id,
            'date': commit.date
        }
        assert_dirs_in_response(response, ['docs', 'vcs'], params)
        files = [
            '.gitignore',
            '.hgignore',
            '.hgtags',
            # TODO: missing in Git
            # '.travis.yml',
            'MANIFEST.in',
            'README.rst',
            # TODO: File is missing in svn repository
            # 'run_test_and_report.sh',
            'setup.cfg',
            'setup.py',
            'test_and_report.sh',
            'tox.ini',
        ]
        assert_files_in_response(response, files, params)
        assert_timeago_in_response(response, files, params)

    def test_show_files_links_submodules_with_absolute_url(self, backend_hg):
        repo = backend_hg['subrepos']
        response = self.app.get(
            route_path('repo_files',
                       repo_name=repo.repo_name,
                       commit_id='tip', f_path='/'))
        assert_response = response.assert_response()
        assert_response.contains_one_link(
            'absolute-path @ 000000000000', 'http://example.com/absolute-path')

    def test_show_files_links_submodules_with_absolute_url_subpaths(
            self, backend_hg):
        repo = backend_hg['subrepos']
        response = self.app.get(
            route_path('repo_files',
                       repo_name=repo.repo_name,
                       commit_id='tip', f_path='/'))
        assert_response = response.assert_response()
        assert_response.contains_one_link(
            'subpaths-path @ 000000000000',
            'http://sub-base.example.com/subpaths-path')

    @pytest.mark.xfail_backends("svn", reason="Depends on branch support")
    def test_files_menu(self, backend):
        new_branch = "temp_branch_name"
        commits = [
            {'message': 'a'},
            {'message': 'b', 'branch': new_branch}
        ]
        backend.create_repo(commits)
        backend.repo.landing_rev = "branch:%s" % new_branch
        Session().commit()

        # get response based on tip and not new commit
        response = self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'))

        # make sure Files menu url is not tip but new commit
        landing_rev = backend.repo.landing_rev[1]
        files_url = route_path('repo_files:default_path',
                               repo_name=backend.repo_name,
                               commit_id=landing_rev)

        assert landing_rev != 'tip'
        response.mustcontain(
            '<li class="active"><a class="menulink" href="%s">' % files_url)

    def test_show_files_commit(self, backend):
        commit = backend.repo.get_commit(commit_idx=32)

        response = self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/'))

        dirs = ['docs', 'tests']
        files = ['README.rst']
        params = {
            'repo_name': backend.repo_name,
            'commit_id': commit.raw_id,
        }
        assert_dirs_in_response(response, dirs, params)
        assert_files_in_response(response, files, params)

    def test_show_files_different_branch(self, backend):
        branches = dict(
            hg=(150, ['git']),
            # TODO: Git test repository does not contain other branches
            git=(633, ['master']),
            # TODO: Branch support in Subversion
            svn=(150, [])
        )
        idx, branches = branches[backend.alias]
        commit = backend.repo.get_commit(commit_idx=idx)
        response = self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/'))

        assert_response = response.assert_response()
        for branch in branches:
            assert_response.element_contains('.tags .branchtag', branch)

    def test_show_files_paging(self, backend):
        repo = backend.repo
        indexes = [73, 92, 109, 1, 0]
        idx_map = [(rev, repo.get_commit(commit_idx=rev).raw_id)
                   for rev in indexes]

        for idx in idx_map:
            response = self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id=idx[1], f_path='/'))

            response.mustcontain("""r%s:%s""" % (idx[0], idx[1][:8]))

    def test_file_source(self, backend):
        commit = backend.repo.get_commit(commit_idx=167)
        response = self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='vcs/nodes.py'))

        msgbox = """<div class="commit right-content">%s</div>"""
        response.mustcontain(msgbox % (commit.message, ))

        assert_response = response.assert_response()
        if commit.branch:
            assert_response.element_contains(
                '.tags.tags-main .branchtag', commit.branch)
        if commit.tags:
            for tag in commit.tags:
                assert_response.element_contains('.tags.tags-main .tagtag', tag)

    def test_file_source_annotated(self, backend):
        response = self.app.get(
            route_path('repo_files:annotated',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='vcs/nodes.py'))
        expected_commits = {
            'hg': 'r356',
            'git': 'r345',
            'svn': 'r208',
        }
        response.mustcontain(expected_commits[backend.alias])

    def test_file_source_authors(self, backend):
        response = self.app.get(
            route_path('repo_file_authors',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='vcs/nodes.py'))
        expected_authors = {
            'hg': ('Marcin Kuzminski', 'Lukasz Balcerzak'),
            'git': ('Marcin Kuzminski', 'Lukasz Balcerzak'),
            'svn': ('marcin', 'lukasz'),
        }

        for author in expected_authors[backend.alias]:
            response.mustcontain(author)

    def test_file_source_authors_with_annotation(self, backend):
        response = self.app.get(
            route_path('repo_file_authors',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='vcs/nodes.py',
                       params=dict(annotate=1)))
        expected_authors = {
            'hg': ('Marcin Kuzminski', 'Lukasz Balcerzak'),
            'git': ('Marcin Kuzminski', 'Lukasz Balcerzak'),
            'svn': ('marcin', 'lukasz'),
        }

        for author in expected_authors[backend.alias]:
            response.mustcontain(author)

    def test_file_source_history(self, backend, xhr_header):
        response = self.app.get(
            route_path('repo_file_history',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='vcs/nodes.py'),
            extra_environ=xhr_header)
        assert get_node_history(backend.alias) == json.loads(response.body)

    def test_file_source_history_svn(self, backend_svn, xhr_header):
        simple_repo = backend_svn['svn-simple-layout']
        response = self.app.get(
            route_path('repo_file_history',
                       repo_name=simple_repo.repo_name,
                       commit_id='tip', f_path='trunk/example.py'),
            extra_environ=xhr_header)

        expected_data = json.loads(
            fixture.load_resource('svn_node_history_branches.json'))
        assert expected_data == response.json

    def test_file_source_history_with_annotation(self, backend, xhr_header):
        response = self.app.get(
            route_path('repo_file_history',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='vcs/nodes.py',
                       params=dict(annotate=1)),

            extra_environ=xhr_header)
        assert get_node_history(backend.alias) == json.loads(response.body)

    def test_tree_search_top_level(self, backend, xhr_header):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_files_nodelist',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/'),
            extra_environ=xhr_header)
        assert 'nodes' in response.json
        assert {'name': 'docs', 'type': 'dir'} in response.json['nodes']

    def test_tree_search_missing_xhr(self, backend):
        self.app.get(
            route_path('repo_files_nodelist',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'),
            status=404)

    def test_tree_search_at_path(self, backend, xhr_header):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_files_nodelist',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/docs'),
            extra_environ=xhr_header)
        assert 'nodes' in response.json
        nodes = response.json['nodes']
        assert {'name': 'docs/api', 'type': 'dir'} in nodes
        assert {'name': 'docs/index.rst', 'type': 'file'} in nodes

    def test_tree_search_at_path_2nd_level(self, backend, xhr_header):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_files_nodelist',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/docs/api'),
            extra_environ=xhr_header)
        assert 'nodes' in response.json
        nodes = response.json['nodes']
        assert {'name': 'docs/api/index.rst', 'type': 'file'} in nodes

    def test_tree_search_at_path_missing_xhr(self, backend):
        self.app.get(
            route_path('repo_files_nodelist',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/docs'),
            status=404)

    def test_nodetree(self, backend, xhr_header):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_nodetree_full',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/'),
            extra_environ=xhr_header)

        assert_response = response.assert_response()

        for attr in ['data-commit-id', 'data-date', 'data-author']:
            elements = assert_response.get_elements('[{}]'.format(attr))
            assert len(elements) > 1

            for element in elements:
                assert element.get(attr)

    def test_nodetree_if_file(self, backend, xhr_header):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_nodetree_full',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='README.rst'),
            extra_environ=xhr_header)
        assert response.body == ''

    def test_nodetree_wrong_path(self, backend, xhr_header):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_nodetree_full',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='/dont-exist'),
            extra_environ=xhr_header)

        err = 'error: There is no file nor ' \
              'directory at the given path'
        assert err in response.body

    def test_nodetree_missing_xhr(self, backend):
        self.app.get(
            route_path('repo_nodetree_full',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'),
            status=404)


@pytest.mark.usefixtures("app", "autologin_user")
class TestRawFileHandling(object):

    def test_download_file(self, backend):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_file_download',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='vcs/nodes.py'),)

        assert response.content_disposition == "attachment; filename=nodes.py"
        assert response.content_type == "text/x-python"

    def test_download_file_wrong_cs(self, backend):
        raw_id = u'ERRORce30c96924232dffcd24178a07ffeb5dfc'

        response = self.app.get(
            route_path('repo_file_download',
                       repo_name=backend.repo_name,
                       commit_id=raw_id, f_path='vcs/nodes.svg'),
            status=404)

        msg = """No such commit exists for this repository"""
        response.mustcontain(msg)

    def test_download_file_wrong_f_path(self, backend):
        commit = backend.repo.get_commit(commit_idx=173)
        f_path = 'vcs/ERRORnodes.py'

        response = self.app.get(
            route_path('repo_file_download',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path=f_path),
            status=404)

        msg = (
            "There is no file nor directory at the given path: "
            "`%s` at commit %s" % (f_path, commit.short_id))
        response.mustcontain(msg)

    def test_file_raw(self, backend):
        commit = backend.repo.get_commit(commit_idx=173)
        response = self.app.get(
            route_path('repo_file_raw',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path='vcs/nodes.py'),)

        assert response.content_type == "text/plain"

    def test_file_raw_binary(self, backend):
        commit = backend.repo.get_commit()
        response = self.app.get(
            route_path('repo_file_raw',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id,
                       f_path='docs/theme/ADC/static/breadcrumb_background.png'),)

        assert response.content_disposition == 'inline'

    def test_raw_file_wrong_cs(self, backend):
        raw_id = u'ERRORcce30c96924232dffcd24178a07ffeb5dfc'

        response = self.app.get(
            route_path('repo_file_raw',
                       repo_name=backend.repo_name,
                       commit_id=raw_id, f_path='vcs/nodes.svg'),
            status=404)

        msg = """No such commit exists for this repository"""
        response.mustcontain(msg)

    def test_raw_wrong_f_path(self, backend):
        commit = backend.repo.get_commit(commit_idx=173)
        f_path = 'vcs/ERRORnodes.py'
        response = self.app.get(
            route_path('repo_file_raw',
                       repo_name=backend.repo_name,
                       commit_id=commit.raw_id, f_path=f_path),
            status=404)

        msg = (
            "There is no file nor directory at the given path: "
            "`%s` at commit %s" % (f_path, commit.short_id))
        response.mustcontain(msg)

    def test_raw_svg_should_not_be_rendered(self, backend):
        backend.create_repo()
        backend.ensure_file("xss.svg")
        response = self.app.get(
            route_path('repo_file_raw',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='xss.svg'),)
        # If the content type is image/svg+xml then it allows to render HTML
        # and malicious SVG.
        assert response.content_type == "text/plain"


@pytest.mark.usefixtures("app")
class TestRepositoryArchival(object):

    def test_archival(self, backend):
        backend.enable_downloads()
        commit = backend.repo.get_commit(commit_idx=173)
        for archive, info in settings.ARCHIVE_SPECS.items():
            mime_type, arch_ext = info
            short = commit.short_id + arch_ext
            fname = commit.raw_id + arch_ext
            filename = '%s-%s' % (backend.repo_name, short)
            response = self.app.get(
                route_path('repo_archivefile',
                           repo_name=backend.repo_name,
                           fname=fname))

            assert response.status == '200 OK'
            headers = [
                ('Content-Disposition', 'attachment; filename=%s' % filename),
                ('Content-Type', '%s' % mime_type),
            ]

            for header in headers:
                assert header in response.headers.items()

    @pytest.mark.parametrize('arch_ext',[
        'tar', 'rar', 'x', '..ax', '.zipz', 'tar.gz.tar'])
    def test_archival_wrong_ext(self, backend, arch_ext):
        backend.enable_downloads()
        commit = backend.repo.get_commit(commit_idx=173)

        fname = commit.raw_id + '.' + arch_ext

        response = self.app.get(
            route_path('repo_archivefile',
                       repo_name=backend.repo_name,
                       fname=fname))
        response.mustcontain(
            'Unknown archive type for: `{}`'.format(fname))

    @pytest.mark.parametrize('commit_id', [
        '00x000000', 'tar', 'wrong', '@$@$42413232', '232dffcd'])
    def test_archival_wrong_commit_id(self, backend, commit_id):
        backend.enable_downloads()
        fname = '%s.zip' % commit_id

        response = self.app.get(
            route_path('repo_archivefile',
                       repo_name=backend.repo_name,
                       fname=fname))
        response.mustcontain('Unknown commit_id')


@pytest.mark.usefixtures("app")
class TestFilesDiff(object):

    @pytest.mark.parametrize("diff", ['diff', 'download', 'raw'])
    def test_file_full_diff(self, backend, diff):
        commit1 = backend.repo.get_commit(commit_idx=-1)
        commit2 = backend.repo.get_commit(commit_idx=-2)

        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=backend.repo_name,
                       f_path='README'),
            params={
                'diff1': commit2.raw_id,
                'diff2': commit1.raw_id,
                'fulldiff': '1',
                'diff': diff,
            })

        if diff == 'diff':
            # use redirect since this is OLD view redirecting to compare page
            response = response.follow()

        # It's a symlink to README.rst
        response.mustcontain('README.rst')
        response.mustcontain('No newline at end of file')

    def test_file_binary_diff(self, backend):
        commits = [
            {'message': 'First commit'},
            {'message': 'Commit with binary',
             'added': [nodes.FileNode('file.bin', content='\0BINARY\0')]},
        ]
        repo = backend.create_repo(commits=commits)

        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=backend.repo_name,
                       f_path='file.bin'),
            params={
                'diff1': repo.get_commit(commit_idx=0).raw_id,
                'diff2': repo.get_commit(commit_idx=1).raw_id,
                'fulldiff': '1',
                'diff': 'diff',
            })
        # use redirect since this is OLD view redirecting to compare page
        response = response.follow()
        response.mustcontain('Expand 1 commit')
        response.mustcontain('1 file changed: 0 inserted, 0 deleted')

        if backend.alias == 'svn':
            response.mustcontain('new file 10644')
            # TODO(marcink): SVN doesn't yet detect binary changes
        else:
            response.mustcontain('new file 100644')
            response.mustcontain('binary diff hidden')

    def test_diff_2way(self, backend):
        commit1 = backend.repo.get_commit(commit_idx=-1)
        commit2 = backend.repo.get_commit(commit_idx=-2)
        response = self.app.get(
            route_path('repo_files_diff_2way_redirect',
                       repo_name=backend.repo_name,
                       f_path='README'),
            params={
                'diff1': commit2.raw_id,
                'diff2': commit1.raw_id,
            })
        # use redirect since this is OLD view redirecting to compare page
        response = response.follow()

        # It's a symlink to README.rst
        response.mustcontain('README.rst')
        response.mustcontain('No newline at end of file')

    def test_requires_one_commit_id(self, backend, autologin_user):
        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=backend.repo_name,
                       f_path='README.rst'),
            status=400)
        response.mustcontain(
            'Need query parameter', 'diff1', 'diff2', 'to generate a diff.')

    def test_returns_no_files_if_file_does_not_exist(self, vcsbackend):
        repo = vcsbackend.repo
        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=repo.name,
                       f_path='does-not-exist-in-any-commit'),
            params={
                'diff1': repo[0].raw_id,
                'diff2': repo[1].raw_id
            })

        response = response.follow()
        response.mustcontain('No files')

    def test_returns_redirect_if_file_not_changed(self, backend):
        commit = backend.repo.get_commit(commit_idx=-1)
        response = self.app.get(
            route_path('repo_files_diff_2way_redirect',
                       repo_name=backend.repo_name,
                       f_path='README'),
            params={
                'diff1': commit.raw_id,
                'diff2': commit.raw_id,
            })

        response = response.follow()
        response.mustcontain('No files')
        response.mustcontain('No commits in this compare')

    def test_supports_diff_to_different_path_svn(self, backend_svn):
        #TODO: check this case
        return

        repo = backend_svn['svn-simple-layout'].scm_instance()
        commit_id_1 = '24'
        commit_id_2 = '26'

        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=backend_svn.repo_name,
                       f_path='trunk/example.py'),
            params={
                'diff1': 'tags/v0.2/example.py@' + commit_id_1,
                'diff2': commit_id_2,
            })

        response = response.follow()
        response.mustcontain(
            # diff contains this
            "Will print out a useful message on invocation.")

        # Note: Expecting that we indicate the user what's being compared
        response.mustcontain("trunk/example.py")
        response.mustcontain("tags/v0.2/example.py")

    def test_show_rev_redirects_to_svn_path(self, backend_svn):
        #TODO: check this case
        return

        repo = backend_svn['svn-simple-layout'].scm_instance()
        commit_id = repo[-1].raw_id

        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=backend_svn.repo_name,
                       f_path='trunk/example.py'),
            params={
                'diff1': 'branches/argparse/example.py@' + commit_id,
                'diff2': commit_id,
            },
            status=302)
        response = response.follow()
        assert response.headers['Location'].endswith(
            'svn-svn-simple-layout/files/26/branches/argparse/example.py')

    def test_show_rev_and_annotate_redirects_to_svn_path(self, backend_svn):
        #TODO: check this case
        return

        repo = backend_svn['svn-simple-layout'].scm_instance()
        commit_id = repo[-1].raw_id
        response = self.app.get(
            route_path('repo_files_diff',
                       repo_name=backend_svn.repo_name,
                       f_path='trunk/example.py'),
            params={
                'diff1': 'branches/argparse/example.py@' + commit_id,
                'diff2': commit_id,
                'show_rev': 'Show at Revision',
                'annotate': 'true',
            },
            status=302)
        response = response.follow()
        assert response.headers['Location'].endswith(
            'svn-svn-simple-layout/annotate/26/branches/argparse/example.py')


@pytest.mark.usefixtures("app", "autologin_user")
class TestModifyFilesWithWebInterface(object):

    def test_add_file_view(self, backend):
        self.app.get(
            route_path('repo_files_add_file',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/')
            )

    @pytest.mark.xfail_backends("svn", reason="Depends on online editing")
    def test_add_file_into_repo_missing_content(self, backend, csrf_token):
        repo = backend.create_repo()
        filename = 'init.py'
        response = self.app.post(
            route_path('repo_files_create_file',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'),
            params={
                'content': "",
                'filename': filename,
                'location': "",
                'csrf_token': csrf_token,
            },
            status=302)
        assert_session_flash(response,
            'Successfully committed new file `{}`'.format(
                os.path.join(filename)))

    def test_add_file_into_repo_missing_filename(self, backend, csrf_token):
        response = self.app.post(
            route_path('repo_files_create_file',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'),
            params={
                'content': "foo",
                'csrf_token': csrf_token,
            },
            status=302)

        assert_session_flash(response, 'No filename')

    def test_add_file_into_repo_errors_and_no_commits(
            self, backend, csrf_token):
        repo = backend.create_repo()
        # Create a file with no filename, it will display an error but
        # the repo has no commits yet
        response = self.app.post(
            route_path('repo_files_create_file',
                       repo_name=repo.repo_name,
                       commit_id='tip', f_path='/'),
            params={
                'content': "foo",
                'csrf_token': csrf_token,
            },
            status=302)

        assert_session_flash(response, 'No filename')

        # Not allowed, redirect to the summary
        redirected = response.follow()
        summary_url = h.route_path('repo_summary', repo_name=repo.repo_name)

        # As there are no commits, displays the summary page with the error of
        # creating a file with no filename

        assert redirected.request.path == summary_url

    @pytest.mark.parametrize("location, filename", [
        ('/abs', 'foo'),
        ('../rel', 'foo'),
        ('file/../foo', 'foo'),
    ])
    def test_add_file_into_repo_bad_filenames(
            self, location, filename, backend, csrf_token):
        response = self.app.post(
            route_path('repo_files_create_file',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path='/'),
            params={
                'content': "foo",
                'filename': filename,
                'location': location,
                'csrf_token': csrf_token,
            },
            status=302)

        assert_session_flash(
            response,
            'The location specified must be a relative path and must not '
            'contain .. in the path')

    @pytest.mark.parametrize("cnt, location, filename", [
        (1, '', 'foo.txt'),
        (2, 'dir', 'foo.rst'),
        (3, 'rel/dir', 'foo.bar'),
    ])
    def test_add_file_into_repo(self, cnt, location, filename, backend,
                                csrf_token):
        repo = backend.create_repo()
        response = self.app.post(
            route_path('repo_files_create_file',
                       repo_name=repo.repo_name,
                       commit_id='tip', f_path='/'),
            params={
                'content': "foo",
                'filename': filename,
                'location': location,
                'csrf_token': csrf_token,
            },
            status=302)
        assert_session_flash(response,
            'Successfully committed new file `{}`'.format(
                os.path.join(location, filename)))

    def test_edit_file_view(self, backend):
        response = self.app.get(
            route_path('repo_files_edit_file',
                       repo_name=backend.repo_name,
                       commit_id=backend.default_head_id,
                       f_path='vcs/nodes.py'),
            status=200)
        response.mustcontain("Module holding everything related to vcs nodes.")

    def test_edit_file_view_not_on_branch(self, backend):
        repo = backend.create_repo()
        backend.ensure_file("vcs/nodes.py")

        response = self.app.get(
            route_path('repo_files_edit_file',
                       repo_name=repo.repo_name,
                       commit_id='tip',
                       f_path='vcs/nodes.py'),
            status=302)
        assert_session_flash(
            response,
            'You can only edit files with commit being a valid branch')

    def test_edit_file_view_commit_changes(self, backend, csrf_token):
        repo = backend.create_repo()
        backend.ensure_file("vcs/nodes.py", content="print 'hello'")

        response = self.app.post(
            route_path('repo_files_update_file',
                       repo_name=repo.repo_name,
                       commit_id=backend.default_head_id,
                       f_path='vcs/nodes.py'),
            params={
                'content': "print 'hello world'",
                'message': 'I committed',
                'filename': "vcs/nodes.py",
                'csrf_token': csrf_token,
            },
            status=302)
        assert_session_flash(
            response, 'Successfully committed changes to file `vcs/nodes.py`')
        tip = repo.get_commit(commit_idx=-1)
        assert tip.message == 'I committed'

    def test_edit_file_view_commit_changes_default_message(self, backend,
                                                           csrf_token):
        repo = backend.create_repo()
        backend.ensure_file("vcs/nodes.py", content="print 'hello'")

        commit_id = (
            backend.default_branch_name or
            backend.repo.scm_instance().commit_ids[-1])

        response = self.app.post(
            route_path('repo_files_update_file',
                       repo_name=repo.repo_name,
                       commit_id=commit_id,
                       f_path='vcs/nodes.py'),
            params={
                'content': "print 'hello world'",
                'message': '',
                'filename': "vcs/nodes.py",
                'csrf_token': csrf_token,
            },
            status=302)
        assert_session_flash(
            response, 'Successfully committed changes to file `vcs/nodes.py`')
        tip = repo.get_commit(commit_idx=-1)
        assert tip.message == 'Edited file vcs/nodes.py via RhodeCode Enterprise'

    def test_delete_file_view(self, backend):
        self.app.get(
            route_path('repo_files_remove_file',
                       repo_name=backend.repo_name,
                       commit_id=backend.default_head_id,
                       f_path='vcs/nodes.py'),
            status=200)

    def test_delete_file_view_not_on_branch(self, backend):
        repo = backend.create_repo()
        backend.ensure_file('vcs/nodes.py')

        response = self.app.get(
            route_path('repo_files_remove_file',
                       repo_name=repo.repo_name,
                       commit_id='tip',
                       f_path='vcs/nodes.py'),
            status=302)
        assert_session_flash(
            response,
            'You can only delete files with commit being a valid branch')

    def test_delete_file_view_commit_changes(self, backend, csrf_token):
        repo = backend.create_repo()
        backend.ensure_file("vcs/nodes.py")

        response = self.app.post(
            route_path('repo_files_delete_file',
                       repo_name=repo.repo_name,
                       commit_id=backend.default_head_id,
                       f_path='vcs/nodes.py'),
            params={
                'message': 'i commited',
                'csrf_token': csrf_token,
            },
            status=302)
        assert_session_flash(
            response, 'Successfully deleted file `vcs/nodes.py`')


@pytest.mark.usefixtures("app")
class TestFilesViewOtherCases(object):

    def test_access_empty_repo_redirect_to_summary_with_alert_write_perms(
            self, backend_stub, autologin_regular_user, user_regular,
            user_util):

        repo = backend_stub.create_repo()
        user_util.grant_user_permission_to_repo(
            repo, user_regular, 'repository.write')
        response = self.app.get(
            route_path('repo_files',
                       repo_name=repo.repo_name,
                       commit_id='tip', f_path='/'))

        repo_file_add_url = route_path(
            'repo_files_add_file',
            repo_name=repo.repo_name,
            commit_id=0, f_path='') + '#edit'

        assert_session_flash(
            response,
            'There are no files yet. <a class="alert-link" '
            'href="{}">Click here to add a new file.</a>'
            .format(repo_file_add_url))

    def test_access_empty_repo_redirect_to_summary_with_alert_no_write_perms(
            self, backend_stub, autologin_regular_user):
        repo = backend_stub.create_repo()
        # init session for anon user
        route_path('repo_summary', repo_name=repo.repo_name)

        repo_file_add_url = route_path(
            'repo_files_add_file',
            repo_name=repo.repo_name,
            commit_id=0, f_path='') + '#edit'

        response = self.app.get(
            route_path('repo_files',
                       repo_name=repo.repo_name,
                       commit_id='tip', f_path='/'))

        assert_session_flash(response, no_=repo_file_add_url)

    @pytest.mark.parametrize('file_node', [
        'archive/file.zip',
        'diff/my-file.txt',
        'render.py',
        'render',
        'remove_file',
        'remove_file/to-delete.txt',
    ])
    def test_file_names_equal_to_routes_parts(self, backend, file_node):
        backend.create_repo()
        backend.ensure_file(file_node)

        self.app.get(
            route_path('repo_files',
                       repo_name=backend.repo_name,
                       commit_id='tip', f_path=file_node),
            status=200)


class TestAdjustFilePathForSvn(object):
    """
    SVN specific adjustments of node history in RepoFilesView.
    """

    def test_returns_path_relative_to_matched_reference(self):
        repo = self._repo(branches=['trunk'])
        self.assert_file_adjustment('trunk/file', 'file', repo)

    def test_does_not_modify_file_if_no_reference_matches(self):
        repo = self._repo(branches=['trunk'])
        self.assert_file_adjustment('notes/file', 'notes/file', repo)

    def test_does_not_adjust_partial_directory_names(self):
        repo = self._repo(branches=['trun'])
        self.assert_file_adjustment('trunk/file', 'trunk/file', repo)

    def test_is_robust_to_patterns_which_prefix_other_patterns(self):
        repo = self._repo(branches=['trunk', 'trunk/new', 'trunk/old'])
        self.assert_file_adjustment('trunk/new/file', 'file', repo)

    def assert_file_adjustment(self, f_path, expected, repo):
        result = RepoFilesView.adjust_file_path_for_svn(f_path, repo)
        assert result == expected

    def _repo(self, branches=None):
        repo = mock.Mock()
        repo.branches = OrderedDict((name, '0') for name in branches or [])
        repo.tags = {}
        return repo
