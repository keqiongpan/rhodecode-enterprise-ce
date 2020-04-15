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

import logging
from pyramid.threadlocal import get_current_registry
from rhodecode.events.base import RhodeCodeIntegrationEvent


log = logging.getLogger(__name__)


def trigger(event, registry=None):
    """
    Helper method to send an event. This wraps the pyramid logic to send an
    event.
    """
    # For the first step we are using pyramids thread locals here. If the
    # event mechanism works out as a good solution we should think about
    # passing the registry as an argument to get rid of it.
    event_name = event.__class__
    log.debug('event %s sent for execution', event_name)
    registry = registry or get_current_registry()
    registry.notify(event)
    log.debug('event %s triggered using registry %s', event_name, registry)

    # Send the events to integrations directly
    from rhodecode.integrations import integrations_event_handler
    if isinstance(event, RhodeCodeIntegrationEvent):
        integrations_event_handler(event)


from rhodecode.events.user import (  # pragma: no cover
    UserPreCreate,
    UserPostCreate,
    UserPreUpdate,
    UserRegistered,
    UserPermissionsChange,
)

from rhodecode.events.repo import (  # pragma: no cover
    RepoEvent, RepoCommitCommentEvent,
    RepoPreCreateEvent, RepoCreateEvent,
    RepoPreDeleteEvent, RepoDeleteEvent,
    RepoPrePushEvent,   RepoPushEvent,
    RepoPrePullEvent,   RepoPullEvent,
)

from rhodecode.events.repo_group import (  # pragma: no cover
    RepoGroupEvent,
    RepoGroupCreateEvent,
    RepoGroupUpdateEvent,
    RepoGroupDeleteEvent,
)

from rhodecode.events.pullrequest import (  # pragma: no cover
    PullRequestEvent,
    PullRequestCreateEvent,
    PullRequestUpdateEvent,
    PullRequestCommentEvent,
    PullRequestReviewEvent,
    PullRequestMergeEvent,
    PullRequestCloseEvent,
)
