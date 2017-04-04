import glob
import shutil
import tempfile
import time
import os
from numbers import Number


def create_temp_dir(dir=None, deleteonclose=True):
    path = tempfile.mkdtemp(dir=dir)
    return TemporaryFileOrDirectory(path, deleteonclose=deleteonclose)


def create_temp_file(dir='', prefix='', deleteonclose=True):
    temp_file = tempfile.NamedTemporaryFile(dir=dir, prefix=prefix, delete=False)
    return TemporaryFileOrDirectory(temp_file.name, temp_file=temp_file, deleteonclose=deleteonclose)


class TemporaryFileOrDirectory(object):
    def __init__(self, path, temp_file=None, deleteonclose=True):
        self.path = path
        self.deleteonclose = deleteonclose
        self.temp_file = temp_file

    def close(self):
        if not self.deleteonclose:
            return

        try:
            shutil.rmtree(self.path)
        except NotADirectoryError as e:
            try:
                # make sure file's closed first
                self.temp_file.close()
                os.remove(self.path)
            except OSError:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def root(dir, timeout=None):
    return Root(path=dir, timeout=timeout)


class Root(object):
    _separator = '__'

    def path(self):
        return self._path

    def __init__(self, path, timeout):
        self._path = path
        if not os.path.exists(path):
            os.makedirs(path)
        if timeout is None or isinstance(timeout, Number):
            self._timeout = timeout
        else:
            self._timeout = self._total_seconds(timeout)

    def _total_seconds(self, value):
        if hasattr(value, "total_seconds"):
            return value.total_seconds()
        else:
            return (value.microseconds + (value.seconds + value.days * 24 * 3600) * 10**6) / 10**6

    def create_temp_dir(self, deleteonclose=False):
        self.cleanup()

        return create_temp_dir(dir=self._path, deleteonclose=deleteonclose)

    def create_temp_file(self, prefix, deleteonclose=False):
        self.cleanup()

        return create_temp_file(dir=self._path, prefix=prefix + self._separator, deleteonclose=deleteonclose)

    # make/get/exists convenience methods wrapping
    # prefix style tempfile names
    def make_file(self, name):
        self.delete_file(name)
        return self.create_temp_file(name).path

    def get_file_path(self, name):
        fname_prefix = os.path.join(self._path, name)
        files = [f for f in glob.glob(fname_prefix + "*") if fname_prefix == f[:f.rindex('__')]]
        print(files)
        if len(files) > 0:
            return files[0]

    def delete_file(self, name):
        fname_prefix = os.path.join(self._path, name)
        files = [f for f in glob.glob(fname_prefix + "*") if fname_prefix == f[:f.rindex('__')]]
        print(files)
        if len(files) > 0:
            for filename in glob.glob(files):
                os.remove(filename)

    def exists(self, name):
        fname_prefix = os.path.join(self._path, name)
        files = [f for f in glob.glob(fname_prefix + "*") if fname_prefix == f[:f.rindex('__')]]
        print(files)
        return len(files) > 0

    def cleanup(self):
        if self._timeout is not None:
            self._delete_directories_older_than_timeout()

    def _delete_directories_older_than_timeout(self):
        now = time.time()
        limit = now - self._timeout

        names = os.listdir(self._path)
        for name in names:
            path = os.path.join(self._path, name)
            stat = os.stat(path)

            if max(stat.st_atime, stat.st_mtime) < limit:
                try:
                    shutil.rmtree(path)
                except NotADirectoryError as e:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
