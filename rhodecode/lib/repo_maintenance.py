# -*- coding: utf-8 -*-

# Copyright (C) 2017-2019 RhodeCode GmbH
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

        objects_before = self._count_objects(instance)

        log.debug('GIT objects:%s', objects_before)
        cmd = ['gc', '--aggressive']
        stdout, stderr = instance.run_git_command(cmd, fail_on_stderr=False)

        out = 'executed {}'.format(' '.join(cmd))
        output.append(out)

        out = ''
        if stderr:
            out += ''.join(stderr.splitlines())

        if stdout:
            out += ''.join(stdout.splitlines())

        if out:
            output.append(out)

        objects_after = self._count_objects(instance)
        log.debug('GIT objects:%s', objects_after)
        output.append('objects before :' + objects_before)
        output.append('objects after  :' + objects_after)

        return '\n'.join(output)


class GitFSCK(MaintenanceTask):
    human_name = 'GIT FSCK'

    def run(self):
        output = []
        instance = self.db_repo.scm_instance()

        cmd = ['fsck', '--full']
        stdout, stderr = instance.run_git_command(cmd, fail_on_stderr=False)

        out = 'executed {}'.format(' '.join(cmd))
        output.append(out)

        out = ''
        if stderr:
            out += ''.join(stderr.splitlines())

        if stdout:
            out += ''.join(stdout.splitlines())

        if out:
            output.append(out)

        return '\n'.join(output)


class GitRepack(MaintenanceTask):
    human_name = 'GIT Repack'

    def run(self):
        output = []
        instance = self.db_repo.scm_instance()
        cmd = ['repack', '-a', '-d',
               '--window-memory', '10m', '--max-pack-size', '100m']
        stdout, stderr = instance.run_git_command(cmd, fail_on_stderr=False)

        out = 'executed {}'.format(' '.join(cmd))
        output.append(out)
        out = ''

        if stderr:
            out += ''.join(stderr.splitlines())

        if stdout:
            out += ''.join(stdout.splitlines())

        if out:
            output.append(out)

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
        'git': [GitFSCK, GitGC, GitRepack],
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
            output = task.human_name + ':\n' + task(db_repo).run() + '\n--\n'
            executed_tasks.append(output)
        return executed_tasks
