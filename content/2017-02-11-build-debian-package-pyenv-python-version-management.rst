========================================================
Собираем debian-пакет для pyenv (менеджер версий python)
========================================================

:slug: build-debian-package-pyenv-python-version-management
:date: 2017-02-11 00:46:24 +0500
:category: Devops
:tags: debian, python, pyenv, Makefile


.. image:: {filename}/images/2017-02-11-build-debian-package-pyenv-python-version-management.jpg
   :alt: Террариум Гвидо Мокафико
   :width: 320px
   :align: left
   :class: post-image

Прошло уже около года как я открыл для себя менеджер версий python - pyenv_.
Теперь даже сложно представить как мне не надоедало вручную устанавливать python всякий
раз когда понадобится новая версия (отличная от распространяемой в репозиториях debian).
Не говоря уже о том, что действия приходилось повторять, при выкатывании нового проекта
на сервер. С pyenv установка выполняется в 1 команду:

.. code-block:: bash

   ~$ pyenv install 3.5.3

Очень не плохо `описал работу с pyenv`_ Адиль Хаштамов в своём блоге.

В этой статье я опишу свой способ установки pyenv на сервер с debian в виде debian-пакета.
Это может быть интересно тем, у кого в рамках одного сервера работают несоклько проектов.
А так-же тем, кто хочет научиться собирать пакеты debian. Бытует мнение что это очень сложно..
Ну, а по моему дак, не на много сложнее чем в arch'е.

.. _pyenv: https://github.com/yyuu/pyenv
.. _описал работу с pyenv: https://khashtamov.com/2015/12/pyenv-python/

-----------------
pyenv не в $HOME?
-----------------

Идея поставить pyenv в систему родилась после того как на одной из виртуалок для 5 проектов
скачивал pyenv в $HOME/.pyenv и ставил python. При этом в трёх из них версия питона была одна
и та-же (миноры не в счёт, в них совместимость не ломают).

Расстроившись от такой избыточности, я попробовал поставить /opt/pyenv и для всех пользователей
прописать PYENV_ROOT. Но, в этом случае, возникают проблемы с правами на файлы
при выполнении команды ``pyenv rehash`` (пересобирает shims_). Так что пришлось откатиться..

Однако, идея поставить на уровень системы меня не покидала, так что я выработал примерный список
требований и задал вопрос мейнтейнеру на `github`_ 'е.
Пинок в сторону "Unix's file permissionissues" - "setgid and/or sticky bit" меня вполне удовлетворил.
А для того чтобы автоматизировать развёртывание и обновление на серверах - выбрал сборку pyenv в
виде debian-пакета, так как других систем под рукой пока не водится.

.. _shims: https://github.com/yyuu/pyenv#understanding-shims
.. _github: https://github.com/yyuu/pyenv/issues/820


Требования
==========

1. Устанавливать pyenv в директорию системы, например /usr/share/pyenv или /opt/pyenv
2. Настроить его так чтобы дать пользователям из группы pyenv права на установку новых python
3. Автоматическая инициализация pyenv при добавлении пользователя в соответствующую группу
4. Удаление интерпритатора недоступно пока не удалены все виртуальные окружения
5. Установка виртуальных окружений в рамках пользователя:
   - в идеале остальные не должны видеть окружения других пользователей
   - как минимум - удалять окружение должен уметь только текущий пользователь
6. Зависимости для установки новых python должны ставиться вместе с pyenv
7. Сборка пакета debian должна быть автоматизирована - хотя бы тем-же make

----------------------------------------
Собираем debian-пакет с помощью Makefile
----------------------------------------

Для нетерпеливых сразу даю `ссылку на gist`_ c результатами работы.
Дальше опишу чуть более подробно, чем в комментариях в Makefile.

В плане сборки debian-пакета очень полезно почитать с `эту статью с хабра`_ от Марка Вартаняна.
В комментах тоже много дельних советов присутствует

Всю работу по сборке в Makefile разбил на 4 этапа:

1. Клонирование репозиториев
2. Обновление репозиториев
3. Сбор данных для пакета из репозиториев
4. Сборка пакета на основе полученных данных

В шапку скинем используемые пути, чтобы было удобно их менять при необходимости

.. code-block:: Makefile

    # Used directories
    PYENV_SRC=pyenv.src
    PYENV_BUILD=pyenv
    PYENV_TARGET=$(PYENV_BUILD)/usr/share/pyenv
    # Files wich needs to be removed from debian package
    NOT_NEEDED_FILES=.agignore CHANGELOG.md CONDUCT.md .git .gitignore LICENSE \
        Makefile src test .travis.yml .vimrc plugins/.gitignore plugins/*/.git \
        plugins/*/.gitignore plugins/*/test plugins/*/LICENSE
    # Extract version from control for package name
    VERSION="`cat $(PYENV_BUILD)/DEBIAN/control|grep 'Version:'|awk '{print $$2}'`"

Эти переменные вычисляются в момент запуска любого сценария make. Заметьте что
синтаксис $(VARIABLE) очень похож на синтаксис bash, но shell для вычисления этих
переменных не вызывается. Первое время это сильно запутывает, - например, для того
чтобы в Makefile выполнить ``echo $HOME`` надо писать ``echo $$HOME``. Тогда make поймёт
что требуется не его переменная, а символ $ для передачи интерпритатор команд.

Переменная VERSION просто хранит команду, которая будет выполнена в одном из сценариев.
С помощью неё мы достанем актуальную версию, для имени пакета.

.. _ссылку на gist: https://gist.github.com/mnach/9ab2f6381d23ddfe70891f25b5ca888e
.. _эту статью с хабра: https://habrahabr.ru/post/78094/

Клонирование
============

.. code-block:: Makefile

    # initial clone - pyenv and relevant plugins
    pyenv.src:
        curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer\
            | PYENV_ROOT=$(PYENV_SRC) bash
        git clone https://github.com/jawshooah/pyenv-default-packages \
            $(PYENV_SRC)/plugins/pyenv-default-packages

Можно вручную склонировать список репозиториев: сам pyenv плюс его плагины.
Я же чуть сократил число строк с помощью pyenv-install, + добавил плагин
pyenv-default-packages, чтобы при установке нового python устанавливался virtualenv.
Плагин pyenv-virtualenv может устанавливать его сам, но мы поставим его сразу, чтобы
под другим пользователем не столкнутся с ошибкой контроля доступа.

Задача названа также, как и директория в которую клонируется pyenv. Таким образом,
она не будет выполняться повторно. Makefile крут, не так ли? =)

Обновление
==========

Скажем спасибо плагину pyenv-update, выполнив задачу в 1 команду

.. code-block:: Makefile

    # pyenv-update do all work for us
    update:
        PYENV_ROOT=$(PYENV_SRC) PATH="$(PYENV_SRC)/bin:$(PATH)" pyenv update

Конфиругирование
================

Задача сбора данных для пакета зависит от предыдущих двух, чтобы её выполнить
сначала выполняются эти две.

.. code-block:: Makefile

    # configure build dir
    pyenv: pyenv.src update
        rm -Rf $(PYENV_BUILD);
        `# move pyenv directory to PYENV_TARGET`
        mkdir -p `dirname $(PYENV_TARGET)`
        cp -R pyenv.src $(PYENV_TARGET)
        cd $(PYENV_TARGET) && rm -Rf $(NOT_NEEDED_FILES)

Сначала всё просто - копируем pyenv в нужную директорию, а затем удаляем все
ненужные файлы.

.. code-block:: Makefile

    pyenv:
        `# users from pyenv group can write to those directories`
        mkdir -p -m 775 $(PYENV_TARGET)/cache
        mkdir -p -m 775 $(PYENV_TARGET)/shims
        mkdir -p -m 775 $(PYENV_TARGET)/versions

Разрешаем писать в эти директории всем из группы pyenv.

.. code-block:: Makefile

    pyenv:
        `# install virtualenv for all new pythons`
        echo "virtualenv" > $(PYENV_TARGET)/default-packages
        `# all pythons must have envs for virutual environments`
        cp mkdir-envs.bash $(PYENV_TARGET)/plugins/pyenv-default-packages/etc/pyenv.d/install/

Выставляем дефолтные приложения и добавляем сценарий добавляющий директорию envs с
нужными правами (чтобы пользователи группы pyenv могли ставить виртуальные окружения)

.. code-block:: Makefile

    pyenv:
        `# copy profile.d and doc directory in usr`
        mkdir -p $(PYENV_BUILD)/etc/profile.d
        cp pyenv.sh $(PYENV_BUILD)/etc/profile.d
        mkdir -p $(PYENV_BUILD)/usr/share/doc/pyenv
        cp copyright $(PYENV_BUILD)/usr/share/doc/pyenv
        gzip --best -k -c changelog.Debian > $(PYENV_BUILD)/usr/share/doc/pyenv/changelog.Debian.gz
        `# package information`
        mkdir $(PYENV_BUILD)/DEBIAN
        for file in conffiles control postinst postrm preinst; do \
            cp $$file $(PYENV_BUILD)/DEBIAN; \
        done

Копируем pyenv.sh в profile.d - это стандартный код инициализации pyenv за
исключением проверки на принадлежность пользователя группе pyenv:
``groups | grep &>/dev/null '\bpyenv\b'``

Копируем неотъемлимые части пакета - copyright, changelog, а также файлы
в директорию DEBIAN. В них самое интересное! Вот самое главное в postinst,
он выполняется сразу после установки:

.. code-block:: bash

    chown root:pyenv -R /usr/share/pyenv
    chmod g+s /usr/share/pyenv/versions
    chmod +t /usr/share/pyenv/versions

Во второй строчке ставим SGID на директорию, для того чтобы все новые файлы
и папки создавались под группой pyenv. Это не обязательно, но я подумал что так
будет логичней. А в третьей - стики бит, если его выставить, то только владелец
файла сможет его удалить. Стики бит также будем ставить для папок envs в скрипте
mkdir-envs.bash

Сборка
======

Ну тут всё просто - собираем пакет с помощью dpkg-deb, fakeroot нужен чтобы
выставлять права файлов как root:root. Для полученного пакета выставляем версию
через команду из переменной VERSION. Кто-то ведь её ещё помнит?

.. code-block:: Makefile

    build: pyenv
        fakeroot dpkg-deb --build $(PYENV_BUILD)
        mkdir -p dists
        mv -v pyenv.deb dists/pyenv_$(VERSION)_all.deb

Готовый пакет можно проверить утилитой - lintian. Она проверяет правильно ли
собран пакет.

----------
Заключение
----------

Чтож.. В результате мы получили средство автоматической сборки pyenv,
который ставится на уровень системы. Обновить pyenv на серверах или поставить
на новый теперь будет чуть легче.

К сожалению, пока я не понял как реализовать четвёртный пункт Требований.
Пятый пункт тоже реализован не полностью. Но чтобы их реализовать надо вмешиваться
в исходный код проекта, чего я сознательно не хотел делать. Рано.. на сейчас
мне и так хватит.

Спасибо что дочитали до конца. Надеюсь было не слишком занудно?.. :-)
