# coding: utf-8
from cgi import escape
import json
import os
import re
import urllib
import urllib2

from flask import make_response, request
from logbook import debug

from pygift.conf import config

URL_PREFIX = config.data['url_prefix']


def simple_pkg(pkg):
    t = urllib2.urlopen(
        "https://pypi.python.org/simple/{}/".format(pkg),
        timeout=15).read()
    t = _wrap_urls_simple(t)
    return t


def _wrap_hrefs(content, host, proto):
    content = re.sub(r'(href=)(["\'])/([^/"][^"]+)\2', r'\1\2{}/world/{}/{}/\3\2'.format(URL_PREFIX, proto, host), content)
    content = re.sub(r'(href=)(["\'])(http:|https:|)//([^/]+)/([^\'"]+)\2', r'\1\2{}/world/_\3/\4/\5\2'.format(URL_PREFIX), content)
    return content


def _wrap_urls_simple(t):
    return re.sub(r'(https?)://([a-z_./A-Z0-9\-]+)', URL_PREFIX + r'/world/\1/\2', t)


def simple_pkg_ver(pkg, ver):
    url = "pypi.python.org/simple/{}/{}/".format(pkg, ver)
    return _fetch(request.method, "https", url)


def setup(app):
    @app.route(URL_PREFIX + "/world/<proto>/<path:url>")
    def world(proto, url):
        proto = proto.lstrip('_').rstrip(':')
        if not proto:
            proto = 'http'

        def post_processing(content):
            host = url.split('/', 1)[0]
            content = _wrap_hrefs(content, host, proto)
            return content

        if request.query_string:
            url = url + '?' + request.query_string

        return _fetch(request.method, proto, url, post_processing)


    @app.route(URL_PREFIX + "/packages/source/<path:path>")
    def packages_source(path):
        url = "pypi.python.org/packages/source/" + path
        return _fetch(request.method, "https", url)


def _fetch(method, proto, url, post_processing=None, content_only=False):
    debug("proxy request: {!r} {!r} {!r}", method, proto, url)

    cache_dir = os.path.join(config.data['cache_dir'], 'proxy')

    is_pkg = any(True for ext in ('.tar.gz', '.tar.bz2', '.tar.xz',
                 '.tar', '.tgz', '.zip') if url.endswith(ext))
    if is_pkg:
        p = os.path.join(cache_dir, "pkgs", os.path.basename(url))
    else:
        p = os.path.join(cache_dir, "index", method, proto, urllib.quote(url, ''))
    pm = os.path.join(cache_dir, "meta", method, proto, urllib.quote(url, ''))

    if not os.path.exists(os.path.dirname(p)):
        os.makedirs(os.path.dirname(p))
    if not os.path.exists(os.path.dirname(pm)):
        os.makedirs(os.path.dirname(pm))

    if not os.path.exists(pm):
        req = urllib2.Request(proto + "://" + url)
        req.get_method = lambda: method
        op = urllib2.build_opener(urllib2.HTTPRedirectHandler)
        r_code = None
        r_headers = None
        r_content = None
        try:
            r = op.open(req, timeout=15)
            r_code = r.getcode()
            r_headers = r.headers.dict
            r_content = r.read()
        except urllib2.HTTPError as e:
            r_code = e.code
            r_headers = {}

        debug("{} returned http code {}", url, r_code)
        if r_code in (200, 404):
            open(pm, 'w').write(
                json.dumps({'headers': r_headers, 'code': r_code}, indent=4))
            if r_code in (200,) and method == 'GET':
                open(p, 'w').write(r_content)

    meta = json.load(open(pm))
    if os.path.exists(p):
        content = open(p).read()
    else:
        content = ''
    if post_processing:
        content = post_processing(content)

    if content_only:
        return content

    resp = make_response(content, meta['code'])

    for k, v in meta['headers'].items():
        if k.lower() in ('content-type', 'content-length', 'last-modified'):
            resp.headers[k] = v
    return resp


def json2simple_pkg_ver(pkg, ver):
    def render(content):
        from urlparse import urlsplit

        d = json.loads(content)
        out = []
        urls = [u['url'] for u in d['urls']]
        urls.append(d['info']['download_url'])

        for url in urls:
            url = _wrap_urls_simple(url)
            url = '<a href="{}">{}</a><br/>'.format(escape(url), escape(pkg))
            out.append(url)

        down_url = d['info'].get('download_url')
        if down_url:
            u = urlsplit(down_url)
            extra = _fetch(request.method, u.scheme, down_url[len(u.scheme) + 3:], content_only=True)
            extra = _wrap_hrefs(extra, host=u.netloc, proto=u.scheme)
            out.append(extra)

        return "\n".join(out)

    url = "pypi.python.org/pypi/{}/{}/json".format(pkg, ver)
    r = _fetch(request.method, "https", url, post_processing=render)
    r.headers['content-type'] = 'text/html'
    del r.headers['content-length']
    return r
