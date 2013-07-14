pygift

Нахренакозебаян
===============

Дано:
 - проект с кучей зависимостей с замороженными версиями прописанных в requirements.txt (pip install -r reqs.txt)
 - часть зависимостей (особенно опять же собственной разработки) лежат не в pypi, а в git/hg/svn и ставятся через "-e"

Проблемы:
 - "-e" неизбежно потому, что:
 	 1) не всё можно публиковать в публичный pypi.python.org (внутренние пакеты например)
 	 2) непубличный pypi это тоже непросто:
 	 	1) лениво каждый раз заливать пакеты в свой pypi, либо городить сложный continuous integration
 	 	2) надо не забывать обвновлять версю пакета
 - "-e" это плохо потому что:
 	1) использование технологии не по назначению (потенциальные подводные камни)
 		- один уже нашёлся — с editable пакетами не работает wheel
 	2) pip install -r reqs.txt приходится каждый раз перепроверять все -e зависимости (он мог бы этого не делать, но он тупой — а патчить не хочется)


Решение:
 - сервис симулирующий pypi, который умеет выдавать пакеты напрямую из git + автоподмена версии пакета в setup.py


Установка
=========

1) обычный wsgi application, — рекомендуется к запуску через gunicorn + nginx
2) конфиг в /etc/pygift.json

На убунте:
# sudo apt-get install nginx gunicorn python-flask python-pip python-demjson  -V
# sudo pip install pygift
# sudo mkdir -p /var/cache/pygift && sudo chown www-data /var/cache/pygift
# sudo mkdir -p /var/log/pygift && sudo chown www-data /var/log/pygift

# sudo cp /etc/pygift.example.json /etc/pygift.json

# sudo service gunicorn restart
# sudo tail /var/log/gunicorn/pygift.log  # just check if there are no errors where

# sudo ln -vs /etc/nginx/sites-available/pygift.conf /etc/nginx/sites-enabled/
# sudo service nginx restart

# sudo editor /etc/pygift.json


Использование
=============

1) прописать пакеты и репозитории в /etc/pygift.json
2) в requirements.txt добавить строчку --index-url=http://pygift.example.org/pygift/simple/
2a) возможно ещё понадобится строчка --extra-index-url=https://pypi.python.org/simple/
3) прописать в reqs.txt нужные пакеты как package==git.6ae9311329df3ef8986518d15faf96d2c632133e # <- git-ревизия
4) ...
5) PROFIT!! aka можно пользоваться pip install -r requirements.txt


Проблемы и решения
==================

Трабла: при каждом вызове `pip install -r reqs.txt` часть пакетов всё равно переустанвливается
Солюшн: проверьте название пакета — в reqs.txt и в pygift.json должно быть прописано тоже самое что выводит, например, `pip freeze`
