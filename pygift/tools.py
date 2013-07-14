# coding: utf-8
import re


_version_validate_re = re.compile('git[.][0-9a-f]{40}')


def version_validate(ver):
    return _version_validate_re.match(ver) is not None


def version_commit(ver):
    return ver.split('.', 1)[1]


def __meta(pkg):
    from pygift.conf import config

    registry = config.data['pkgs']
    meta = registry.get(pkg)
    if meta is None:
        return None

    if not isinstance(meta, dict):
        meta = {'url': meta}

    return meta


def get_remote_archive_url(pkg, commit):
    meta = __meta(pkg)
    if meta is None:
        return None

    tpl = meta.get('url')
    if tpl is None:
        return None

    url = tpl.format(commit=commit)
    assert url != tpl, "package spec without {commit} found"

    return url, meta.get('sub_dir')


def can_be_proxied(pkg):
    u"""
    прописан ли у нас этот пакет
    """
    meta = __meta(pkg)
    return meta is None
