Решаем траблы с ssl в requests
##############################

:slug: solving-issue-with-ssl-in-requests
:date: 2016-07-07 22:50:24 +0500
:category: Python
:tags: requests, ssl

Довольно необычное поведение обнаружил у python библиотеки
requests_
при работе с SSL-сертификатами. Если коротко:
"requests не использует `системные сертификаты`_"

Как можно догадаться это приводит к сообщениям о не безопасном соединении,
тогда как система уже давно доверенняет данному сертификату.

.. _requests: http://requests.readthedocs.io/en/master/
.. _системные сертификаты: http://docs.python-requests.org/en/latest/user/advanced/#ca-certificates

----------
Проявления
----------

Итак, в каких случаях это может быть проблемой?
Например, Вы поддерживаете некий старый проект использующий эту библиотеку
чтобы обращаться к некому внешнему https ресурсу. Если ресурс поменяет
удостоверяющий центр(Certificate Authority - CA), то проект станет считать
ресурс небезопасными и выдавать примерно следующее:

.. code-block:: python

   Traceback (most recent call last):
     File "/home/user/.pyenv/versions/3.3.6/envs/project-3.3.6/lib/python3.3/site-packages/requests/adapters.py", line 376, in send
       timeout=timeout
     File "/home/user/.pyenv/versions/3.3.6/envs/project-3.3.6/lib/python3.3/site-packages/requests/packages/urllib3/connectionpool.py", line 588, in urlopen
       raise SSLError(e)
   requests.packages.urllib3.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:548)

   During handling of the above exception, another exception occurred:

   Traceback (most recent call last):
     File "/home/user/src/project/application/tests.py", line 38, in test_get_token
       token = self.auth_token_mixin.get_token()
     ....
     File "/home/user/.pyenv/versions/3.3.6/envs/project-3.3.6/lib/python3.3/site-packages/requests/adapters.py", line 447, in send
       raise SSLError(e, request=request)
   requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:548)

То-же самое будет, если вы решили выпустить свой корневой сертификат для внутренних
нужд. Не достаточно просто прописать Ваш корневой сертификат в системе, так как
библиотека смотрит не на систему, а на себя.

-----------
Что делать?
-----------

В первом случае придётся один раз обновить библиотеку requests до 2.4.0 и старше.
Начиная с этой версии она использует Certify_
для получения CA, таким образом в дальнейшем можно обновлять только её.

.. _Certify: https://certifi.io/en/latest/

Во втором случае придётся установить переменную окружения *REQUESTS_CA_BUNDLE* в папку где хранятся системные корневые сертификаты, например в debian-системах

.. code-block:: bash

   user@pc ~$ export REQUESTS_CA_BUNDLE=/etc/ssl/certs/

**Спасибо за внимание**
