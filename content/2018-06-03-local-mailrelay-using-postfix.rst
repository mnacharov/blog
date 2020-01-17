===========================================
Локальный почтовый релей средствами postfix
===========================================

:slug: local-mailrelay-using-postfix
:date: 2018-06-03 11:36:11 +0500
:category: devops
:tags: postfix, smarthost, relay, debian, docker


.. image:: {filename}/images/2018-06-03-local-mailrelay-using-postfix.jpeg
   :alt: Postfix as mail relay
   :width: 440px
   :align: left
   :class: post-image
	   
Эх.. Давненько я уже ничего не писал. Сложное это дело писать на естественных языках.
Толи дело на языках программирования! :-) Жаль что NDA часто не даёт выкладывать
шедевры на всеобщее обозрение. Иногда чуствуешь себя поэтом продающим свой талант.

Ну, довольно лирики! Сегодня хочу поделиться простым решением отказоустойчивой
отправки почты с использованием SMTP-сервера postfix установленного локально.

------
Зачем?
------

Проблема отказов при отправке почты возможна при сетевых ошибках (все мы знаем о
внезапных блокировках всего интернета РКН), а также при превышении квот на отправку
писем. Случай с квотами вполне вероятен при использовании публичных серверов для
отправки писем созданных автоматически (сообщения об ошибках, списки рассылок и т.п.)

Вариантов решения может быть несколько. У всех один принцип: локальная очередь
сообщений. Реализация может быть сколь угодно изощерённой - каждый любит свои
велосипеды..

Тут опишу пример использования очереди сообщений postfix, e-mail сервера очень часто
используемого как в качестве локального почтаря (в `*nix` всегда есть место почте),
так и для построения корпоративных почтовых систем.

Кстати, дополнительным бонусом локальной очереди e-mail сообщений является скорость
отправки. Так как письма идут на localhost, они доходят практически мгновенно. И, Вы
можете не беспокоиться о задержках в вашем web-приложении.

--------------------------------------
Postfix в качестве ретранслятора писем
--------------------------------------

В общем это будет стандартное тупое пошаговое руководство, ни в коем случае не претендующее на полноту. Велком

Ставим!
=======

Наш SMTP-сервер есть в репозиториях большинства unix-систем. Буду приводить команды использованные мной на debian 9 (stretch).

.. code-block:: bash

    ~# apt-get update
    ~# apt-get install postfix

При установке будет предложено выполнить базовую конфигурацию (если нет, переходим к
следующей главе)


.. code-block:: text

    Postfix Configuration
    ---------------------

    Please select the mail server configuration type that best meets your needs.

    No configuration:
     Should be chosen to leave the current configuration unchanged.
    Internet site:
     Mail is sent and received directly using SMTP.
    Internet with smarthost:
     Mail is received directly using SMTP or by running a utility such
     as fetchmail. Outgoing mail is sent using a smarthost.
    Satellite system:
     All mail is sent to another machine, called a 'smarthost', for delivery.
    Local only:
     The only delivered mail is the mail for local users. There is no network.

     1. No configuration  2. Internet Site  3. Internet with smarthost
     4. Satellite system  5. Local only
    General type of mail configuration: _

Тут нас спрашивают, как мы хотим использовать postfix:

1. без конфигурации (сделать всё самому)
2. Публичный SMTP сервер: сам отправляет и получает почту
3. Smarthost - это и есть релей(ретранслятор) почты: получает почту и пересылает её
   публичным серверам для реальной доставки (входит под каким-либо пользователем)
4. Satellite - спутник, имеет доступ к Smarthost, не знает как отправлять публичным
   серверам (не хранит учётных данных)
5. Локальный: получает почту и сохраняет её в файлики, в пределах одной машины

Выбираем вариант 3. Мы дадим postfix публичную учётку, а к нему будем стучаться без
учётки на localhost

.. code-block:: text

    The "mail name" is the domain name used to "qualify" _ALL_ mail addresses without
    a domain name. This includes mail to and from <root>: please do not make
    your machine send out mail from root@example.org unless root@example.org has told
    you to.

    This name will also be used by other programs. It should be the single, fully
    qualified domain name (FQDN).

    Thus, if a mail address on the local host is foo@example.org, the correct value
    for this option would be example.org.

    System mail name: _

Доменное имя почтаря. Сохраняется в /etc/mailname. Для smarthost не имеет особого
смысла. Я указал relay.example.com

.. code-block:: text

   Please specify a domain, host, host:port, [address] or [address]:port. Use the form
   [destination] to turn off MX lookups. Leave this blank for no relay host.

   Do not specify more than one host.

   The relayhost parameter specifies the default host to send mail to when no entry is
   matched in the optional transport(5) table. When no relay host is given, mail is
   routed directly to the destination.

   SMTP relay host (blank for none): _

Просят указать публичный сервер на который наш smarthost будет отправлять письма.
А "optional transport(5) table", это более продвинутый случай: по отправителю
postfix может определять через какой сервер отправлять почту. Тогда указанный в этом
пункте сервер[:порт] будет использоваться "по-умолчанию". Пишем, к примеру: `smtp-mail.outlook.com:587`.

На этом с установкой всё. Наш конфиг к этому времени выглядит `примерно так`_

.. _примерно так: https://bitbucket.org/snippets/webnach/yedpay/revisions/b01c319a981062815f34b552604238ff1506b2f3

Настройка
=========

По большому счёту всё что нам осталось сделать это прописать метод аутентификации
на сервере. Я рассмотрю 2 варианта: первый - все письма отправляются через один
сервер, второй - сервер зависит от отправителя

Всё просто
----------

Давайте в секцию `# TLS parameters` добавим следующие опции:

.. code:: text

    smtp_use_tls = yes
    smtp_tls_security_level = encrypt
    smtp_tls_note_starttls_offer = yes
    smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache
    # Authentication
    smtp_sasl_auth_enable = yes
    smtp_sasl_security_options = noanonymous
    smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd

Первые четыре обязывают postfix пользоваться шифрованием. Последние три - указывают
что на сервер надо ходить под пользователями определёнными в файле sasl_passwd

А в этом файле укажем нашего пользователя

.. code:: text

    smtp-mail.outlook.com:587 secret.user@outlook.com:very-strong-password

И запустим `postmap` для создания файла sals_passwd.db и говорим `postfix` подтянуть
новую конфигурацию

.. code:: bash

    ~# postmap hash:/etc/postfix/sasl_passwd
    ~# postfix reload

Проверяем:

.. code:: bash

    ~$ echo "Test Body"| mail -aFrom:secret.user@outlook.com -s 'Testing' secret.user@outlook.com

Если были проблемы с отправкой смотрим что говорит posfix: `tail -f /var/log/mail.log`.
Так, например, в моём случае outlook.com отклонял письма так как к аккаунту не был
привязан телефон. А ещё, я получал ошибку "не найден хост smtp-mail.outlook.com" пока
не скопировал resolv.conf в chroot-окружение postfix'а:
`cp /etc/resolv.conf /var/spool/postfix/etc/`.
Видимо схватил какой-то косяк при установке..

`Конфигурация`_

.. _Конфигурация: https://bitbucket.org/snippets/webnach/yedpay/revisions/afbd22e40e513809e931fa596592526d8613394f

Чуть сложнее
------------

Привяжем второй ящик к нашему ретранслятору, руководствуясь вот этой
`замечательной статьёй`_.

Добавляем в main.cf:

.. code:: text

    # Multiple ISP
    smtp_sender_dependent_authentication = yes
    sender_dependent_relayhost_maps = hash:/etc/postfix/relayhost_map
	  
Создаём файл relayhost_map:

.. code:: text

    # Per-sender provider
    secret.user@outlook.com         smtp-mail.outlook.com:587
    another.user@yahoo.com          smtp.mail.yahoo.com:587

И вносим правки в наш файл с паролями sasl_passwd

.. code:: text

    # Per-sender authentication
    secret.user@outlook.com secret.user@outlook.com:very-strong-password
    another.user@yahoo.com  another.user@yahoo.com:yet-another-password

    # Login for the default relayhost
    smtp-mail.outlook.com:587 secret.user@outlook.com:very-strong-password

Вот и всё! Осталось создать `*.db` файлы для relayhost_map и sasl_passwd и подопнуть
posfix:

.. code:: bash

    ~# postmap hash:/etc/postfix/sasl_passwd
    ~# postmap hash:/etc/postfix/relayhost_map
    ~# postfix reload

Проверяем:

.. code:: bash

    ~$ echo "Test Body"| mail -aFrom:secret.user@outlook.com -s 'Testing' another.user@yahoo.com
    ~$ echo "Test Body"| mail -aFrom:another.user@yahoo.com -s 'Testing' secret.user@outlook.com

Получаем по письму в каждом из наших ящиков.

`Результат`_

.. _замечательной статьёй: https://www.cyberciti.biz/faq/postfix-multiple-isp-accounts-smarthost-smtp-client/
.. _Результат: https://bitbucket.org/snippets/webnach/yedpay/revisions/31b0c879477714ced3fd54c30cd4c5c3d578742a

------
Docker
------

Ну как не включить пол-слова о модных технологиях!

Вообще говоря, всё что мы сделали, можно выполнить всего одной командой, если на вашем
хосте есть докер.

Я пользовался образом `alterrebe/postfix-relay`_ для поднятия релея в одну команду. Но
в целом, при желании можно собрать и свой, с возможностью нескольких ISP в том числе.

.. code:: bash

    ~# docker run -d -h relay.example.com --name="mailrelay" \
         -e SMTP_LOGIN=secret.user@outlook.com -e SMTP_PASSWORD=very-strong-password \
         -e EXT_RELAY_HOST=smtp-mail.outlook.com -e EXT_RELAY_PORT=587 -e USE_TLS=yes \
         -p 127.0.0.1:25:25 alterrebe/postfix-relay

Подняли контейнер с именем mailrelay, в котором запущен postfix, с пробросом портов на
наш localhost:25. Файлы конфигурации будут созданы на основе переменных окружения
переданных с помощью флагов -e.


.. _alterrebe/postfix-relay: https://hub.docker.com/r/alterrebe/postfix-relay/

----
Итог
----

Мы подняли postfix в качестве smarthost - ретранслятора почты.

Он выполняет за нас авторизацию в публичных почтовых сервисах. И, если они оказываются
недоступными, хранит отправленные нами письма в локальной очереди (файлы).

Мы можем просматривать очередь сообщений с помощью утилиты `mailq` или `postqueue`.

В наших веб-приложениях получили:

* отказоустойчивость отправки (временные сетевые ошибки больше не страшны)
* ускорение отклика в web-приложениях при выполнении действий, приводящих к отправке
  почты
