====================
Fabric автоматизация
====================

:slug: Fabric-automation
:date: 2016-07-15 15:10:07 +0500
:category: Devops
:tags: deploy, fabric

.. image:: {filename}/images/2016-07-15-deploy.png
   :alt: fabric deploy web
   :width: 320px
   :align: left
   :class: post-image

Итак, Ваш веб-проект, готовый поразить весь мир своей гениальностью, уже написан?
Тогда вам надо срочно развернуть его на каком-нибудь бесперебойном сервере, типа VPS,
а потом продолжить добавлять функционал и фиксить баги...

Однако, зайдя в 100 раз по ssh на сервер и выполнив рутинную цепочку команд:

.. code-block:: bash

   $ git pull
   $ ./manage.py migrate
   $ ./manage.py collecstatic
   $ ./manage.py compilemessages
   $ supervisorctl restart my_best_project

Вы не сможете не задуматься о том, как же всё-таки автоматизировать этот процесс.
Что ж, для этого обязательно есть решение!

Тут я приведу один из способов, котором в данный момент пользуюсь: библиотекой
Fabric_ для python

.. _Fabric: http://www.fabfile.org/

--------------
Принцип работы
--------------

В python есть библиотека paramiko_, которая является
реализацией SSH протокола, как сервера, так и клиента. С помощью неё также можно
отправлять файлы по SFTP-протоколу на удалённый сервер, но сейчас речь не об этом.
Итак, с помощью этой библиотеки мы можем зайти на сервер и выполнить любую команду,
выглядит это примерно так:

.. code-block:: python

   >>> import paramiko
   >>> ssh = paramiko.SSHClient()
   >>> ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   >>> ssh.connect('127.0.0.1', username='stretch', password='lol')
   >>> stdin, stdout, stderr = ssh.exec_command("uptime")
   >>> stdout.readlines()
   [u' 13:25:52 up 8 days, 47 min,  5 users,  load average: 4.89, 4.74, 4.33\n']

Довольно сложно для запуска 1 команды, не правда ли? Чтобы было удобно обновлять наш проект, придётся сделать некую
надстройку над этим низким уровнем для удобства работы.

.. _paramiko: http://www.paramiko.org/

----------------------------------
Либо взять готовое решение: Fabric
----------------------------------

Эта библиотека предоставляет удобный интерфейс для написания скриптов удалённо запускаемых команд. Вот как выглядит удалённый запуск того-же uptime:

.. code-block:: python

   from fabric.api import run, env

   env.hosts = ['stretch@localhost']

   def test():
       run("uptime")

Вот так: читаемо и понятно. Сохраняем в файл fabfile.py и выполняем в терминале

.. code-block:: bash

   $ fab test
   [stretch@localhost] Executing task 'test'
   [stretch@localhost] run: uptime
   [stretch@localhost] out:  13:44:14 up 8 days,  1:05,  6 users,  load average: 5.15, 4.59, 4.47
   [stretch@localhost] out:


   Done.
   Disconnecting from localhost... done.

Итак, разберём этот пример по-подробней:

1. Мы имеем дело с обычным python-скриптом, т.е. мы можем так-же использовать любые
   другие библиотеки / свои функции в сочетании с fabric
2. Библиотека предоставляет набор функций для работы с удалёнными серверами,
   которые расположены в
   fabric.api.operations_
3. Параметры запуска можно настраивать через специальный объект -
   env_
4. Задачи описываются в виде обычных функций, которые могут быть запущены через
   ``fab <имя задачи>``, таким образом отпадает необходимость в конструкции
   ``if __name__ == '__main__':`` и ручном разборе параметров запуска
   передавать их в задачу
   `тоже очень легко`_

.. _fabric.api.operations: http://docs.fabfile.org/en/1.11/api/core/operations.html
.. _env: http://docs.fabfile.org/en/1.11/usage/env.html
.. _тоже очень легко: http://docs.fabfile.org/en/1.11/usage/fab.html#task-arguments

-----------
Мои рецепты
-----------

Обновляем список задач cron
===========================

Вы всё ещё в ручную вбиваете список задач крона? Хватит над собой издеваться!
Файл со списком задач лежит на сервере, а значит он может быть утерян, или исправлен
кем-то по-ошибке. Кроме того, открыв проект на своей машине, или в репозитории, вы
не знаете какая задача как часто выполняется и не храните историю изменений этого
файла. Лучше всего хранить список задач cron в проекте, а на сервере выполнять ``$ cat config/cron.conf | crontab -``

fab-задача
----------

.. code-block:: python

    def update_crontab(cron_path):
        cron_not_ends_with_new_line = cron_missing = True
        with settings(warn_only=True):
            cron_missing = run("test %s" % cron_path).failed
            if not cron_missing:
                command = "test `tail -n 1 %s | wc --lines` -gt 0" % cron_path
                cron_not_ends_with_new_line = run(command).failed
        if not cron_missing:
            if cron_not_ends_with_new_line:
                if not confirm("Your crontab have not been installed! No new line "
                               "at the end of the file. Continue anyway?"):
                    abort("Aborting at user request.")
            run('cat {cron} | crontab -'.format(cron=cron_path))

Обновление конфигурации веб-сервера
===================================

То-же самое можно сказать про конфигурацию веб-сервера. Как вы можете быть уверены,
что всё то, что вы настроили на сервере не пропадёт? Или некий криворукий
администратор в вашей компании не поправит файл без согласования с Вами? Лучше
попросить администратора дать вам права на sudo без пароля на команды обновления
конфигураций сервера. Как-то так

   web-project    ALL = NOPASSWD: /bin/cp -f [A-Za-z/.-]*/web-project/prod/[A-Za-z/.-]* /etc/nginx/sites-available/web-project

   web-project    ALL = NOPASSWD: /usr/sbin/service nginx reload

и зашить обновление в задачу fabric

fab-задача
----------

.. code-block:: python

    def update_nginx():
        """
        Обновляет конфигурацию nginx'а и запускает их в работу
        """
        # 1. Копируем конфигурацию файла в конфиг-папку на сервере
        run('sudo cp -f {source} {target}'.format(
            source=config_files['nginx'],
            target=remote_configs['nginx']))
        # 2. Говорим демону перечитать конфигурации
        run('sudo service nginx reload')

Различные роли серверов
=======================

Что если проект должен быть развёрнут сразу на нескольких серверах, которые будут заниматься
решением разных задач? Для этого есть так называемые `роли серверов`_
С их помощью Вы можете определить на каких машинах должно выполняться то или иное задание.
Так например, можно вынести тяжёлые скрипты для обработки данных
или сложных вычислений на отдельный сервер и ваше веб-приложение не будет тормозить.
А за счёт автоматизации, период времени когда исполняемый код на серверах отличался
сводится к минимуму.

.. _роли серверов: http://docs.fabfile.org/en/1.11/usage/execution.html?highlight=roles#roles

fab-задача
----------

.. code-block:: python

    env.roledefs = {
        'web': ['my_project@web'],
        'celery': ['my_project@grinder'],
    }
    # ....

    @task
    @roles('web')
    def update_web():
        run("git pull")
        update_nginx()
    # ...

    @task
    @roles('celery')
    def update_celery():
        run("git pull")
        update_crontab()

----------
Заключение
----------

В целом мне больше нечего сказать.. Согласен, это был довольно краткий обзор и я не
рассмотрел все достоинства и недостатки этой библиотеки. Я даже не сравнил её с
каким-то другим аналогом.

Главное что я хотел донести: если Вы используете ручной труд для выполнения
повседневных задач, Ваше время утекает впустую!

Единственный способ избежать этого - выбрать средство автоматизации и освоить его.

**Успехов!**
