# -*- coding: utf-8 -*-

# Copyright (C) 2017-2018 RhodeCode GmbH
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

log = logging.getLogger(__name__)


class MaintenanceTask(object):
    human_name = 'undefined'

    def __init__(self, db_repo):
        self.db_repo = db_repo

    def run(self):
        """Execute task and return task human value"""
        raise NotImplementedError()


class GitGC(MaintenanceTask):
    human_name = 'GIT Garbage collect'

    def _count_objects(self, repo):
        stdout, stderr = repo.run_git_command(
            ['count-objects', '-v'], fail_on_stderr=False)

        errors = ' '
        objects = ' '.join(stdout.splitlines())

        if stderr:
            errors = '\nSTD ERR:' + '\n'.join(stderr.splitlines())
        return objects + errors

    def run(self):
        output = []
        instance = self.db_repo.scm_instance()

        objects = self._count_objects(instance)
        output.append(objects)
        log.debug('GIT objects:%s', objects)

        stdout, stderr = instance.run_git_command(
            ['gc', '--aggressive'], fail_on_stderr=False)

        out = 'executed git gc --aggressive'
        if stderr:
            out = ''.join(stderr.splitlines())

        elif stdout:
            out = ''.join(stdout.splitlines())

        output.append(out)

        objects = self._count_objects(instance)
        log.debug('GIT objects:%s', objects)
        output.append(objects)

        return '\n'.join(output)


class HGVerify(MaintenanceTask):
    human_name = 'HG Verify repo'

    def run(self):
        instance = self.db_repo.scm_instance()
        res = instance.verify()
        return res


class SVNVerify(MaintenanceTask):
    human_name = 'SVN Verify repo'

    def run(self):
        instance = self.db_repo.scm_instance()
        res = instance.verify()
        return res


class RepoMaintenance(object):
    """
    Performs maintenance of repository based on it's type
    """
    tasks = {
        'hg': [HGVerify],
        'git': [GitGC],
        'svn': [SVNVerify],
    }

    def get_tasks_for_repo(self, db_repo):
        """
        fetches human names of tasks pending for execution for given type of repo
        """
        tasks = []
        for task in self.tasks[db_repo.repo_type]:
            tasks.append(task.human_name)
        return tasks

    def execute(self, db_repo):
        executed_tasks = []
        for task in self.tasks[db_repo.repo_type]:
            executed_tasks.append(task(db_repo).run())
        return executed_tasks
