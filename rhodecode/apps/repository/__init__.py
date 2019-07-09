# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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

    # repo creating checks, special cases that aren't repo routes
    config.add_route(
        name='repo_creating',
        pattern='/{repo_name:.*?[^/]}/repo_creating')

    config.add_route(
        name='repo_creating_check',
        pattern='/{repo_name:.*?[^/]}/repo_creating_check')

    # Summary
    # NOTE(marcink): one additional route is defined in very bottom, catch
    # all pattern
    config.add_route(
        name='repo_summary_explicit',
        pattern='/{repo_name:.*?[^/]}/summary', repo_route=True)
    config.add_route(
        name='repo_summary_commits',
        pattern='/{repo_name:.*?[^/]}/summary-commits', repo_route=True)

    # Commits
    config.add_route(
        name='repo_commit',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_children',
        pattern='/{repo_name:.*?[^/]}/changeset_children/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_parents',
        pattern='/{repo_name:.*?[^/]}/changeset_parents/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_raw',
        pattern='/{repo_name:.*?[^/]}/changeset-diff/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_patch',
        pattern='/{repo_name:.*?[^/]}/changeset-patch/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_download',
        pattern='/{repo_name:.*?[^/]}/changeset-download/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_data',
        pattern='/{repo_name:.*?[^/]}/changeset-data/{commit_id}', repo_route=True)

    config.add_route(
        name='repo_commit_comment_create',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/create', repo_route=True)

    config.add_route(
        name='repo_commit_comment_preview',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/preview', repo_route=True)

    config.add_route(
        name='repo_commit_comment_delete',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/{comment_id}/delete', repo_route=True)

    # still working url for backward compat.
    config.add_route(
        name='repo_commit_raw_deprecated',
        pattern='/{repo_name:.*?[^/]}/raw-changeset/{commit_id}', repo_route=True)

    # Files
    config.add_route(
        name='repo_archivefile',
        pattern='/{repo_name:.*?[^/]}/archive/{fname:.*}', repo_route=True)

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
        name='repo_files_upload_file',
        pattern='/{repo_name:.*?[^/]}/upload_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_route(
        name='repo_files_create_file',
        pattern='/{repo_name:.*?[^/]}/create_file/{commit_id}/{f_path:.*}',
        repo_route=True)

    # Refs data
    config.add_route(
        name='repo_refs_data',
        pattern='/{repo_name:.*?[^/]}/refs-data', repo_route=True)

    config.add_route(
        name='repo_refs_changelog_data',
        pattern='/{repo_name:.*?[^/]}/refs-data-changelog', repo_route=True)

    config.add_route(
        name='repo_stats',
        pattern='/{repo_name:.*?[^/]}/repo_stats/{commit_id}', repo_route=True)

    # Commits
    config.add_route(
        name='repo_commits',
        pattern='/{repo_name:.*?[^/]}/commits', repo_route=True)
    config.add_route(
        name='repo_commits_file',
        pattern='/{repo_name:.*?[^/]}/commits/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_route(
        name='repo_commits_elements',
        pattern='/{repo_name:.*?[^/]}/commits_elements', repo_route=True)
    config.add_route(
        name='repo_commits_elements_file',
        pattern='/{repo_name:.*?[^/]}/commits_elements/{commit_id}/{f_path:.*}', repo_route=True)

    # Changelog (old deprecated name for commits page)
    config.add_route(
        name='repo_changelog',
        pattern='/{repo_name:.*?[^/]}/changelog', repo_route=True)
    config.add_route(
        name='repo_changelog_file',
        pattern='/{repo_name:.*?[^/]}/changelog/{commit_id}/{f_path:.*}', repo_route=True)

    # Compare
    config.add_route(
        name='repo_compare_select',
        pattern='/{repo_name:.*?[^/]}/compare', repo_route=True)

    config.add_route(
        name='repo_compare',
        pattern='/{repo_name:.*?[^/]}/compare/{source_ref_type}@{source_ref:.*?}...{target_ref_type}@{target_ref:.*?}', repo_route=True)

    # Tags
    config.add_route(
        name='tags_home',
        pattern='/{repo_name:.*?[^/]}/tags', repo_route=True)

    # Branches
    config.add_route(
        name='branches_home',
        pattern='/{repo_name:.*?[^/]}/branches', repo_route=True)

    # Bookmarks
    config.add_route(
        name='bookmarks_home',
        pattern='/{repo_name:.*?[^/]}/bookmarks', repo_route=True)

    # Forks
    config.add_route(
        name='repo_fork_new',
        pattern='/{repo_name:.*?[^/]}/fork', repo_route=True,
        repo_forbid_when_archived=True,
        repo_accepted_types=['hg', 'git'])

    config.add_route(
        name='repo_fork_create',
        pattern='/{repo_name:.*?[^/]}/fork/create', repo_route=True,
        repo_forbid_when_archived=True,
        repo_accepted_types=['hg', 'git'])

    config.add_route(
        name='repo_forks_show_all',
        pattern='/{repo_name:.*?[^/]}/forks', repo_route=True,
        repo_accepted_types=['hg', 'git'])
    config.add_route(
        name='repo_forks_data',
        pattern='/{repo_name:.*?[^/]}/forks/data', repo_route=True,
        repo_accepted_types=['hg', 'git'])

    # Pull Requests
    config.add_route(
        name='pullrequest_show',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}',
        repo_route=True)

    config.add_route(
        name='pullrequest_show_all',
        pattern='/{repo_name:.*?[^/]}/pull-request',
        repo_route=True, repo_accepted_types=['hg', 'git'])

    config.add_route(
        name='pullrequest_show_all_data',
        pattern='/{repo_name:.*?[^/]}/pull-request-data',
        repo_route=True, repo_accepted_types=['hg', 'git'])

    config.add_route(
        name='pullrequest_repo_refs',
        pattern='/{repo_name:.*?[^/]}/pull-request/refs/{target_repo_name:.*?[^/]}',
        repo_route=True)

    config.add_route(
        name='pullrequest_repo_targets',
        pattern='/{repo_name:.*?[^/]}/pull-request/repo-targets',
        repo_route=True)

    config.add_route(
        name='pullrequest_new',
        pattern='/{repo_name:.*?[^/]}/pull-request/new',
        repo_route=True, repo_accepted_types=['hg', 'git'],
        repo_forbid_when_archived=True)

    config.add_route(
        name='pullrequest_create',
        pattern='/{repo_name:.*?[^/]}/pull-request/create',
        repo_route=True, repo_accepted_types=['hg', 'git'],
        repo_forbid_when_archived=True)

    config.add_route(
        name='pullrequest_update',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/update',
        repo_route=True, repo_forbid_when_archived=True)

    config.add_route(
        name='pullrequest_merge',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/merge',
        repo_route=True, repo_forbid_when_archived=True)

    config.add_route(
        name='pullrequest_delete',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/delete',
        repo_route=True, repo_forbid_when_archived=True)

    config.add_route(
        name='pullrequest_comment_create',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/comment',
        repo_route=True)

    config.add_route(
        name='pullrequest_comment_delete',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/comment/{comment_id}/delete',
        repo_route=True, repo_accepted_types=['hg', 'git'])

    # Artifacts, (EE feature)
    config.add_route(
        name='repo_artifacts_list',
        pattern='/{repo_name:.*?[^/]}/artifacts', repo_route=True)

    # Settings
    config.add_route(
        name='edit_repo',
        pattern='/{repo_name:.*?[^/]}/settings', repo_route=True)
    # update is POST on edit_repo

    # Settings advanced
    config.add_route(
        name='edit_repo_advanced',
        pattern='/{repo_name:.*?[^/]}/settings/advanced', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_archive',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/archive', repo_route=True)
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

    config.add_route(
        name='edit_repo_advanced_hooks',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/hooks', repo_route=True)

    # Caches
    config.add_route(
        name='edit_repo_caches',
        pattern='/{repo_name:.*?[^/]}/settings/caches', repo_route=True)

    # Permissions
    config.add_route(
        name='edit_repo_perms',
        pattern='/{repo_name:.*?[^/]}/settings/permissions', repo_route=True)

    config.add_route(
        name='edit_repo_perms_set_private',
        pattern='/{repo_name:.*?[^/]}/settings/permissions/set_private', repo_route=True)

    # Permissions Branch (EE feature)
    config.add_route(
        name='edit_repo_perms_branch',
        pattern='/{repo_name:.*?[^/]}/settings/branch_permissions', repo_route=True)
    config.add_route(
        name='edit_repo_perms_branch_delete',
        pattern='/{repo_name:.*?[^/]}/settings/branch_permissions/{rule_id}/delete',
        repo_route=True)

    # Maintenance
    config.add_route(
        name='edit_repo_maintenance',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance', repo_route=True)

    config.add_route(
        name='edit_repo_maintenance_execute',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance/execute', repo_route=True)

    # Fields
    config.add_route(
        name='edit_repo_fields',
        pattern='/{repo_name:.*?[^/]}/settings/fields', repo_route=True)
    config.add_route(
        name='edit_repo_fields_create',
        pattern='/{repo_name:.*?[^/]}/settings/fields/create', repo_route=True)
    config.add_route(
        name='edit_repo_fields_delete',
        pattern='/{repo_name:.*?[^/]}/settings/fields/{field_id}/delete', repo_route=True)

    # Locking
    config.add_route(
        name='repo_edit_toggle_locking',
        pattern='/{repo_name:.*?[^/]}/settings/toggle_locking', repo_route=True)

    # Remote
    config.add_route(
        name='edit_repo_remote',
        pattern='/{repo_name:.*?[^/]}/settings/remote', repo_route=True)
    config.add_route(
        name='edit_repo_remote_pull',
        pattern='/{repo_name:.*?[^/]}/settings/remote/pull', repo_route=True)
    config.add_route(
        name='edit_repo_remote_push',
        pattern='/{repo_name:.*?[^/]}/settings/remote/push', repo_route=True)

    # Statistics
    config.add_route(
        name='edit_repo_statistics',
        pattern='/{repo_name:.*?[^/]}/settings/statistics', repo_route=True)
    config.add_route(
        name='edit_repo_statistics_reset',
        pattern='/{repo_name:.*?[^/]}/settings/statistics/update', repo_route=True)

    # Issue trackers
    config.add_route(
        name='edit_repo_issuetracker',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers', repo_route=True)
    config.add_route(
        name='edit_repo_issuetracker_test',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers/test', repo_route=True)
    config.add_route(
        name='edit_repo_issuetracker_delete',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers/delete', repo_route=True)
    config.add_route(
        name='edit_repo_issuetracker_update',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers/update', repo_route=True)

    # VCS Settings
    config.add_route(
        name='edit_repo_vcs',
        pattern='/{repo_name:.*?[^/]}/settings/vcs', repo_route=True)
    config.add_route(
        name='edit_repo_vcs_update',
        pattern='/{repo_name:.*?[^/]}/settings/vcs/update', repo_route=True)

    # svn pattern
    config.add_route(
        name='edit_repo_vcs_svn_pattern_delete',
        pattern='/{repo_name:.*?[^/]}/settings/vcs/svn_pattern/delete', repo_route=True)

    # Repo Review Rules (EE feature)
    config.add_route(
        name='repo_reviewers',
        pattern='/{repo_name:.*?[^/]}/settings/review/rules', repo_route=True)

    config.add_route(
        name='repo_default_reviewers_data',
        pattern='/{repo_name:.*?[^/]}/settings/review/default-reviewers', repo_route=True)

    # Repo Automation (EE feature)
    config.add_route(
        name='repo_automation',
        pattern='/{repo_name:.*?[^/]}/settings/automation', repo_route=True)

    # Strip
    config.add_route(
        name='edit_repo_strip',
        pattern='/{repo_name:.*?[^/]}/settings/strip', repo_route=True)

    config.add_route(
        name='strip_check',
        pattern='/{repo_name:.*?[^/]}/settings/strip_check', repo_route=True)

    config.add_route(
        name='strip_execute',
        pattern='/{repo_name:.*?[^/]}/settings/strip_execute', repo_route=True)

    # Audit logs
    config.add_route(
        name='edit_repo_audit_logs',
        pattern='/{repo_name:.*?[^/]}/settings/audit_logs', repo_route=True)

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
    config.scan('.views', ignore='.tests')
