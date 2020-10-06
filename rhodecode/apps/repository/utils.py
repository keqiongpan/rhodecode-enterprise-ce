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

from rhodecode.lib import helpers as h
from rhodecode.lib.utils2 import safe_int
from rhodecode.model.pull_request import get_diff_info
from rhodecode.model.db import PullRequestReviewers
# V3 - Reviewers, with default rules data
# v4 - Added observers metadata
REVIEWER_API_VERSION = 'V4'


def reviewer_as_json(user, reasons=None, role=None, mandatory=False, rules=None, user_group=None):
    """
    Returns json struct of a reviewer for frontend

    :param user: the reviewer
    :param reasons: list of strings of why they are reviewers
    :param mandatory: bool, to set user as mandatory
    """
    role = role or PullRequestReviewers.ROLE_REVIEWER
    if role not in PullRequestReviewers.ROLES:
        raise ValueError('role is not one of %s', PullRequestReviewers.ROLES)

    return {
        'user_id': user.user_id,
        'reasons': reasons or [],
        'rules': rules or [],
        'role': role,
        'mandatory': mandatory,
        'user_group': user_group,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_link': h.link_to_user(user),
        'gravatar_link': h.gravatar_url(user.email, 14),
    }


def get_default_reviewers_data(current_user, source_repo, source_commit, target_repo, target_commit):
    """
    Return json for default reviewers of a repository
    """

    diff_info = get_diff_info(
        source_repo, source_commit.raw_id, target_repo, target_commit.raw_id)

    reasons = ['Default reviewer', 'Repository owner']
    json_reviewers = [reviewer_as_json(
        user=target_repo.user, reasons=reasons, mandatory=False, rules=None, role=None)]

    return {
        'api_ver': REVIEWER_API_VERSION,  # define version for later possible schema upgrade
        'diff_info': diff_info,
        'reviewers': json_reviewers,
        'rules': {},
        'rules_data': {},
    }


def validate_default_reviewers(review_members, reviewer_rules):
    """
    Function to validate submitted reviewers against the saved rules
    """
    reviewers = []
    reviewer_by_id = {}
    for r in review_members:
        reviewer_user_id = safe_int(r['user_id'])
        entry = (reviewer_user_id, r['reasons'], r['mandatory'], r['role'], r['rules'])

        reviewer_by_id[reviewer_user_id] = entry
        reviewers.append(entry)

    return reviewers


def validate_observers(observer_members):
    return {}
