#!/usr/bin/env python2
"""
Name :          projsync.py
Created :       July 21 2016
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Configure vim to copy files to other location(s)
                     relative to the project's git-root on file-save
                     (or whenever else it is useful to you)

                     ex:
                         /home/dev/scripts/.git                        >> /devsync/win32/
                         /home/dev/scripts/ python/animtools/file.py   >> /devsync/win32/ python/animtools/file.py
________________________________________________________________________________
"""
# builtin
from __future__ import absolute_import, division, print_function
import os
import shlex
import subprocess
import shutil
import json
import logging
import platform
import fnmatch
# external
import vim
# internal

logger = logging.getLogger(__name__)
ll = locals


#!TODO: there is no reason this needs to be a class.. break it up.
#!TODO: ProjSync could be a singleton (?)


class ProjSync(object):
    def __init__(self, debug=False):
        """ Constructor.

        Args:
            debug (bool, optional):
                When set to ``True`` prints additional debug information

        """
        self.debug = debug
        self.proj_configs = {}  # { gitroot : {(json file contents)} }
        #  stores main config, and every encountered localconfig

    def clear(self):
        """ Clears all cached information about config-files.
        """
        self.proj_configs = {}

    def sync_all(self):
        """ For the opened file's 'gitroot'
        Removes all files in each 'copy_paths' location,
        then copies all files from gitroot into each 'copy_paths' location.

        Notes:
            Designed to be run every time you switch git-branches.
        """

        # get filepath, and it's gitroot (which identifies it's project)
        filepath = vim.current.buffer.name
        gitroot = self._find_gitroot(filepath)

        # delete everything under each 'copy_path'
        # (but not copypath itself, since that is generally a shared folder)
        project_copypaths = self.get_copypaths(
            gitroot=gitroot, filedir=gitroot
        )

        for copypath in project_copypaths:
            for filepath in os.listdir(copypath['path']):
                cwd = copypath['path']
                copypath_path = '{cwd}/{filepath}'.format(**ll())

                if copypath['method'] == 'copy':
                    if self.debug:
                        print('Recursively Deleting path: "{}"'.format(
                            copypath_path)
                        )
                    try:
                        if os.path.isdir(copypath_path):
                            shutil.rmtree(copypath_path)
                        else:
                            os.remove(copypath_path)
                    except(Exception):
                        print('error deleting: "{}"'.format(copypath_path))

                else:
                    logger.error(
                        'bad config - unknown method: "{method}"'.format(**copypath))

        # copy all files under each 'copy_path'
        ##
        for (cwd, dirs, files) in os.walk(gitroot, topdown=False):
            project_copypaths = self.get_copypaths(
                gitroot=gitroot, filedir=cwd
            )

            for filename in files:
                filepath = '{}/{}'.format(cwd, filename)
                for copypath in project_copypaths:
                    gitroot_filepath = filepath.replace(gitroot, '')
                    if copypath['method'] == 'copy':
                        self._pushmethod_copy(
                            filepath, gitroot_filepath, copypath)
                    else:
                        logger.error(
                            'bad config - unknown method: "{method}"'.format(**copypath))

    def push_file(self, filepath=None, gitroot=None, project_copypaths=None):
        """ Copies the file from active vim buffer to all of it's git-project's
        configured 'copy_paths'.

        Notes:
            All timestamps/file-attrs should be preserved.
            Designed to run every time you save a file.

        Args:
            filepath (str, optional) ``(ex: '/home/dev/myfile.py' )``
                path to the file to be copied. If no file is provided,
                the currently opened filepath in the active vim buffer
                is used.

            gitroot (str, optional): ``(ex: '/home/dev' )``
                If you already know the gitroot, you may provide it here.

            project_copypaths (str, optional): ``(ex: ['/devsync/project/scripts', ...] )``
                If you already know the copy_paths, you may provide them
                here.
        """
        # get filepath, and it's gitroot (which identifies it's project)
        if not filepath:
            filepath = vim.current.buffer.name

        gitroot = self._find_gitroot(filepath)
        gitroot_filepath = filepath.replace(gitroot, '')

        # identify path from gitroot, and all dirs to copy to
        if not project_copypaths:
            project_copypaths = self.get_copypaths(filepath)

        # for each copypath, handle it's method
        # (currently copy only, but potential for scp, rsync, ...)
        if not project_copypaths:
            if self.debug:
                print('No copy_paths configured')
            return

        for copypath in project_copypaths:
            if copypath['method'] == 'copy':
                self._pushmethod_copy(filepath, gitroot_filepath, copypath)
            else:
                logger.error(
                    'bad config - unknown method: "{method}"'.format(**copypath))

    def _find_gitroot(self, filepath):
        """
        Inspects a filepath, and returns it's
        git project-root (location containing .git dir)
        """
        filedir = os.path.dirname(filepath)
        if self.debug:
            print('finding git-root from: "%s"' % filedir)
        pipe = subprocess.Popen(
            shlex.split('git rev-parse --show-toplevel'),
            cwd=filedir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pipe.wait()

        if pipe.returncode != 0:
            logger.error('returncode: {}'.format(pipe.returncode))

            if self.debug:
                print('Searching for gitroot from: {}'.format(filedir))
                for line in pipe.stderr:
                    print(line)
                raise RuntimeError('Error finding gitroot')

        else:
            gitroot = pipe.stdout.readline()
            if self.debug:
                print('Using gitroot: {}'.format(gitroot))
            return gitroot.strip()

    def _pushmethod_copy(self, filepath, gitroot_filepath, config):
        """
        Copies 'filepath' to ['copy_paths']['path'],
            * using file-attributes from 'filepath' (including last-modified)

        ( handler for 'copy_paths' keys using method 'copy' )
        """
        copypath_path = os.path.expanduser(config['path'])
        copypath_path = '{}/{}'.format(copypath_path, gitroot_filepath)

        if not os.path.isdir(os.path.dirname(copypath_path)):
            os.makedirs(os.path.dirname(copypath_path))

        if os.path.isfile(copypath_path):
            try:
                os.remove(copypath_path)
            except(Exception):
                print('error deleting: "%s"' % copypath_path)

        if self.debug:
            print('copying file "{filepath}" > "{copypath_path}"'.format(
                    filepath=filepath, copypath_path=copypath_path
                )
            )

        try:
            shutil.copy2(filepath, copypath_path)
        except(Exception):
            print('Error copying: "{filepath}" > "{copypath_path}"'.format(
                    filepath=filepath, copypath_path=copypath_path
                )
            )

    def _delmethod_copy(self, filepath, gitroot_filepath, config):
        """ Copies 'filepath' to ['copy_paths']['path'],
        Using file-attributes from 'filepath' (including last-modified)

        ( handler for 'copy_paths' keys using method 'copy' )
        """
        HOME = os.environ['HOME']

        copypath_path = config['path']
        copypath_path.replace('~', HOME)
        copypath_path = '{copypath_path}/{gitroot_filepath}'.format(**ll())

        if not os.path.isdir(os.path.dirname(copypath_path)):
            os.makedirs(os.path.dirname(copypath_path))

        if self.debug:
            print('deleting file "{copypath_path}"'.format(**ll()))

        if os.path.isfile(copypath_path):
            os.remove(copypath_path)

    def get_copypaths(self, filepath=None, filedir=None, gitroot=None):
        """
        Based on JSON config, and the file's gitroot,
        retrieves the locations that the file should also be copied to

        Args:
            filepath (str):  ``(ex: '/home/dev/progs/myscript.py' )``
                path to the file you are operating on (copying).
                (generally this is the currently opened file in vim)

            filedir (str, optional):
                path to the directory containing your file
                (obtained if you do not know it)

            gitroot (str, optional):
                path to your file's project's gitroot (if you know it)

        Returns:
            the contents of the 'copy_paths' key for the relevant json file:

            .. code-block:: python

                # if copypaths exist
                [
                    { "method":"copy", "path":"/devsync/test" },
                    { "method":"copy", "path":"/devsync/test2" },
                ]

                # if copypaths do not exist
                []
        """
        HOME = os.environ['HOME']

        # identify gitroot
        if not gitroot:
            gitroot = self._find_gitroot(filepath)
            if not gitroot:
                logger.debug(
                    'file not in a git-project. ignoring: "%s"' % filepath)
                return

        # identify file's config
        config = self._get_fileconfig(filepath=filepath, filedir=filedir)
        if not config:
            logger.debug(
                'no JSON config detected for filepath: "%s"' % filepath)
            return []

        # return copy_paths

        # in local json files, the gitroot project is implied
        # they only need to contain the key 'copy_paths', and it's contents
        if 'copy_paths' in config:
            return config['copy_paths']

        # if we are using the central ~/.vim/projsync.json, then
        # we need to find if our current gitroot exists in there
        else:
            for project in config:
                if not 'gitroot' in config[project]:
                    raise RuntimeError(
                        'Invalid Project Config. Every project must contain the key "gitroot". project "%s"' % project)
                if not 'copy_paths' in config[project]:
                    raise RuntimeError(
                        'Invalid Project Config. Every project must contain the key "copy_paths". project "%s"' % project)
                if not 'hostnames' in config[project]:
                    raise RuntimeError(
                        'Invalid Project Config. Every project must contain the key "hostnames". project "%s"' % project)

                project_gitroot = config[project]['gitroot'].replace('~', HOME)
                project_hostnames = config[project]['hostnames']

                # check if gitroot matches project's gitroot
                if gitroot == project_gitroot:

                    # check if hostname matches the projsync config
                    host_match = False
                    for hostname in project_hostnames:
                        if fnmatch.fnmatch(platform.node(), hostname):
                            host_match = True
                            break

                    if host_match:
                        if self.debug:
                            print('Project Identified: %s' % project)
                        return config[project]['copy_paths']

            if self.debug:
                print('current gitroot not found in config: gitroot "%s"' % gitroot)

    def _get_fileconfig(self, filepath=None, filedir=None):
        """
        configs can be stored in the following locations:

            * ``projsync.json``  in same directory as file
            * ``.projsync.json`` in the same directory as file
            * ``~/.vim/projsync.vim`` global configuration

        Args:
            filepath (str):
                The path to the file you are operating on.

            filedir (str, optional):
                Alternatively, if you are working with an entire directory
                of files, you may pass the file's directory directly

        Returns:
            the entire contents of the JSON file that applies to your file.

            .. code-block:: python

                    {
                        "testproj" :{
                            "path" :      "/home/vagrant/dev",
                            "copy_paths": [
                                        { "method":"copy", "path":"/devsync/test" },
                                        { "method":"copy", "path":"/devsync/test" },
                                    ]
                        }
                    }
        """
        HOME = os.environ['HOME']

        if filedir:
            cwd = filedir
        else:
            cwd = os.path.dirname(filepath)

        def save_new_config(config_path=None, cwd=None):
            """
            reads a config_file,
            saves contents under current-working-directory
            with last-mod-date for future reference

            Args:
                config_path (str, optional):  ``(ex: '/path/to/projsync.json' )``
                    The config's full filepath.

                cwd (str, optional):  ``(ex: '/path/ro' )``
                    the path to the config
            """
            if self.debug:
                print('using config from: "{config_path}"'.format(**ll()))
            with open(config_path, 'r') as ff:
                config = json.load(ff)
            self.proj_configs[cwd] = {'config_path': cwd,
                                      'mtime': os.path.getmtime(config_path),
                                      'conts': config,
                                      }
            return config

        json_paths = [
            '{cwd}/projsync.json'.format(**ll()),
            '{cwd}/.projsync.json'.format(**ll()),
            '{HOME}/.vim/projsync.json'.format(**ll()),
        ]

        existing_project = False
        if self.proj_configs:
            if cwd in self.proj_configs:
                existing_project = True

        # If this directory's config has already been read,
        # Check if config has changed since last read (reload if changed)
        if existing_project:
            config_path = self.proj_configs[cwd]['config_path']
            last_mtime = self.proj_configs[cwd]['mtime']
            if self.debug:
                print('reusing existing config: "%s"' % config_path)

            if os.path.getmtime(config_path) > last_mtime:
                return save_new_config(cwd=config_path)

        # Otherwise, figure out which json-config to use for this
        # file, load & save
        else:
            if self.debug:
                print('No config stored for cwd: {cwd}'.format(**ll()))
            for path in json_paths:
                if os.path.isfile(path):
                    return save_new_config(path)
                elif self.debug:
                    print('No config found at: {path}'.format(**ll()))

        # otherwise, (no config for project, or filepath)
        return False


if __name__ == '__main__':
    pass
