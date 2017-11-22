=========================================
Метаклассы Python: Django ORM ChoiceField
=========================================

:slug: python-metaclass-django-orm-choicefield
:date: 2017-11-22 14:38:44 +0500
:category: django
:tags: django, python

# TODO: Картинка
.. image:: {filename}/images/2017-02-11-build-debian-package-pyenv-python-version-management.jpg
   :alt: Террариум Гвидо Мокафико
   :width: 320px
   :align: left
   :class: post-image

Мне всегда нравился лаконичный декларативный синтаксис объявления моделей реализованный в Django ORM.

.. code-block:: python

    class Musician(models.Model):
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
        instrument = models.CharField(max_length=100)

Конечно, на первый взгляд это похоже на магию: нам не нужно объявлять метод __init__ чтобы описать поля класса,
вместо этого мы описываем поля базы данных на уровне класса.

Такой синтаксис возможен благодоря *мета-классам*: классам которые создают классы. Базовый мета-класс `type` -
используется при создании класса с помощью спец-слова `class`. В блоге веб-студии jetfix довольно развёрнутое
`введение в метаклассы`_. Ну а я рассмотрю пример их практического применения для атрибута choices в models.CharField
и forms.ChoiceField.

----
Цель
----

Упростить описание полей ORM с ограниченным выбором:

.. code-block:: python

    class Employee(models.Model):
        FEMALE = 'F'
        MALE = 'M'
        gender = models.CharField('Пол', max_length=1, choices=((FEMALE, 'Женский'), (MALE, 'Мужской')))

Думаю всем хорошо известна данная конструкция, и думаю многих напрягает когда в одной модели сходятся два таких поля,
или одно из полей имеет достаточно большой набор значений. Объявлять их на уровне модели не так удобно, в итоге
объявляем в отдельном классе:

.. code-block:: python

    class Finger(object):
        THUMB = 'T'
        POINTER = 'P'
        MIDDLE = 'M'
        RING = 'R'
        LITTLE = 'L'
        choices = (
            (THUMB, 'Большой'),
            (POINTER, 'Указательный'),
            (MIDDLE, 'Средний'),
            (RING, 'Безымянный'),
            (LITTLE, 'Мизинец'),
        )

    class RingMaterial(object):
        GOLD = 'G'
        SILVER = 'S'
        choices = (
            (GOLD, 'Золото'),
            (SILVER, 'Серебро'),
        )

    class MyRing(models.Model):
        finger = models.CharField('Палец', max_length=1, choices=Finger.choices)
        width = models.IntegerField('Толщина')
        material = models.CharField('Материал', max_length=1, choices=RingMaterial.choices)

Хотя данный способ уже достаточно удобный, он обладает некоторой избыточностью:

* Для объявления одного типа мы должны написать имя константы дважды: при инициализации и в choices
* Обязательный атрибут max_length не информативен - никак не отражает связь с длиной возможных значений

-------
Решение
-------

Приведу сразу пример того, как будет в итоге:

.. code-block:: python

    class Finger(Choices):
        THUMB = ('T', 'Большой')
        POINTER = ('P', 'Указательный')
        MIDDLE = ('M', 'Средний')
        RING = ('R', 'Безымянный')
        LITTLE = ('L', 'Мизинец')

    class RingMaterial(Choices):
        GOLD = ('G', 'Золото')
        SILVER = ('S', 'Серебро')

    class MyRing(models.Model):
        finger = models.CharField('Палец', max_length=len(Finger), choices=Finger)
        width = models.IntegerField('Толщина')
        material = models.CharField('Материал', max_length=len(RingMaterial), choices=RingMaterial)

Что скажете? По-моему - так гораздо локаничней.

А вот и реализация класса Choices, предоставляющего нам эту "магию":

.. _введение в метаклассы: http://blog.jetfix.ru/post/metaklassy-razrushenie-mifov