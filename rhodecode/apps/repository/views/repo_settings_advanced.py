# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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

import logging


from pyramid.httpexceptions import HTTPFound
from packaging.version import Version

from rhodecode import events
from rhodecode.apps._base import RepoAppView
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired,
    HasRepoPermissionAny)
from rhodecode.lib.exceptions import AttachedForksError, AttachedPullRequestsError
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib.vcs import RepositoryError
from rhodecode.model.db import Session, UserFollowing, User, Repository
from rhodecode.model.permission import PermissionModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class RepoSettingsAdvancedView(RepoAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    def _get_users_with_permissions(self):
        user_permissions = {}
        for perm in self.db_repo.permissions():
            user_permissions[perm.user_id] = perm

        return user_permissions

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    def edit_advanced(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'advanced'

        c.default_user_id = User.get_default_user_id()
        c.in_public_journal = UserFollowing.query() \
            .filter(UserFollowing.user_id == c.default_user_id) \
            .filter(UserFollowing.follows_repository == self.db_repo).scalar()

        c.ver_info_dict = self.rhodecode_vcs_repo.get_hooks_info()
        c.hooks_outdated = False

        try:
            if Version(c.ver_info_dict['pre_version']) < Version(c.rhodecode_version):
                c.hooks_outdated = True
        except Exception:
            pass

        # update commit cache if GET flag is present
        if self.request.GET.get('update_commit_cache'):
            self.db_repo.update_commit_cache()
            h.flash(_('updated commit cache'), category='success')

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def edit_advanced_archive(self):
        """
        Archives the repository. It will become read-only, and not visible in search
        or other queries. But still visible for super-admins.
        """

        _ = self.request.translate

        try:
            old_data = self.db_repo.get_api_data()
            RepoModel().archive(self.db_repo)

            repo = audit_logger.RepoWrap(repo_id=None, repo_name=self.db_repo.repo_name)
            audit_logger.store_web(
                'repo.archive', action_data={'old_data': old_data},
                user=self._rhodecode_user, repo=repo)

            ScmModel().mark_for_invalidation(self.db_repo_name, delete=True)
            h.flash(
                _('Archived repository `%s`') % self.db_repo_name,
                category='success')
            Session().commit()
        except Exception:
            log.exception("Exception during archiving of repository")
            h.flash(_('An error occurred during archiving of `%s`')
                    % self.db_repo_name, category='error')
            # redirect to advanced for more deletion options
            raise HTTPFound(
                h.route_path('edit_repo_advanced', repo_name=self.db_repo_name,
                             _anchor='advanced-archive'))

        # flush permissions for all users defined in permissions
        affected_user_ids = self._get_users_with_permissions().keys()
        PermissionModel().trigger_permission_flush(affected_user_ids)

        raise HTTPFound(h.route_path('home'))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def edit_advanced_delete(self):
        """
        Deletes the repository, or shows warnings if deletion is not possible
        because of attached forks or other errors.
        """
        _ = self.request.translate
        handle_forks = self.request.POST.get('forks', None)
        if handle_forks == 'detach_forks':
            handle_forks = 'detach'
        elif handle_forks == 'delete_forks':
            handle_forks = 'delete'

        try:
            old_data = self.db_repo.get_api_data()
            RepoModel().delete(self.db_repo, forks=handle_forks)

            _forks = self.db_repo.forks.count()
            if _forks and handle_forks:
                if handle_forks == 'detach_forks':
                    h.flash(_('Detached %s forks') % _forks, category='success')
                elif handle_forks == 'delete_forks':
                    h.flash(_('Deleted %s forks') % _forks, category='success')

            repo = audit_logger.RepoWrap(repo_id=None, repo_name=self.db_repo.repo_name)
            audit_logger.store_web(
                'repo.delete', action_data={'old_data': old_data},
                user=self._rhodecode_user, repo=repo)

            ScmModel().mark_for_invalidation(self.db_repo_name, delete=True)
            h.flash(
                _('Deleted repository `%s`') % self.db_repo_name,
                category='success')
            Session().commit()
        except AttachedForksError:
            repo_advanced_url = h.route_path(
                'edit_repo_advanced', repo_name=self.db_repo_name,
                _anchor='advanced-delete')
            delete_anchor = h.link_to(_('detach or delete'), repo_advanced_url)
            h.flash(_('Cannot delete `{repo}` it still contains attached forks. '
                      'Try using {delete_or_detach} option.')
                    .format(repo=self.db_repo_name, delete_or_detach=delete_anchor),
                    category='warning')

            # redirect to advanced for forks handle action ?
            raise HTTPFound(repo_advanced_url)

        except AttachedPullRequestsError:
            repo_advanced_url = h.route_path(
                'edit_repo_advanced', repo_name=self.db_repo_name,
                _anchor='advanced-delete')
            attached_prs = len(self.db_repo.pull_requests_source +
                               self.db_repo.pull_requests_target)
            h.flash(
                _('Cannot delete `{repo}` it still contains {num} attached pull requests. '
                  'Consider archiving the repository instead.').format(
                    repo=self.db_repo_name, num=attached_prs), category='warning')

            # redirect to advanced for forks handle action ?
            raise HTTPFound(repo_advanced_url)

        except Exception:
            log.exception("Exception during deletion of repository")
            h.flash(_('An error occurred during deletion of `%s`')
                    % self.db_repo_name, category='error')
            # redirect to advanced for more deletion options
            raise HTTPFound(
                h.route_path('edit_repo_advanced', repo_name=self.db_repo_name,
                             _anchor='advanced-delete'))

        raise HTTPFound(h.route_path('home'))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def edit_advanced_journal(self):
        """
        Set's this repository to be visible in public journal,
        in other words making default user to follow this repo
        """
        _ = self.request.translate

        try:
            user_id = User.get_default_user_id()
            ScmModel().toggle_following_repo(self.db_repo.repo_id, user_id)
            h.flash(_('Updated repository visibility in public journal'),
                    category='success')
            Session().commit()
        except Exception:
            h.flash(_('An error occurred during setting this '
                      'repository in public journal'),
                    category='error')

        raise HTTPFound(
            h.route_path('edit_repo_advanced', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def edit_advanced_fork(self):
        """
        Mark given repository as a fork of another
        """
        _ = self.request.translate

        new_fork_id = safe_int(self.request.POST.get('id_fork_of'))

        # valid repo, re-check permissions
        if new_fork_id:
            repo = Repository.get(new_fork_id)
            # ensure we have at least read access to the repo we mark
            perm_check = HasRepoPermissionAny(
                'repository.read', 'repository.write', 'repository.admin')

            if repo and perm_check(repo_name=repo.repo_name):
                new_fork_id = repo.repo_id
            else:
                new_fork_id = None

        try:
            repo = ScmModel().mark_as_fork(
                self.db_repo_name, new_fork_id, self._rhodecode_user.user_id)
            fork = repo.fork.repo_name if repo.fork else _('Nothing')
            Session().commit()
            h.flash(
                _('Marked repo %s as fork of %s') % (self.db_repo_name, fork),
                category='success')
        except RepositoryError as e:
            log.exception("Repository Error occurred")
            h.flash(str(e), category='error')
        except Exception:
            log.exception("Exception while editing fork")
            h.flash(_('An error occurred during this operation'),
                    category='error')

        raise HTTPFound(
            h.route_path('edit_repo_advanced', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def edit_advanced_toggle_locking(self):
        """
        Toggle locking of repository
        """
        _ = self.request.translate
        set_lock = self.request.POST.get('set_lock')
        set_unlock = self.request.POST.get('set_unlock')

        try:
            if set_lock:
                Repository.lock(self.db_repo, self._rhodecode_user.user_id,
                                lock_reason=Repository.LOCK_WEB)
                h.flash(_('Locked repository'), category='success')
            elif set_unlock:
                Repository.unlock(self.db_repo)
                h.flash(_('Unlocked repository'), category='success')
        except Exception as e:
            log.exception("Exception during unlocking")
            h.flash(_('An error occurred during unlocking'), category='error')

        raise HTTPFound(
            h.route_path('edit_repo_advanced', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    def edit_advanced_install_hooks(self):
        """
        Install Hooks for repository
        """
        _ = self.request.translate
        self.load_default_context()
        self.rhodecode_vcs_repo.install_hooks(force=True)
        h.flash(_('installed updated hooks into this repository'),
                category='success')
        raise HTTPFound(
            h.route_path('edit_repo_advanced', repo_name=self.db_repo_name))
