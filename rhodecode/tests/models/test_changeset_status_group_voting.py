# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

import pytest
import random
from mock import Mock, MagicMock
from rhodecode.model import db
from rhodecode.model.changeset_status import ChangesetStatusModel


status_approved = db.ChangesetStatus.STATUS_APPROVED
status_rejected = db.ChangesetStatus.STATUS_REJECTED
status_under_review = db.ChangesetStatus.STATUS_UNDER_REVIEW


pytestmark = [
    pytest.mark.backends("git", "hg"),
]


class ReviewerMock(object):
    def __init__(self, reviewer_def):
        self.reviewer_def = reviewer_def

    def rule_user_group_data(self):
        return {'vote_rule': self.reviewer_def['vote_rule']}


class MemberMock(object):
    def __init__(self, reviewer_def):
        self.reviewer_def = reviewer_def
        self.user_id = random.randint(1, 1024*1024)


class Statuses(object):
    def __init__(self, member_status):
        self.member_status = member_status

    def get_statuses(self):
        if not self.member_status:
            return []

        ver = 1
        latest = MagicMock(status=self.member_status)
        return [
            [ver, latest]
        ]


@pytest.mark.parametrize("reviewers_def, expected_votes", [
    # empty values
    ({},
     []),

    # 3 members, 1 votes approved, 2 approvals required
    ({'members': [status_approved, None, None], 'vote_rule':2},
     [status_approved, status_under_review, status_under_review]),

    # 3 members,  2 approvals required
    ({'members': [status_approved, status_approved, None], 'vote_rule': 2},
     [status_approved, status_approved, status_approved]),

    # 3 members,  3 approvals required
    ({'members': [status_approved, status_approved, None], 'vote_rule': 3},
     [status_approved, status_approved, status_under_review]),

    # 3 members, 1 votes approved, 2 approvals required
    ({'members': [status_approved, status_approved, status_rejected], 'vote_rule': 2},
     [status_approved, status_approved, status_approved]),

    # 2 members, 1 votes approved, ALL approvals required
    ({'members': [status_approved, None,], 'vote_rule': -1},
     [status_approved, status_under_review]),

    # 4 members, 2 votes approved, 2 rejected, 3 approvals required
    ({'members': [status_approved, status_rejected, status_approved, status_rejected], 'vote_rule': 3},
     [status_approved, status_rejected, status_approved, status_rejected]),

    # 2 members, ALL approvals required
    ({'members': [status_approved, status_approved], 'vote_rule': -1},
     [status_approved, status_approved]),

    # 3 members, 4 approvals required
    ({'members': [status_approved, None, None], 'vote_rule': 4},
     [status_approved, status_under_review, status_under_review]),

    # 4 members, 3 approvals required
    ({'members': [status_approved, status_approved, status_rejected, status_approved], 'vote_rule': 3},
     [status_approved, status_approved, status_approved, status_approved]),

    # 4 members, 3 approvals required
    ({'members': [status_rejected, status_rejected, status_approved, status_approved], 'vote_rule': 3},
     [status_rejected, status_rejected, status_approved, status_approved]),

])
def test_calculate_group_vote(reviewers_def, expected_votes):
    reviewers_data = []

    for member_status in reviewers_def.get('members', []):
        mandatory_flag = True
        reviewers_data.append((
            ReviewerMock(reviewers_def),
            MemberMock(reviewers_def),
            'Test Reason',
            mandatory_flag,
            Statuses(member_status).get_statuses()
        ))

    votes = ChangesetStatusModel().calculate_group_vote(123, reviewers_data)
    assert votes == expected_votes
