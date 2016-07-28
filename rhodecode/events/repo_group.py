# Copyright (C) 2016-2016  RhodeCode GmbH
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

from rhodecode.translation import lazy_ugettext
from rhodecode.events.base import RhodecodeEvent

log = logging.getLogger()


class RepoGroupEvent(RhodecodeEvent):
    """
    Base class for events acting on a repository group.

    :param repo: a :class:`RepositoryGroup` instance
    """

    def __init__(self, repo_group):
        super(RepoGroupEvent, self).__init__()
        self.repo_group = repo_group

    # TODO: Implement this
    # def as_dict(self):
    #     from rhodecode.model.repo import RepoModel
    #     data = super(RepoGroupEvent, self).as_dict()
    #     data.update({
    #         'repo': {
    #             'repo_id': self.repo.repo_id,
    #             'repo_name': self.repo.repo_name,
    #             'repo_type': self.repo.repo_type,
    #             'url': RepoModel().get_url(self.repo)
    #         }
    #     })
    #     return data


class RepoGroupCreateEvent(RepoGroupEvent):
    """
    An instance of this class is emitted as an :term:`event` whenever a
    repository group is created.
    """
    name = 'repo-group-create'
    display_name = lazy_ugettext('repository group created')


class RepoGroupDeleteEvent(RepoGroupEvent):
    """
    An instance of this class is emitted as an :term:`event` whenever a
    repository group is deleted.
    """
    name = 'repo-group-delete'
    display_name = lazy_ugettext('repository group deleted')


class RepoGroupUpdateEvent(RepoGroupEvent):
    """
    An instance of this class is emitted as an :term:`event` whenever a
    repository group is updated.
    """
    name = 'repo-group-update'
    display_name = lazy_ugettext('repository group update')
