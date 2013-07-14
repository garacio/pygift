#!/usr/bin/env python
from distutils.core import setup


setup(
    name='pygift',
    version='2',
    author='Denis Orlikhin',
    author_email='qbikk@ya.ru',
    url='''https://github.com/overplumbum/pygift''',
    packages=['pygift'],
    requires=[
        'Flask',
        'Logbook',
        'demjson',  # json config with comments
    ],
    data_files=[
        ('/etc/nginx/sites-available/', [
            'etc/nginx/sites-available/pygift.conf']),
        ('/etc/gunicorn.d/', ['etc/gunicorn.d/pygift']),
        ('/etc/', ['etc/pygift.example.json']),
    ]
)
