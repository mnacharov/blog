=========================================
Метаклассы Python: Django ORM ChoiceField
=========================================

:slug: python-metaclass-django-orm-choicefield
:date: 2017-11-22 11:48:44 +0500
:category: django
:tags: django, python

.. image:: {filename}/images/2017-11-24-we-need-to-go-deeper.jpg
   :alt: We need to go deeper
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
используется при создании класса с помощью спец-слова `class`. В блоге веб-студии jetfix написали довольно развёрнутое
`введение в метаклассы`_. Ну а я рассмотрю пример их практического применения для атрибута choices в models.CharField
и forms.ChoiceField.

.. _введение в метаклассы: http://blog.jetfix.ru/post/metaklassy-razrushenie-mifov

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

* Для объявления одного типа мы должны написать имя константы дважды: при инициализации и при добавлении в choices
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

Ну вот, так гораздо локаничней!

А вот и реализация класса Choices, предоставляющего нам эту "магию":

.. code-block:: python

    class ChoicesMetaclass(type):
        field_re = re.compile('^[A-Z][^a-z]*$')

        def __new__(cls, name, bases, dct):
            choices = []
            for field, value in tuple(dct.items()):
                if cls.field_re.match(field):
                    if isinstance(value, tuple) and len(value) == 2:
                        choice, message = value
                        dct[field] = choice
                    elif isinstance(value, str):
                        choice, message = value, field
                    else:
                        continue
                    choices.append((choice, message))
            dct['choices'] = tuple(choices)
            return super(ChoicesMetaclass, cls).__new__(cls, name, bases, dct)

        def __iter__(self):
            return self.choices.__iter__()

        def __len__(self):
            if self.choices:
                return max(len(field) for field, value in self.choices)
            return 0

    class Choices(metaclass=ChoicesMetaclass):
        """Базовый класс для описания атрибута choices в forms.ChoiceField и models.CharField"""

Итак, главное что делает этот метакласс определено в методе __new__: сбор статических переменных класса
объявленных без букв нижнего регистра и инициализированных строкой или кортежем с двумя значениями в переменную choices.

Таким образом у нас 2 варианта инициализации одного из choices:

  1. `MIDDLE = 'M'` тогда в choices подставится `('M', 'MIDDLE')`
  2. через кортеж `MIDDLE = ('M', 'Средний')`, значение которого перекочует в choices как есть, а в него
     подставится только значение - `MIDDLE = 'M'`.

Дополнительно, мы определили два "магических" метода:

| `__iter__` - позволяет нам использовать класс как итератор, и избавляет от необходимости обращатся к choices вручную.
| Писать `choices=Finger.choices` слишком сложно, это же петон :)

`__len__` - вызывается встроеным оператором `len`, и избавляет от необходимости считать размер для CharField

------
Выводы
------

Метаклассы существенно расширяют возможности наследования: они позволяют переопределить логику создания новых классов.
Используя данный инструмент, можно упростить некоторые конструкции в ваших программах.

Но, как говориться "The greater the force, the greater the responsibility", не дайте себе всё испортить!

Пока! Наслаждайтесь кодом!