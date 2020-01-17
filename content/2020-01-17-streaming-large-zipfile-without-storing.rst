=======================================
Потоковое скачивание больших zip-файлов
=======================================

:slug: streaming-large-zipfile-without-storing
:date: 2020-01-17 20:13:05 +05:00
:category: django
:tags: django, zipfile, optimization


.. image:: {filename}/images/2020-01-17-zipfile.png
   :alt: Zipfile image
   :width: 520px
   :align: left
   :class: post-image

**Задача:** отдавать набор файлов с диска одним zip-архивом без потребления памяти

Как ни странно, стандартных утилит `python` и `django` для этого оказалось недостаточно.
Если вкрадце - для этого написана отдельная либа_, на основе стандартного модуля `zipfile`,
которая решает эту проблему. Как-то так:

.. code-block:: python

   # views.py
   from pathlib import Path

   from django.http import StreamingHttpResponse
   from zipstream import ZipFile, ZIP_DEFLATED


   def some_streaming_zipfile_view(request):
       """A view that streams a large zip-file."""
       zip_stream = ZipFile(mode='w', compression=ZIP_DEFLATED)
       for file_path in Path.home().glob('**/*'):
           zip_stream.write(str(file_path))
    
       response = StreamingHttpResponse(zip_stream, content_type="application/zip")
       response['Content-Disposition'] = 'attachment; filename="home.zip"'
       return response

Первые три строки функции `some_streaming_zipfile_view`, сохраняют имена всех файлов из домашней
директории пользователя. А процедура сжатия начинается уже после выхода из функции:
когда `StreamingHttpResponse` начинает передавать HTTP-body пользователю итерируя `zip_stream`.

Так-же есть форк_ этой либы, который решает некоторые баги.

Но, зачем?
==========

Решаем две проблемы:

* Не потребляем дополнительного места на диске и в оперативной памяти
* | Не ждём сжатия, а начинаем отдавать zip-файл сразу.
  | Избегаем разрывов по таймауту в продакшене на nginx.


Алтернативы
===========

Если в качестве реверс-проки выбран `nginx`, можно воспользоваться его модуем `mod_zip` и `django_zip_stream`_.

К сожалению, больше ничего путного я не нашёл. В том, числе для аналогичной работы c `tarfile`.


.. _либа: https://github.com/allanlei/python-zipstream
.. _форк: https://pypi.org/project/zipstream-new/
.. _django_zip_stream: https://github.com/travcunn/django-zip-stream
