# coding: utf-8
import os
from logbook import info, warn
import demjson


class Config(object):
    def __init__(self):
        self._initialized = False
        self._data = None
        self._mtime = None
        self._path = None

    @property
    def data(self):
        if self._needs_update():
            self._reread()
        return self._data

    def _reread(self):
        conf_name = 'pygift.json'
        conf_dirs = (
            os.path.dirname(os.path.abspath(__file__)),
            '/etc',
        )
        conf_paths = (
            os.path.join(conf_dir, conf_name)
            for conf_dir in conf_dirs
        )
        self._path = next(
            (path for path in conf_paths if os.path.exists(path)),
            None
        )
        if not self._path:
            self._data = {}
            warn('config not found')
        else:
            info('using config {!r}', self._path)
            self._mtime = os.path.getmtime(self._path)
            with open(self._path) as f:
                self._data = demjson.decode(f.read())
        self._initialized = True

    def _needs_update(self):
        return not self._initialized or self._mtime != os.path.getmtime(self._path)


config = Config()
__ALL__ = [config]
