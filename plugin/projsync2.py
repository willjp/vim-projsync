#!/usr/bin/env python
import fnmatch
import json
import os
import platform
import shutil

import vim


class Config(object):
    """ Object representing a [.]projsync.json file (local or global).

    Example:

        .. code-block:: json

            {
                "Work Stuff": {
                    "gitroot": "~/progs/work",
                    "hostnames": ["*-work-*"],
                    "copy_paths": ["/devsync/work"],
                },
                "Windows Stuff": {
                    "gitroot": "~/progs/os/windows",
                    "hostnames": ["*-home-*"],
                    "copy_paths": ["/devsync/windows"],
                }
                ...
            }

    """
    globalconfig = os.path.expanduser('~/.vim/projsync.json')

    def __init__(self, filepath=None):
        if filepath is not None:
            filepath = os.path.abspath(os.path.expanduser(filepath))
        self.__filepath = filepath

    @property
    def filepath(self):
        return self.__filepath

    @property
    def is_globalconfig(self):
        return self.filepath == self.globalconfig

    def validate(self, data, globalconfig=False):
        pass

    def read(self):
        """ Read/Validate the contents of this projsync.json file.
        """
        if self.__data:
            return self.__data

        if not os.path.isfile(self.filepath):
            raise RuntimeError('expected config at: {}'.format(self.filepath))

        with open(self.filepath, 'r') as fd:
            data = json.loads(fd.read())

        self.validate(data, self.is_globalconfig)
        self.__data = data

    def copypaths(self, gitroot):
        """ Returns copypaths defined in this configfile, filtered by
        defined hostname match.

        If this is the globalconfig, it is also filtered by gitroot.

        Returns:
            list: list of copypaths.

                .. code-block:: python

                    [
                        '/devsync/projectA',
                        '/mnt/backup/projectA',
                        ...
                    ]

        """
        data = self.read()
        hostname = platform.node()
        copypaths = set()

        for project in data:
            projdata = data[project]

            # global projsync.json must match the gitrepo,
            # (local projsync.json files imply their parent gitrepo)
            if self.is_globalconfig:
                if not projdata['gitroot'] == gitroot:
                    continue
            if not any([
                fnmatch.fnmatch(hostname, x) for x in projdata['hostnames']
            ]):
                continue

            copypaths.update(set(projdata['copy_paths']))

        return list(copypaths)


class ProjectFile(object):
    """ Object representing a file/directory.
    """
    def __init__(self, filepath=None):
        """ Constructor.

        Args:
            filepath (str, optional):
                Path to file this object will represent.
                If none, defaults to the current vim buffer.
        """
        if filepath is None:
            filepath = vim.current.buffer.name

        self.__filepath = filepath
        self.__config = None
        self.__gitroot = None

    @property
    def filepath(self):
        return self.__filepath

    def gitroot(self):
        """ Searches for the git project root above a given file.
        """
        if self.__gitroot:
            return self.__gitroot

        for parentdir in self.walk_parentdirs():
            # file if submodule, dir if gitroot
            gitpath = '{}/.git'.format(parentdir)
            if os.path.exists(gitpath):
                self.__gitroot = parentdir
                return self.__gitroot

        raise RuntimeError(
            'unable to find git project above "{}"'.format(self.filepath)
        )

    def relpath(self, root):
        if not self.filepath.startswith(root):
            raise RuntimeError(
                (
                    '`root` is not related to `filepath` \n'
                    'root: {}\n'
                    'filepath: {}\n'
                ).format(root, self.filepath)
            )

        if root == self.filepath:
            return ''
        else:
            return self.filepath[len(root) + 1:]

    def walk_parentdirs(self):
        """ Generator, iterating over parent directories.
        """
        # if already at root
        if all([
            os.path.isdir(self.filepath),
            os.path.dirname(self.filepath) == self.filepath,
        ]):
            yield self.filepath

        # walk parents
        else:
            parent_dirpath = None
            dirpath = self.filepath

            while parent_dirpath != dirpath:
                dirpath = parent_dirpath
                parent_dirpath = os.path.dirname(dirpath)
                yield parent_dirpath

    def copypaths(self):
        """ Retrieve list of paths this file should be synchronized to
        (retaining relative path from it's gitroot).

        This will include the global configuration, in addition to copypaths
        defined at any level within the parent hierarchy of the file.

        Returns:
            list: list of copypaths.

                .. code-block:: python

                    [
                        '/devsync/projectA',
                        '/mnt/backup/projectA',
                        ...
                    ]

        """
        # only return copypaths if hostname matches
        gitroot = self.gitroot()
        copypaths = set()

        # local .projsync.json files
        for parentdir in self.walk_parentdirs():
            configpath = '{}/.projsync.json'.format(parentdir)
            if os.path.isfile(configpath):
                config = Config(configpath)
                copypaths.update(set(config.copypaths(gitroot)))

        # global ~/.vim/projsync.json
        config = Config(Config.globalconfig)
        copypaths.update(set(config.copypaths(gitroot)))

        return list(copypaths)


def sync_gitroot(filepath=None, force=False):
    """ copies all files from gitroot to all configured copypaths.

    Args:
        filepath (str, optional):
            A filepath within a git project. Determines which
            gitroot's files get synchronized. If not provided, uses
            the current vim buffer.
    """
    projfile = ProjectFile(filepath)
    gitroot = ProjectFile(projfile.gitroot)
    copypaths = gitroot.copypaths()

    for (root, dirnames, filenames) in os.walk(gitroot.filepath, topdown=False):
        relpath = ProjectFile(root).relpath(gitroot.filepath)
        if relpath:
            relpath += '/'

        for filename in filenames:
            for copypath in copypaths:
                srcpath = '{}/{}'.format(root, filename)
                destpath = '{}/{}{}'.format(copypath, relpath, filename)
                if not force and os.path.isfile(srcpath):
                    if os.path.getmtime(destpath) >= os.path.getmtime(srcpath):
                        continue
                shutil.copyfile(srcpath, destpath)


def sync_file(filepath=None, force=False):
    """ copies one file to all of it's git-project's configured copypaths.

    Args:
        filepath (str, optional):
            Filepath you'd like to sync. If not provided defaults to the
            currently opened vim buffer.
    """
    projfile = ProjectFile(filepath)
    gitroot = projfile.gitroot()

    relpath = projfile.relpath(gitroot)

    for copypath in projfile.copypaths():
        destpath = '{}/{}'.format(copypath, relpath)

        if all([
            not force,
            os.path.getmtime(projfile.filepath) > os.path.getmtime(destpath),
        ]):
            shutil.copyfile(projfile.filepath, destpath)
