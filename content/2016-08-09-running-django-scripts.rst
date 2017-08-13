======================
Запуск скриптов Django
======================

:slug: running-django-scripts
:date: 2016-08-09 15:09:00+0500
:category: Django
:tags: scripting

.. image:: {filename}/images/2016-08-09-do-it-without-django-setup.ipg.jpeg
   :alt: Давай-ка без django.setup(), бро!
   :width: 320px
   :align: left
   :class: post-image

При написании программы на python очень удобно проверять результаты своей работы на
практике. Все интерпретируемые языки этому способствуют. Так быстрее! Не знаешь как
работает метод или функция, документация отсутствует, исходный код печалит?
Ок - пишем скриптик с примерным поведением и смотрим на результат. И прояснилось!..

Однако, с django появляются некоторые особенности, которые я рассмотрю в этой статье

-----------
Особенности
-----------

Пути к модулям
==============

Любой проект на django содержит как минимум 2 модуля python

- модуль настроек проекта - ``settings``, ``urls``, ``wsgi``
- модуль вашего приложения с представлениями, шаблонами, статикой и прочим

Если вы положите ваш скрипт в корень проекта, то, скорее всего, проблем не возникнет.
Однако, в больших проектах, так делать не очень удобно, тем более хранить такие
скрипты там в дальнейшем (для демонстрации работы непонятной функции например)

А если положите в какой-нибудь модуль, то изменятся пути к остальным скриптам проекта
и импорты не будут работать:

.. code-block:: python

   from my_app import views  # не работает т.к. my_app не в PYTHONPATH

Чтобы исправить надо прописывать корневую директорию проекта в системную переменную ``PYTHONPATH``
или вызывать скрипты всегда из этой директории

Settings и Django ORM
=====================

Правильно загружать файл настроек Django надо с помощью

.. code-block:: python

   from django.conf import settings

Однако, чтобы воспользоваться этим вам надо

* задать переменную DJANGO_SETTINGS_MODULE
* выполнить django.setup() до импорта settings

C ORM ситуация такая же, если выполните import ваших моделей, до того как выполните
``django.setup()``, ORM будет не рабочей.

Вот и появляются весьма странные конструкции

.. code-block:: python

    if __name__ == '__main__':
        import sys, os
        from os.path import abspath, dirname, join
        sys.path.insert(0, abspath(join(dirname(__file__), '..')))
        os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
        import django
        django.setup()

в самом верху скрипта, где по pythonic-way ничего кроме ``import`` быть не должно!

-------------
Как правильно
-------------

В Django есть возможность написания своих собственных команд для скрипта manage.py,
который лежит в корне и предназначен для управления вашим проектом.
Давайте, руководствуясь `документацией`_,
напишем команду exec, которая будет выполнять произвольный скрипт в нашем проекте.

.. _документацией: https://docs.djangoproject.com/en/1.8/howto/custom-management-commands/

Простой запуск
==============

Создаём в любом приложении django пакет management, а в нём пакет commands.
В последнем пакете создаём exec.py и помещаем туда следующий код

.. code-block:: python

   from django.core.management import BaseCommand
   from django.utils.module_loading import import_string

   class Command(BaseCommand):
       help = 'Выполнить функцию в скрипте проекта'

       def add_arguments(self, parser):
           parser.add_argument('function', type=str)

       def handle(self, *args, **opts):
           function = import_string(opts['function'])
           return function()

Всё довольно просто, API django для написания команд полагается на модуль ``argparse``.
В функции ``add_arguments`` мы задаём аргументы для запуска команды, а в ``handle``
определяем действия которые мы выполним после того как пользователь передаст
корректные параметры. Теперь если мы хотим в модуле, к примеру:
``my_app.examples.simple`` выполнить функцию run пишем:

.. code-block:: bash

   $ ./manage.py exec my_app.examples.simple.run

Запуск функции с аргументами
============================

Можно усложнить задачу и сделать возможным запуск функции с параметрами.
Благодаря тому что python язык интерпретируемый, мы можем легко узнать какие
параметры нам требуются. А аннотации типов в python3 помогут нам привести типы
из строковых в числовые и булевы.
Вот что у меня получилось:

.. code-block:: python
   :linenos: table

    import inspect
    import celery.app.task
    import decimal
    from django.core.management import BaseCommand
    from django.utils.module_loading import import_string


    class Command(BaseCommand):
        help = 'Выполнить функцию в скрипте проекта'

        def add_arguments(self, parser):
            parser.add_argument('function', type=str)

            parser.add_argument('args', nargs='*', type=str)

        def handle(self, *args, **opts):
            function = import_string(opts['function'])
            if not inspect.isfunction(function):
                if isinstance(function.__class__, celery.app.task.TaskType):
                    function = function.run
                else:
                    raise NotImplementedError('Wrong function! {0!r}'.format(function))
            fullArgSpec = inspect.getfullargspec(function)
            if len(args) < (len(fullArgSpec.args or ()) - len(fullArgSpec.defaults or ()) +
                            len(fullArgSpec.kwonlyargs or ()) - len(fullArgSpec.kwonlydefaults or ())):
                raise AttributeError('Not enough arguments for function {function}'.format(**opts))

            kwargs = dict((kwarg_key, args[i]) for i, kwarg_key in enumerate(fullArgSpec.args + fullArgSpec.kwonlyargs) if i < len(args))
            if fullArgSpec.annotations:
                for kwarg, annotation in fullArgSpec.annotations.items():
                    if any(annotation is cs for cs in (int, float, complex, decimal.Decimal)):
                        # Эти типы можно создать передав в конструктор str
                        kwargs[kwarg] = annotation(kwargs[kwarg])
                    elif annotation is bool:
                # Булевый тип переводим - 'False'=>False, 'True'=>True, остальное => None
                        kwargs[kwarg] = {'False': False, 'True': True}.get(kwargs[kwarg], None)
            return function(**kwargs)

Как видно из примера, я также предусмотрел возможность запуска функций заключённых в
декоратор ``@celery.task``, это специфика конкретного проекта. Способы приведения
типов также могут быть различны, всё зависит только от Вас.

**Успехов!**
