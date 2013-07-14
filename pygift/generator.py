# coding: utf-8
from flask import send_file, make_response
import glob
from logbook import info, error
import os
import shutil
import subprocess
import tempfile
import urllib2

from pygift import cache


setup_py_tpl = """
def versioned_du_setup(**attrs):
    attrs['version'] = {version!r}
    return core_du_setup(**attrs)

import distutils.core
core_du_setup = distutils.core.setup
distutils.core.setup = versioned_du_setup


def versioned_st_setup(**attrs):
    attrs['version'] = {version!r}
    return core_st_setup(**attrs)

import setuptools
core_st_setup = setuptools.setup
setuptools.setup = versioned_st_setup


original_setup_code = r'''
{original_setup_code}
'''
exec(compile(original_setup_code, __file__, 'exec'))
""".lstrip()


def _pkg_generate(pkg, ver):
    from pygift import tools

    if not tools.version_validate(ver):
        return make_response('unsupported version format', 404)

    commit = tools.version_commit(ver)
    archive_url, archive_sub_dir = tools.get_remote_archive_url(pkg, commit) or (None, None)
    if not archive_url:
        return make_response('unknown package', 404)

    archive_path = cache.retrieve(pkg, commit)
    if archive_path is None:
        archive_path = _fetch_n_build_archive(
            archive_url,
            commit=commit,
            pkg=pkg,
            ver=ver,
            archive_sub_dir=archive_sub_dir
        )

    return send_file(
        archive_path,
        mimetype='application/x-tar',
    )


def _unpack(dst_path, tmp_base):
    ext = os.path.splitext(dst_path)[1]
    if ext == '.tar':
        cmd = ['tar', '-xf']
    elif ext == '.tar.gz' or ext == '.tgz':
        cmd = ['tar', '--gzip', '-xf']
    elif ext == '.tar.bz2' or ext == '.tbz2':
        cmd = ['tar', '--bzip2', '-xf']
    elif ext == '.tar.xz' or ext == '.txz':
        cmd = ['tar', '--xz', '-xf']
    elif ext == '.zip':
        cmd = ['unzip', '-q']
    else:
        assert False, "unsupported archive: {!r}".format(ext)

    cmd = cmd + [dst_path]
    try:
        output = subprocess.check_output(cmd, cwd=tmp_base, stderr=subprocess.STDOUT)
        info("unpack output: {}", output.rstrip())
    except subprocess.CalledProcessError as e:
        error("unpack failed {!r} {}", cmd, e.output.rstrip())
        raise


def _fetch_n_build_archive(archive_url, commit, pkg, ver, archive_sub_dir):
    tmp_base = tempfile.mkdtemp()
    try:
        archive_type = os.path.splitext(archive_url)[1]
        assert archive_type[0] == '.'
        dst_path = os.path.join(tmp_base, 'tmp' + archive_type)

        info("fetching {!r}", archive_url)
        src = urllib2.urlopen(archive_url, timeout=50)

        with open(dst_path, 'w') as dst:
            done = 0
            chunk = 5*(1024**2)
            buf = '-'
            while buf != '':
                buf = src.read(chunk)
                done += len(buf)
                dst.write(buf)
                info("done {} mb", round(done/1024./1024., 1))
        src.close()
        info("done, unpacking {!r}", dst_path)
        _unpack(dst_path, tmp_base)
        os.unlink(dst_path)

        subdir = list(glob.glob(tmp_base + '/*'))
        subdir = [d for d in subdir if os.path.isdir(d)]
        assert len(subdir) == 1, repr(subdir)
        subdir = subdir[0]

        if archive_sub_dir:
            subdir = os.path.join(subdir, archive_sub_dir)

        info("done, patching")
        original_setup_code = open(os.path.join(subdir, 'setup.py')).read()
        original_setup_code = original_setup_code.replace("'''", "''' \"'''\" '''")
        open(os.path.join(subdir, 'setup.py'), 'w').write(setup_py_tpl.format(
            version=ver,
            original_setup_code=original_setup_code,
        ))
        info("done, packing back")
        subprocess.check_call(['tar', '-cf', os.path.join(tmp_base, 'new.tar'), os.path.basename(subdir)], cwd=os.path.dirname(subdir))
        info("done, returning back to user")

        archive_path = cache.store(os.path.join(tmp_base, 'new.tar'), pkg, commit)
        return archive_path
    finally:
        shutil.rmtree(tmp_base)
