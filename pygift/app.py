# coding: utf-8
from cgi import escape
import os

from flask import Flask, request, redirect, url_for
import logbook
from logbook import warn, debug
from logbook.compat import RedirectLoggingHandler

from pygift.conf import config
from pygift import proxy, tools


URL_PREFIX = config.data['url_prefix']

core_log_handler = logbook.RotatingFileHandler(os.path.join(config.data['log_dir'], 'app.log'))
core_log_handler.push_application()


app = Flask(__name__)
app.logger.addHandler(RedirectLoggingHandler())


@app.route(URL_PREFIX + '/simple/<pkg>/')
def simple_pkg(pkg):
    u"""
    Зараза pip дёргает эту ручку даже если версия пакета прибита гвоздями.
    Было бы прикольно её поддерживать, чтобы уметь отдавать номер самой последней версии.
    Но пока как это делать быстро, непонятно :(
    """
    debug("pip asking for {!r} available versions", pkg)
    if tools.can_be_proxied(pkg):
        return proxy.simple_pkg(pkg)
    return ''


@app.route(URL_PREFIX + '/simple/<pkg>/<ver>/')
def simple_pkg_ver(pkg, ver):
    u"""
    pip справшивает где скачать пакет такой-то версии — даём ссылку на самих себя
    """
    from pygift.tools import version_validate

    if tools.can_be_proxied(pkg):
        return proxy.simple_pkg_ver(pkg, ver)

    # если пакет публичный - его могут попробовать поставить по обычному номеру версии
    if not version_validate(ver):
        if not tools.is_public(pkg):
            warn("unsupported version requested: {!r}=={!r}", pkg, ver)
            return '<!-- unsupported version format --!>'
        else:
            debug("unsupported version format, yet public pkg, simulating proxy: {!r}=={!r}", pkg, ver)
            return proxy.json2simple_pkg_ver(pkg, ver)

    url = url_for('pkg_generate', pkg=pkg, ver=ver)
    return '<a href="{url}">{pkg}-{ver}</a>'.format(url=escape(url), pkg=escape(pkg), ver=escape(ver))


@app.route(URL_PREFIX + '/generate/<pkg>-<ver>.tar')
def pkg_generate(pkg, ver):
    from pygift.generator import _pkg_generate
    return _pkg_generate(pkg, ver)


@app.route(URL_PREFIX + '/simple/<pkg>')
def simple_pkg_redirect(pkg):
    u"""
    pip всегда запрашивает этот url без '/' на конце,
    а pypi всегда посылает на url с ним
    не будем нарушать традиции, но 301 как бы намекает
    """
    return redirect(request.url + '/', code=301)


@app.route(URL_PREFIX + '/simple/<pkg>/<ver>')
def simple_pkg_ver_redirect(git, pkg, ver):
    u"""
    аналогично `simple_pkg_redirect`
    """
    return redirect(request.url + '/', code=301)


proxy.setup(app)


if __name__ == '__main__':
    app.run(debug=True, host='0', port=11282)
