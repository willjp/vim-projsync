import os
import shutil
import vim


class Config(object):
    """ Object representing a [.]projsync.json file (local or global).
    """
    def __init__(self, filepath=None):
        self.__filepath = filepath

    @property
    def filepath(self):
        return self.__filepath

    @staticmethod
    def get(filepath):
        """ Find the configfile to use for a particular file.

        Returns:
            Config: a config instance.
        """
        pass

    def validate(self, data):
        pass

    def read(self, force=False):
        pass

    def copypaths(self, gitroot):
        # only return copypaths if hostname matches
        pass


class SyncCache(object):
    def clear(self):
        pass


class ProjectFile(object):
    def __init__(self, filepath=None):
        if filepath is None:
            filepath = vim.current.buffer.name

        self.__filepath = filepath
        self.__config = None
        self.__gitroot = None

    @property
    def filepath(self):
        return self.__filepath

    def config(self):
        if not self.__config:
            self.__config = Config.get(self.filepath)
        return self.__config

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
        if root not in self.filepath:
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
            return root[len(gitroot) + 1:]

    def walk_parentdirs(self):
        """ Generator, iterating over parent directories.
        """
        # if already at root
        if all([
            os.path.isdir(self.filepath),
            os.path.dirname(self.filepath) == self.filepath,
        ]):
            return self.filepath

        # walk parents
        parent_dirpath = None
        dirpath = self.filepath

        while parent_dirpath != dirpath:
            dirpath = parent_dirpath
            parent_dirpath = os.path.dirname(dirpath)
            yield parent_dirpath


def clear_cache(config=None):
    if not config:
        config = Config.get()

    config.clear()


def sync_all(filepath=None, force=False):
    """ copies all files from gitroot to all configured copypaths.

    Args:
        filepath (str, optional):
            A filepath within a git project. Determines which
            gitroot's files get synchronized. If not provided, uses
            the current vim buffer.
    """
    projfile = ProjectFile(filepath)
    gitroot = projfile.gitroot()
    config = projfile.config()

    copypaths = config.copypaths(gitroot)

    for (root, dirnames, filenames) in os.walk(gitroot, topdown=False):
        relpath = ProjectFile(root).relpath(gitroot)
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
    config = projfile.config()

    relpath = projfile.relpath(gitroot)

    for copypath in config.copypaths(gitroot):
        destpath = '{}/{}'.format(copypath, relpath)

        if all([
            not force,
            os.path.getmtime(projfile.filepath) > os.path.getmtime(destpath),
        ]):
            shutil.copyfile(projfile.filepath, destpath)
