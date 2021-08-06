# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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
    from rhodecode.apps.repository.views.repo_artifacts import RepoArtifactsView
    from rhodecode.apps.repository.views.repo_audit_logs import AuditLogsView
    from rhodecode.apps.repository.views.repo_automation import RepoAutomationView
    from rhodecode.apps.repository.views.repo_bookmarks import RepoBookmarksView
    from rhodecode.apps.repository.views.repo_branch_permissions import RepoSettingsBranchPermissionsView
    from rhodecode.apps.repository.views.repo_branches import RepoBranchesView
    from rhodecode.apps.repository.views.repo_caches import RepoCachesView
    from rhodecode.apps.repository.views.repo_changelog import RepoChangelogView
    from rhodecode.apps.repository.views.repo_checks import RepoChecksView
    from rhodecode.apps.repository.views.repo_commits import RepoCommitsView
    from rhodecode.apps.repository.views.repo_compare import RepoCompareView
    from rhodecode.apps.repository.views.repo_feed import RepoFeedView
    from rhodecode.apps.repository.views.repo_files import RepoFilesView
    from rhodecode.apps.repository.views.repo_forks import RepoForksView
    from rhodecode.apps.repository.views.repo_maintainance import RepoMaintenanceView
    from rhodecode.apps.repository.views.repo_permissions import RepoSettingsPermissionsView
    from rhodecode.apps.repository.views.repo_pull_requests import RepoPullRequestsView
    from rhodecode.apps.repository.views.repo_review_rules import RepoReviewRulesView
    from rhodecode.apps.repository.views.repo_settings import RepoSettingsView
    from rhodecode.apps.repository.views.repo_settings_advanced import RepoSettingsAdvancedView
    from rhodecode.apps.repository.views.repo_settings_fields import RepoSettingsFieldsView
    from rhodecode.apps.repository.views.repo_settings_issue_trackers import RepoSettingsIssueTrackersView
    from rhodecode.apps.repository.views.repo_settings_remote import RepoSettingsRemoteView
    from rhodecode.apps.repository.views.repo_settings_vcs import RepoSettingsVcsView
    from rhodecode.apps.repository.views.repo_strip import RepoStripView
    from rhodecode.apps.repository.views.repo_summary import RepoSummaryView
    from rhodecode.apps.repository.views.repo_tags import RepoTagsView

    # repo creating checks, special cases that aren't repo routes
    config.add_route(
        name='repo_creating',
        pattern='/{repo_name:.*?[^/]}/repo_creating')
    config.add_view(
        RepoChecksView,
        attr='repo_creating',
        route_name='repo_creating', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_creating.mako')

    config.add_route(
        name='repo_creating_check',
        pattern='/{repo_name:.*?[^/]}/repo_creating_check')
    config.add_view(
        RepoChecksView,
        attr='repo_creating_check',
        route_name='repo_creating_check', request_method='GET',
        renderer='json_ext')

    # Summary
    # NOTE(marcink): one additional route is defined in very bottom, catch
    # all pattern
    config.add_route(
        name='repo_summary_explicit',
        pattern='/{repo_name:.*?[^/]}/summary', repo_route=True)
    config.add_view(
        RepoSummaryView,
        attr='summary',
        route_name='repo_summary_explicit', request_method='GET',
        renderer='rhodecode:templates/summary/summary.mako')

    config.add_route(
        name='repo_summary_commits',
        pattern='/{repo_name:.*?[^/]}/summary-commits', repo_route=True)
    config.add_view(
        RepoSummaryView,
        attr='summary_commits',
        route_name='repo_summary_commits', request_method='GET',
        renderer='rhodecode:templates/summary/summary_commits.mako')
    
    # Commits
    config.add_route(
        name='repo_commit',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_show',
        route_name='repo_commit', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_commit_children',
        pattern='/{repo_name:.*?[^/]}/changeset_children/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_children',
        route_name='repo_commit_children', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_commit_parents',
        pattern='/{repo_name:.*?[^/]}/changeset_parents/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_parents',
        route_name='repo_commit_parents', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='repo_commit_raw',
        pattern='/{repo_name:.*?[^/]}/changeset-diff/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_raw',
        route_name='repo_commit_raw', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_commit_patch',
        pattern='/{repo_name:.*?[^/]}/changeset-patch/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_patch',
        route_name='repo_commit_patch', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_commit_download',
        pattern='/{repo_name:.*?[^/]}/changeset-download/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_download',
        route_name='repo_commit_download', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_commit_data',
        pattern='/{repo_name:.*?[^/]}/changeset-data/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_data',
        route_name='repo_commit_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_commit_comment_create',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/create', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_comment_create',
        route_name='repo_commit_comment_create', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='repo_commit_comment_preview',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/preview', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_comment_preview',
        route_name='repo_commit_comment_preview', request_method='POST',
        renderer='string', xhr=True)

    config.add_route(
        name='repo_commit_comment_history_view',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/{comment_id}/history_view/{comment_history_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_comment_history_view',
        route_name='repo_commit_comment_history_view', request_method='POST',
        renderer='string', xhr=True)

    config.add_route(
        name='repo_commit_comment_attachment_upload',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/attachment_upload', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_comment_attachment_upload',
        route_name='repo_commit_comment_attachment_upload', request_method='POST',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_commit_comment_delete',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/{comment_id}/delete', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_comment_delete',
        route_name='repo_commit_comment_delete', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='repo_commit_comment_edit',
        pattern='/{repo_name:.*?[^/]}/changeset/{commit_id}/comment/{comment_id}/edit', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_comment_edit',
        route_name='repo_commit_comment_edit', request_method='POST',
        renderer='json_ext')

    # still working url for backward compat.
    config.add_route(
        name='repo_commit_raw_deprecated',
        pattern='/{repo_name:.*?[^/]}/raw-changeset/{commit_id}', repo_route=True)
    config.add_view(
        RepoCommitsView,
        attr='repo_commit_raw',
        route_name='repo_commit_raw_deprecated', request_method='GET',
        renderer=None)

    # Files
    config.add_route(
        name='repo_archivefile',
        pattern='/{repo_name:.*?[^/]}/archive/{fname:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_archivefile',
        route_name='repo_archivefile', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files_diff',
        pattern='/{repo_name:.*?[^/]}/diff/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_diff',
        route_name='repo_files_diff', request_method='GET',
        renderer=None)

    config.add_route(  # legacy route to make old links work
        name='repo_files_diff_2way_redirect',
        pattern='/{repo_name:.*?[^/]}/diff-2way/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_diff_2way_redirect',
        route_name='repo_files_diff_2way_redirect', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files',
        pattern='/{repo_name:.*?[^/]}/files/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files',
        route_name='repo_files', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files:default_path',
        pattern='/{repo_name:.*?[^/]}/files/{commit_id}/', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files',
        route_name='repo_files:default_path', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files:default_commit',
        pattern='/{repo_name:.*?[^/]}/files', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files',
        route_name='repo_files:default_commit', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files:rendered',
        pattern='/{repo_name:.*?[^/]}/render/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files',
        route_name='repo_files:rendered', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files:annotated',
        pattern='/{repo_name:.*?[^/]}/annotate/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files',
        route_name='repo_files:annotated', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_files:annotated_previous',
        pattern='/{repo_name:.*?[^/]}/annotate-previous/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_annotated_previous',
        route_name='repo_files:annotated_previous', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_nodetree_full',
        pattern='/{repo_name:.*?[^/]}/nodetree_full/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_nodetree_full',
        route_name='repo_nodetree_full', request_method='GET',
        renderer=None, xhr=True)

    config.add_route(
        name='repo_nodetree_full:default_path',
        pattern='/{repo_name:.*?[^/]}/nodetree_full/{commit_id}/', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_nodetree_full',
        route_name='repo_nodetree_full:default_path', request_method='GET',
        renderer=None, xhr=True)

    config.add_route(
        name='repo_files_nodelist',
        pattern='/{repo_name:.*?[^/]}/nodelist/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_nodelist',
        route_name='repo_files_nodelist', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_file_raw',
        pattern='/{repo_name:.*?[^/]}/raw/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_file_raw',
        route_name='repo_file_raw', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_file_download',
        pattern='/{repo_name:.*?[^/]}/download/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_file_download',
        route_name='repo_file_download', request_method='GET',
        renderer=None)

    config.add_route(  # backward compat to keep old links working
        name='repo_file_download:legacy',
        pattern='/{repo_name:.*?[^/]}/rawfile/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_file_download',
        route_name='repo_file_download:legacy', request_method='GET',
        renderer=None)

    config.add_route(
        name='repo_file_history',
        pattern='/{repo_name:.*?[^/]}/history/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_file_history',
        route_name='repo_file_history', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='repo_file_authors',
        pattern='/{repo_name:.*?[^/]}/authors/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_file_authors',
        route_name='repo_file_authors', request_method='GET',
        renderer='rhodecode:templates/files/file_authors_box.mako')

    config.add_route(
        name='repo_files_check_head',
        pattern='/{repo_name:.*?[^/]}/check_head/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_check_head',
        route_name='repo_files_check_head', request_method='POST',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_files_remove_file',
        pattern='/{repo_name:.*?[^/]}/remove_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_remove_file',
        route_name='repo_files_remove_file', request_method='GET',
        renderer='rhodecode:templates/files/files_delete.mako')

    config.add_route(
        name='repo_files_delete_file',
        pattern='/{repo_name:.*?[^/]}/delete_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_delete_file',
        route_name='repo_files_delete_file', request_method='POST',
        renderer=None)

    config.add_route(
        name='repo_files_edit_file',
        pattern='/{repo_name:.*?[^/]}/edit_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_edit_file',
        route_name='repo_files_edit_file', request_method='GET',
        renderer='rhodecode:templates/files/files_edit.mako')

    config.add_route(
        name='repo_files_update_file',
        pattern='/{repo_name:.*?[^/]}/update_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_update_file',
        route_name='repo_files_update_file', request_method='POST',
        renderer=None)

    config.add_route(
        name='repo_files_add_file',
        pattern='/{repo_name:.*?[^/]}/add_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_add_file',
        route_name='repo_files_add_file', request_method='GET',
        renderer='rhodecode:templates/files/files_add.mako')

    config.add_route(
        name='repo_files_upload_file',
        pattern='/{repo_name:.*?[^/]}/upload_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view(
        RepoFilesView,
        attr='repo_files_add_file',
        route_name='repo_files_upload_file', request_method='GET',
        renderer='rhodecode:templates/files/files_upload.mako')
    config.add_view( # POST creates
        RepoFilesView,
        attr='repo_files_upload_file',
        route_name='repo_files_upload_file', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='repo_files_create_file',
        pattern='/{repo_name:.*?[^/]}/create_file/{commit_id}/{f_path:.*}',
        repo_route=True)
    config.add_view( # POST creates
        RepoFilesView,
        attr='repo_files_create_file',
        route_name='repo_files_create_file', request_method='POST',
        renderer=None)

    # Refs data
    config.add_route(
        name='repo_refs_data',
        pattern='/{repo_name:.*?[^/]}/refs-data', repo_route=True)
    config.add_view(
        RepoSummaryView,
        attr='repo_refs_data',
        route_name='repo_refs_data', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='repo_refs_changelog_data',
        pattern='/{repo_name:.*?[^/]}/refs-data-changelog', repo_route=True)
    config.add_view(
        RepoSummaryView,
        attr='repo_refs_changelog_data',
        route_name='repo_refs_changelog_data', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='repo_stats',
        pattern='/{repo_name:.*?[^/]}/repo_stats/{commit_id}', repo_route=True)
    config.add_view(
        RepoSummaryView,
        attr='repo_stats',
        route_name='repo_stats', request_method='GET',
        renderer='json_ext')

    # Commits
    config.add_route(
        name='repo_commits',
        pattern='/{repo_name:.*?[^/]}/commits', repo_route=True)
    config.add_view(
        RepoChangelogView,
        attr='repo_changelog',
        route_name='repo_commits', request_method='GET',
        renderer='rhodecode:templates/commits/changelog.mako')
    # old routes for backward compat
    config.add_view(
        RepoChangelogView,
        attr='repo_changelog',
        route_name='repo_changelog', request_method='GET',
        renderer='rhodecode:templates/commits/changelog.mako')

    config.add_route(
        name='repo_commits_elements',
        pattern='/{repo_name:.*?[^/]}/commits_elements', repo_route=True)
    config.add_view(
        RepoChangelogView,
        attr='repo_commits_elements',
        route_name='repo_commits_elements', request_method=('GET', 'POST'),
        renderer='rhodecode:templates/commits/changelog_elements.mako',
        xhr=True)

    config.add_route(
        name='repo_commits_elements_file',
        pattern='/{repo_name:.*?[^/]}/commits_elements/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoChangelogView,
        attr='repo_commits_elements',
        route_name='repo_commits_elements_file', request_method=('GET', 'POST'),
        renderer='rhodecode:templates/commits/changelog_elements.mako',
        xhr=True)

    config.add_route(
        name='repo_commits_file',
        pattern='/{repo_name:.*?[^/]}/commits/{commit_id}/{f_path:.*}', repo_route=True)
    config.add_view(
        RepoChangelogView,
        attr='repo_changelog',
        route_name='repo_commits_file', request_method='GET',
        renderer='rhodecode:templates/commits/changelog.mako')
    # old routes for backward compat
    config.add_view(
        RepoChangelogView,
        attr='repo_changelog',
        route_name='repo_changelog_file', request_method='GET',
        renderer='rhodecode:templates/commits/changelog.mako')

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
    config.add_view(
        RepoCompareView,
        attr='compare_select',
        route_name='repo_compare_select', request_method='GET',
        renderer='rhodecode:templates/compare/compare_diff.mako')

    config.add_route(
        name='repo_compare',
        pattern='/{repo_name:.*?[^/]}/compare/{source_ref_type}@{source_ref:.*?}...{target_ref_type}@{target_ref:.*?}', repo_route=True)
    config.add_view(
        RepoCompareView,
        attr='compare',
        route_name='repo_compare', request_method='GET',
        renderer=None)

    # Tags
    config.add_route(
        name='tags_home',
        pattern='/{repo_name:.*?[^/]}/tags', repo_route=True)
    config.add_view(
        RepoTagsView,
        attr='tags',
        route_name='tags_home', request_method='GET',
        renderer='rhodecode:templates/tags/tags.mako')

    # Branches
    config.add_route(
        name='branches_home',
        pattern='/{repo_name:.*?[^/]}/branches', repo_route=True)
    config.add_view(
        RepoBranchesView,
        attr='branches',
        route_name='branches_home', request_method='GET',
        renderer='rhodecode:templates/branches/branches.mako')

    # Bookmarks
    config.add_route(
        name='bookmarks_home',
        pattern='/{repo_name:.*?[^/]}/bookmarks', repo_route=True)
    config.add_view(
        RepoBookmarksView,
        attr='bookmarks',
        route_name='bookmarks_home', request_method='GET',
        renderer='rhodecode:templates/bookmarks/bookmarks.mako')

    # Forks
    config.add_route(
        name='repo_fork_new',
        pattern='/{repo_name:.*?[^/]}/fork', repo_route=True,
        repo_forbid_when_archived=True,
        repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoForksView,
        attr='repo_fork_new',
        route_name='repo_fork_new', request_method='GET',
        renderer='rhodecode:templates/forks/forks.mako')

    config.add_route(
        name='repo_fork_create',
        pattern='/{repo_name:.*?[^/]}/fork/create', repo_route=True,
        repo_forbid_when_archived=True,
        repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoForksView,
        attr='repo_fork_create',
        route_name='repo_fork_create', request_method='POST',
        renderer='rhodecode:templates/forks/fork.mako')

    config.add_route(
        name='repo_forks_show_all',
        pattern='/{repo_name:.*?[^/]}/forks', repo_route=True,
        repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoForksView,
        attr='repo_forks_show_all',
        route_name='repo_forks_show_all', request_method='GET',
        renderer='rhodecode:templates/forks/forks.mako')
    
    config.add_route(
        name='repo_forks_data',
        pattern='/{repo_name:.*?[^/]}/forks/data', repo_route=True,
        repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoForksView,
        attr='repo_forks_data',
        route_name='repo_forks_data', request_method='GET',
        renderer='json_ext', xhr=True)

    # Pull Requests
    config.add_route(
        name='pullrequest_show',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_show',
        route_name='pullrequest_show', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequest_show.mako')

    config.add_route(
        name='pullrequest_show_all',
        pattern='/{repo_name:.*?[^/]}/pull-request',
        repo_route=True, repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_list',
        route_name='pullrequest_show_all', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequests.mako')

    config.add_route(
        name='pullrequest_show_all_data',
        pattern='/{repo_name:.*?[^/]}/pull-request-data',
        repo_route=True, repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_list_data',
        route_name='pullrequest_show_all_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='pullrequest_repo_refs',
        pattern='/{repo_name:.*?[^/]}/pull-request/refs/{target_repo_name:.*?[^/]}',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_repo_refs',
        route_name='pullrequest_repo_refs', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='pullrequest_repo_targets',
        pattern='/{repo_name:.*?[^/]}/pull-request/repo-targets',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pullrequest_repo_targets',
        route_name='pullrequest_repo_targets', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='pullrequest_new',
        pattern='/{repo_name:.*?[^/]}/pull-request/new',
        repo_route=True, repo_accepted_types=['hg', 'git'],
        repo_forbid_when_archived=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_new',
        route_name='pullrequest_new', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequest.mako')

    config.add_route(
        name='pullrequest_create',
        pattern='/{repo_name:.*?[^/]}/pull-request/create',
        repo_route=True, repo_accepted_types=['hg', 'git'],
        repo_forbid_when_archived=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_create',
        route_name='pullrequest_create', request_method='POST',
        renderer=None)

    config.add_route(
        name='pullrequest_update',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/update',
        repo_route=True, repo_forbid_when_archived=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_update',
        route_name='pullrequest_update', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='pullrequest_merge',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/merge',
        repo_route=True, repo_forbid_when_archived=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_merge',
        route_name='pullrequest_merge', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='pullrequest_delete',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/delete',
        repo_route=True, repo_forbid_when_archived=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_delete',
        route_name='pullrequest_delete', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='pullrequest_comment_create',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/comment',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_comment_create',
        route_name='pullrequest_comment_create', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='pullrequest_comment_edit',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/comment/{comment_id}/edit',
        repo_route=True, repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_comment_edit',
        route_name='pullrequest_comment_edit', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='pullrequest_comment_delete',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/comment/{comment_id}/delete',
        repo_route=True, repo_accepted_types=['hg', 'git'])
    config.add_view(
        RepoPullRequestsView,
        attr='pull_request_comment_delete',
        route_name='pullrequest_comment_delete', request_method='POST',
        renderer='json_ext')

    config.add_route(
        name='pullrequest_comments',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/comments',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pullrequest_comments',
        route_name='pullrequest_comments', request_method='POST',
        renderer='string_html', xhr=True)

    config.add_route(
        name='pullrequest_todos',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/todos',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pullrequest_todos',
        route_name='pullrequest_todos', request_method='POST',
        renderer='string_html', xhr=True)

    config.add_route(
        name='pullrequest_drafts',
        pattern='/{repo_name:.*?[^/]}/pull-request/{pull_request_id:\d+}/drafts',
        repo_route=True)
    config.add_view(
        RepoPullRequestsView,
        attr='pullrequest_drafts',
        route_name='pullrequest_drafts', request_method='POST',
        renderer='string_html', xhr=True)

    # Artifacts, (EE feature)
    config.add_route(
        name='repo_artifacts_list',
        pattern='/{repo_name:.*?[^/]}/artifacts', repo_route=True)
    config.add_view(
        RepoArtifactsView,
        attr='repo_artifacts',
        route_name='repo_artifacts_list', request_method='GET',
        renderer='rhodecode:templates/artifacts/artifact_list.mako')

    # Settings
    config.add_route(
        name='edit_repo',
        pattern='/{repo_name:.*?[^/]}/settings', repo_route=True)
    config.add_view(
        RepoSettingsView,
        attr='edit_settings',
        route_name='edit_repo', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    # update is POST on edit_repo
    config.add_view(
        RepoSettingsView,
        attr='edit_settings_update',
        route_name='edit_repo', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # Settings advanced
    config.add_route(
        name='edit_repo_advanced',
        pattern='/{repo_name:.*?[^/]}/settings/advanced', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced',
        route_name='edit_repo_advanced', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    
    config.add_route(
        name='edit_repo_advanced_archive',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/archive', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced_archive',
        route_name='edit_repo_advanced_archive', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    
    config.add_route(
        name='edit_repo_advanced_delete',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/delete', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced_delete',
        route_name='edit_repo_advanced_delete', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_advanced_locking',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/locking', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced_toggle_locking',
        route_name='edit_repo_advanced_locking', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_advanced_journal',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/journal', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced_journal',
        route_name='edit_repo_advanced_journal', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    
    config.add_route(
        name='edit_repo_advanced_fork',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/fork', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced_fork',
        route_name='edit_repo_advanced_fork', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_advanced_hooks',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/hooks', repo_route=True)
    config.add_view(
        RepoSettingsAdvancedView,
        attr='edit_advanced_install_hooks',
        route_name='edit_repo_advanced_hooks', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # Caches
    config.add_route(
        name='edit_repo_caches',
        pattern='/{repo_name:.*?[^/]}/settings/caches', repo_route=True)
    config.add_view(
        RepoCachesView,
        attr='repo_caches',
        route_name='edit_repo_caches', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    config.add_view(
        RepoCachesView,
        attr='repo_caches_purge',
        route_name='edit_repo_caches', request_method='POST')

    # Permissions
    config.add_route(
        name='edit_repo_perms',
        pattern='/{repo_name:.*?[^/]}/settings/permissions', repo_route=True)
    config.add_view(
        RepoSettingsPermissionsView,
        attr='edit_permissions',
        route_name='edit_repo_perms', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    config.add_view(
        RepoSettingsPermissionsView,
        attr='edit_permissions_update',
        route_name='edit_repo_perms', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_perms_set_private',
        pattern='/{repo_name:.*?[^/]}/settings/permissions/set_private', repo_route=True)
    config.add_view(
        RepoSettingsPermissionsView,
        attr='edit_permissions_set_private_repo',
        route_name='edit_repo_perms_set_private', request_method='POST',
        renderer='json_ext')

    # Permissions Branch (EE feature)
    config.add_route(
        name='edit_repo_perms_branch',
        pattern='/{repo_name:.*?[^/]}/settings/branch_permissions', repo_route=True)
    config.add_view(
        RepoSettingsBranchPermissionsView,
        attr='branch_permissions',
        route_name='edit_repo_perms_branch', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_perms_branch_delete',
        pattern='/{repo_name:.*?[^/]}/settings/branch_permissions/{rule_id}/delete',
        repo_route=True)
    ## Only implemented in EE

    # Maintenance
    config.add_route(
        name='edit_repo_maintenance',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance', repo_route=True)
    config.add_view(
        RepoMaintenanceView,
        attr='repo_maintenance',
        route_name='edit_repo_maintenance', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_maintenance_execute',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance/execute', repo_route=True)
    config.add_view(
        RepoMaintenanceView,
        attr='repo_maintenance_execute',
        route_name='edit_repo_maintenance_execute', request_method='GET',
        renderer='json', xhr=True)

    # Fields
    config.add_route(
        name='edit_repo_fields',
        pattern='/{repo_name:.*?[^/]}/settings/fields', repo_route=True)
    config.add_view(
        RepoSettingsFieldsView,
        attr='repo_field_edit',
        route_name='edit_repo_fields', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_fields_create',
        pattern='/{repo_name:.*?[^/]}/settings/fields/create', repo_route=True)
    config.add_view(
        RepoSettingsFieldsView,
        attr='repo_field_create',
        route_name='edit_repo_fields_create', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_fields_delete',
        pattern='/{repo_name:.*?[^/]}/settings/fields/{field_id}/delete', repo_route=True)
    config.add_view(
        RepoSettingsFieldsView,
        attr='repo_field_delete',
        route_name='edit_repo_fields_delete', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # Locking
    config.add_route(
        name='repo_edit_toggle_locking',
        pattern='/{repo_name:.*?[^/]}/settings/toggle_locking', repo_route=True)
    config.add_view(
        RepoSettingsView,
        attr='edit_advanced_toggle_locking',
        route_name='repo_edit_toggle_locking', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # Remote
    config.add_route(
        name='edit_repo_remote',
        pattern='/{repo_name:.*?[^/]}/settings/remote', repo_route=True)
    config.add_view(
        RepoSettingsRemoteView,
        attr='repo_remote_edit_form',
        route_name='edit_repo_remote', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_remote_pull',
        pattern='/{repo_name:.*?[^/]}/settings/remote/pull', repo_route=True)
    config.add_view(
        RepoSettingsRemoteView,
        attr='repo_remote_pull_changes',
        route_name='edit_repo_remote_pull', request_method='POST',
        renderer=None)

    config.add_route(
        name='edit_repo_remote_push',
        pattern='/{repo_name:.*?[^/]}/settings/remote/push', repo_route=True)

    # Statistics
    config.add_route(
        name='edit_repo_statistics',
        pattern='/{repo_name:.*?[^/]}/settings/statistics', repo_route=True)
    config.add_view(
        RepoSettingsView,
        attr='edit_statistics_form',
        route_name='edit_repo_statistics', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    
    config.add_route(
        name='edit_repo_statistics_reset',
        pattern='/{repo_name:.*?[^/]}/settings/statistics/update', repo_route=True)
    config.add_view(
        RepoSettingsView,
        attr='repo_statistics_reset',
        route_name='edit_repo_statistics_reset', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # Issue trackers
    config.add_route(
        name='edit_repo_issuetracker',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers', repo_route=True)
    config.add_view(
        RepoSettingsIssueTrackersView,
        attr='repo_issuetracker',
        route_name='edit_repo_issuetracker', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    
    config.add_route(
        name='edit_repo_issuetracker_test',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers/test', repo_route=True)
    config.add_view(
        RepoSettingsIssueTrackersView,
        attr='repo_issuetracker_test',
        route_name='edit_repo_issuetracker_test', request_method='POST',
        renderer='string', xhr=True)

    config.add_route(
        name='edit_repo_issuetracker_delete',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers/delete', repo_route=True)
    config.add_view(
        RepoSettingsIssueTrackersView,
        attr='repo_issuetracker_delete',
        route_name='edit_repo_issuetracker_delete', request_method='POST',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='edit_repo_issuetracker_update',
        pattern='/{repo_name:.*?[^/]}/settings/issue_trackers/update', repo_route=True)
    config.add_view(
        RepoSettingsIssueTrackersView,
        attr='repo_issuetracker_update',
        route_name='edit_repo_issuetracker_update', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # VCS Settings
    config.add_route(
        name='edit_repo_vcs',
        pattern='/{repo_name:.*?[^/]}/settings/vcs', repo_route=True)
    config.add_view(
        RepoSettingsVcsView,
        attr='repo_vcs_settings',
        route_name='edit_repo_vcs', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='edit_repo_vcs_update',
        pattern='/{repo_name:.*?[^/]}/settings/vcs/update', repo_route=True)
    config.add_view(
        RepoSettingsVcsView,
        attr='repo_settings_vcs_update',
        route_name='edit_repo_vcs_update', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # svn pattern
    config.add_route(
        name='edit_repo_vcs_svn_pattern_delete',
        pattern='/{repo_name:.*?[^/]}/settings/vcs/svn_pattern/delete', repo_route=True)
    config.add_view(
        RepoSettingsVcsView,
        attr='repo_settings_delete_svn_pattern',
        route_name='edit_repo_vcs_svn_pattern_delete', request_method='POST',
        renderer='json_ext', xhr=True)

    # Repo Review Rules (EE feature)
    config.add_route(
        name='repo_reviewers',
        pattern='/{repo_name:.*?[^/]}/settings/review/rules', repo_route=True)
    config.add_view(
        RepoReviewRulesView,
        attr='repo_review_rules',
        route_name='repo_reviewers', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='repo_default_reviewers_data',
        pattern='/{repo_name:.*?[^/]}/settings/review/default-reviewers', repo_route=True)
    config.add_view(
        RepoReviewRulesView,
        attr='repo_default_reviewers_data',
        route_name='repo_default_reviewers_data', request_method='GET',
        renderer='json_ext')

    # Repo Automation (EE feature)
    config.add_route(
        name='repo_automation',
        pattern='/{repo_name:.*?[^/]}/settings/automation', repo_route=True)
    config.add_view(
        RepoAutomationView,
        attr='repo_automation',
        route_name='repo_automation', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # Strip
    config.add_route(
        name='edit_repo_strip',
        pattern='/{repo_name:.*?[^/]}/settings/strip', repo_route=True)
    config.add_view(
        RepoStripView,
        attr='strip',
        route_name='edit_repo_strip', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    config.add_route(
        name='strip_check',
        pattern='/{repo_name:.*?[^/]}/settings/strip_check', repo_route=True)
    config.add_view(
        RepoStripView,
        attr='strip_check',
        route_name='strip_check', request_method='POST',
        renderer='json', xhr=True)

    config.add_route(
        name='strip_execute',
        pattern='/{repo_name:.*?[^/]}/settings/strip_execute', repo_route=True)
    config.add_view(
        RepoStripView,
        attr='strip_execute',
        route_name='strip_execute', request_method='POST',
        renderer='json', xhr=True)

    # Audit logs
    config.add_route(
        name='edit_repo_audit_logs',
        pattern='/{repo_name:.*?[^/]}/settings/audit_logs', repo_route=True)
    config.add_view(
        AuditLogsView,
        attr='repo_audit_logs',
        route_name='edit_repo_audit_logs', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')

    # ATOM/RSS Feed, shouldn't contain slashes for outlook compatibility
    config.add_route(
        name='rss_feed_home',
        pattern='/{repo_name:.*?[^/]}/feed-rss', repo_route=True)
    config.add_view(
        RepoFeedView,
        attr='rss',
        route_name='rss_feed_home', request_method='GET', renderer=None)

    config.add_route(
        name='rss_feed_home_old',
        pattern='/{repo_name:.*?[^/]}/feed/rss', repo_route=True)
    config.add_view(
        RepoFeedView,
        attr='rss',
        route_name='rss_feed_home_old', request_method='GET', renderer=None)

    config.add_route(
        name='atom_feed_home',
        pattern='/{repo_name:.*?[^/]}/feed-atom', repo_route=True)
    config.add_view(
        RepoFeedView,
        attr='atom',
        route_name='atom_feed_home', request_method='GET', renderer=None)

    config.add_route(
        name='atom_feed_home_old',
        pattern='/{repo_name:.*?[^/]}/feed/atom', repo_route=True)
    config.add_view(
        RepoFeedView,
        attr='atom',
        route_name='atom_feed_home_old', request_method='GET', renderer=None)

    # NOTE(marcink): needs to be at the end for catch-all
    add_route_with_slash(
        config,
        name='repo_summary',
        pattern='/{repo_name:.*?[^/]}', repo_route=True)
    config.add_view(
        RepoSummaryView,
        attr='summary',
        route_name='repo_summary', request_method='GET',
        renderer='rhodecode:templates/summary/summary.mako')
    
    # TODO(marcink): there's no such route??
    config.add_view(
        RepoSummaryView,
        attr='summary',
        route_name='repo_summary_slash', request_method='GET',
        renderer='rhodecode:templates/summary/summary.mako')