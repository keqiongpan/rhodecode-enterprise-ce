# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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
from rhodecode.apps._base import add_route_with_slash


def includeme(config):

    # Summary
    # NOTE(marcink): one additional route is defined in very bottom, catch
    # all pattern
    config.add_route(
        name='repo_summary_explicit',
        pattern='/{repo_name:.*?[^/]}/summary', repo_route=True)
    config.add_route(
        name='repo_summary_commits',
        pattern='/{repo_name:.*?[^/]}/summary-commits', repo_route=True)

    # repo commits
    config.add_route(
        name='repo_commit',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}', repo_route=True)

    # repo files
    config.add_route(
        name='repo_archivefile',
        pattern='/{repo_name:.*?[^/]}/archive/{fname}', repo_route=True)

    config.add_route(
        name='repo_files_diff',
        pattern='/{repo_name:.*?[^/]}/diff/{f_path:.*}', repo_route=True)
    config.add_route(  # legacy route to make old links work
        name='repo_files_diff_2way_redirect',
        pattern='/{repo_name:.*?[^/]}/diff-2way/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_files',
        pattern='/{repo_name:.*?[^/]}/files/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_route(
        name='repo_files:default_path',
        pattern='/{repo_name:.*?[^/]}/files/{commit_id}/', repo_route=True)
    config.add_route(
        name='repo_files:default_commit',
        pattern='/{repo_name:.*?[^/]}/files', repo_route=True)

    config.add_route(
        name='repo_files:rendered',
        pattern='/{repo_name:.*?[^/]}/render/{commit_id}/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_files:annotated',
        pattern='/{repo_name:.*?[^/]}/annotate/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_route(
        name='repo_files:annotated_previous',
        pattern='/{repo_name:.*?[^/]}/annotate-previous/{commit_id}/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_nodetree_full',
        pattern='/{repo_name:.*?[^/]}/nodetree_full/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_route(
        name='repo_nodetree_full:default_path',
        pattern='/{repo_name:.*?[^/]}/nodetree_full/{commit_id}/', repo_route=True)

    config.add_route(
        name='repo_files_nodelist',
        pattern='/{repo_name:.*?[^/]}/nodelist/{commit_id}/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_file_raw',
        pattern='/{repo_name:.*?[^/]}/raw/{commit_id}/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_file_download',
        pattern='/{repo_name:.*?[^/]}/download/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_route(  # backward compat to keep old links working
        name='repo_file_download:legacy',
        pattern='/{repo_name:.*?[^/]}/rawfile/{commit_id}/{f_path:.*}',
        repo_route=True)

    config.add_route(
        name='repo_file_history',
        pattern='/{repo_name:.*?[^/]}/history/{commit_id}/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_file_authors',
        pattern='/{repo_name:.*?[^/]}/authors/{commit_id}/{f_path:.*}', repo_route=True)

    config.add_route(
        name='repo_files_remove_file',
        pattern='/{repo_name:.*?[^/]}/remove_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_route(
        name='repo_files_delete_file',
        pattern='/{repo_name:.*?[^/]}/delete_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_route(
        name='repo_files_edit_file',
        pattern='/{repo_name:.*?[^/]}/edit_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_route(
        name='repo_files_update_file',
        pattern='/{repo_name:.*?[^/]}/update_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_route(
        name='repo_files_add_file',
        pattern='/{repo_name:.*?[^/]}/add_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_route(
        name='repo_files_create_file',
        pattern='/{repo_name:.*?[^/]}/create_file/{commit_id}/{f_path:.*}',
        repo_route=True)

    # refs data
    config.add_route(
        name='repo_refs_data',
        pattern='/{repo_name:.*?[^/]}/refs-data', repo_route=True)

    config.add_route(
        name='repo_refs_changelog_data',
        pattern='/{repo_name:.*?[^/]}/refs-data-changelog', repo_route=True)

    config.add_route(
        name='repo_stats',
        pattern='/{repo_name:.*?[^/]}/repo_stats/{commit_id}', repo_route=True)

    # Changelog
    config.add_route(
        name='repo_changelog',
        pattern='/{repo_name:.*?[^/]}/changelog', repo_route=True)
    config.add_route(
        name='repo_changelog_file',
        pattern='/{repo_name:.*?[^/]}/changelog/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_route(
        name='repo_changelog_elements',
        pattern='/{repo_name:.*?[^/]}/changelog_elements', repo_route=True)

    # Tags
    config.add_route(
        name='tags_home',
        pattern='/{repo_name:.*?[^/]}/tags', repo_route=True)

    # Branches
    config.add_route(
        name='branches_home',
        pattern='/{repo_name:.*?[^/]}/branches', repo_route=True)

    config.add_route(
        name='bookmarks_home',
        pattern='/{repo_name:.*?[^/]}/bookmarks', repo_route=True)

    # Pull Requests
    config.add_route(
        name='pullrequest_show',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id}',
        repo_route=True)

    config.add_route(
        name='pullrequest_show_all',
        pattern='/{repo_name:.*?[^/]}/pull-request',
        repo_route=True, repo_accepted_types=['hg', 'git'])

    config.add_route(
        name='pullrequest_show_all_data',
        pattern='/{repo_name:.*?[^/]}/pull-request-data',
        repo_route=True, repo_accepted_types=['hg', 'git'])

    # commits aka changesets
    # TODO(dan): handle default landing revision ?
    config.add_route(
        name='changeset_home',
        pattern='/{repo_name:.*?[^/]}/changeset/{revision}',
        repo_route=True)
    config.add_route(
        name='changeset_children',
        pattern='/{repo_name:.*?[^/]}/changeset_children/{revision}',
        repo_route=True)
    config.add_route(
        name='changeset_parents',
        pattern='/{repo_name:.*?[^/]}/changeset_parents/{revision}',
        repo_route=True)

    # Settings
    config.add_route(
        name='edit_repo',
        pattern='/{repo_name:.*?[^/]}/settings', repo_route=True)

    # Settings advanced
    config.add_route(
        name='edit_repo_advanced',
        pattern='/{repo_name:.*?[^/]}/settings/advanced', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_delete',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/delete', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_locking',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/locking', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_journal',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/journal', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_fork',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/fork', repo_route=True)

    # Caches
    config.add_route(
        name='edit_repo_caches',
        pattern='/{repo_name:.*?[^/]}/settings/caches', repo_route=True)

    # Permissions
    config.add_route(
        name='edit_repo_perms',
        pattern='/{repo_name:.*?[^/]}/settings/permissions', repo_route=True)

    # Repo Review Rules
    config.add_route(
        name='repo_reviewers',
        pattern='/{repo_name:.*?[^/]}/settings/review/rules', repo_route=True)

    config.add_route(
        name='repo_default_reviewers_data',
        pattern='/{repo_name:.*?[^/]}/settings/review/default-reviewers', repo_route=True)

    # Maintenance
    config.add_route(
        name='repo_maintenance',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance', repo_route=True)

    config.add_route(
        name='repo_maintenance_execute',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance/execute', repo_route=True)

    # Strip
    config.add_route(
        name='strip',
        pattern='/{repo_name:.*?[^/]}/settings/strip', repo_route=True)

    config.add_route(
        name='strip_check',
        pattern='/{repo_name:.*?[^/]}/settings/strip_check', repo_route=True)

    config.add_route(
        name='strip_execute',
        pattern='/{repo_name:.*?[^/]}/settings/strip_execute', repo_route=True)

    # ATOM/RSS Feed
    config.add_route(
        name='rss_feed_home',
        pattern='/{repo_name:.*?[^/]}/feed/rss', repo_route=True)

    config.add_route(
        name='atom_feed_home',
        pattern='/{repo_name:.*?[^/]}/feed/atom', repo_route=True)

    # NOTE(marcink): needs to be at the end for catch-all
    add_route_with_slash(
        config,
        name='repo_summary',
        pattern='/{repo_name:.*?[^/]}', repo_route=True)

    # Scan module for configuration decorators.
    config.scan()
