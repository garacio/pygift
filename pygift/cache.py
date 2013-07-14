# coding: utf-8
import os
import re
from pygift.conf import config


def _file_path(pkg, commit):
    cache_dir = config.data['cache_dir']
    assert re.match('[A-Za-z0-9_\-]+', pkg)
    assert re.match('[0-9a-f]{40}', commit)
    return os.path.join(cache_dir, 'patched', pkg, commit + '.tar')


def retrieve(pkg, commit):
    path = _file_path(pkg, commit)
    return path if os.path.exists(path) else None


def store(tmp_pkg_path, pkg, commit):
    path = _file_path(pkg, commit)
    assert path.endswith('.tar')
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    os.rename(tmp_pkg_path, path)
    return path
