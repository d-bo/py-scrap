# -*- coding: utf-8 -*-
"""
Make .xml (python3 makexml.py > out.xml)

<?xml version="1.0" encoding="UTF-8"?>
<products>
    <product>
        <id>Уникальный идентификатор записи</id>
        <name>Наименование товара</name>
        <shortName>Краткое наименование товара</shortName>
        <description>Описание товара без HTML тэгов</description>
        <manufacturer>Производитель</manufacturer>
        <attributes>
            <attribute name="Наименование характеристики"
            unit="Единица измерения"
            id="Уникальный идентификатор характеристики">
                Значение характеристики
            </attribute>
        </attributes>
        <files>
            <file>Путь до файла изображения</file>
        </files>
        <price currency="RUR">Цена</price>
        <code></code>
        <model></model>
        <type></type>
        <category>Категория</category>
        <analogs>
            <analog id="Уникальный идентификатор товара">
                Наименование аналогичного товара
            </analog>
        </analogs>
        <url>Ссылка на товар</url>
    </product>
</products>
"""


import os
from html import escape
import hashlib
from pymongo import MongoClient


SKLAD_BASE_URL = os.getenv('SKLAD_BASE_URL')


def print_prod(rec):

    """ Format output """

    print('<product>')
    print('<id>%s</id>' % hashlib.sha256(escape(rec['chars']['Модель'])
                                         .encode('utf-8')).hexdigest())
    print('<name>%s</name>' % escape(rec['name']))
    print('<shortName>%s</shortName>' % escape(rec['chars']['Модель']))
    print('<description>%s</description>' % escape(rec['desc']))
    print('<manufacturer>%s</manufacturer>' % escape(rec['brand']))
    print('<attributes>')
    for attr in rec['chars']:
        att = attr
        if attr == 'Топливо':
            att = 'Тип топлива'
        if attr == 'Число фаз':
            att = 'Количество фаз'
        if attr == 'Пуск':
            att = 'Тип запуска'
        if attr == 'Наличие автомата ввода резерва (АВР)':
            att = 'Автомат ввода резерва (АВР)'
        if attr == 'Исполнение':
            att = 'Тип исполнения'
        if attr == 'Функция сварки':
            att = 'Наличие сварочного выхода'
        if attr == 'Степень защиты':
            att = 'Класс защиты (IP)'
        if attr == 'Частота':
            att = 'Частота выходного тока'
        if attr == 'Инверторная модель':
            att = 'Инверторный тип альтернатора'
        if attr == 'Тип генератора':
            att = 'Тип альтернатора'
        if attr == 'Расход топлива при 75% нагрузке':
            att = 'Расход "Стандартный" на нагрузке 75%'
        if attr == 'Объем топливного бака':
            att = 'Емкость топливного бака'
        if attr == 'Уровень шума':
            att = 'Уровень шума LpA'
        if attr == 'Производитель двигателя':
            att = 'Марка двигателя'
        if attr == 'Частота вращения двигателя':
            att = 'Номинальное количество оборотов'
        if attr == 'Масса':
            att = 'Вес'
        if attr == 'Гарантия':
            att = 'Стандартная гарантия'
        if attr == 'Генератор':
            att = 'Альтернатор'
        if attr == 'Наличие морского регистра':
            att = 'Морской регистр'
        if attr == 'Генератор':
            att = 'Альтернатор'
        if attr == 'Род сварочного тока':
            att = 'Тип сварочного тока'
        if attr == 'Ток сварки':
            att = 'Сварочный ток'
        if attr == 'Диаметр электр/пров':
            att = 'Диаметр электрода'
        if attr == 'Диаметр электр/пров':
            att = 'Диаметр электрода'
        if attr == 'Функция сварки':
            att = 'Наличие сварочного выхода'
        if attr == 'Сварочный ток макс':
            att = 'Максимальный сварочный ток'
        if attr == 'Сварочный ток мин':
            att = 'Минимальный сварочный ток'
        if attr == 'Наличие речного регистра':
            att = 'Речной регистр'
        print('<attribute name="%s" id="%s">%s</attribute>' %
              (escape(att), hashlib.sha256(escape(att).encode('utf-8'))
               .hexdigest(), escape(rec['chars'][attr])))
    print('</attributes>')
    print('<files>')
    print('<file>img/main.%s</file>' % rec['img_original']
          .replace('{}/'.format(SKLAD_BASE_URL), '').replace('/', '.'))
    print('</files>')
    print('<price currency="RUR">%s</price>' % rec['price'])
    print('<code></code>')
    print('<model></model>')
    print('<type>Электростанции</type>')
    print('<category></category>')
    print('<analogs>')
    for anc in rec['analog']:
        print('<analog id="%s">%s</analog>' %
              (hashlib.sha256(escape(anc).encode('utf-8'))
               .hexdigest(), escape(anc)))
    print('</analogs>')
    print('<url>%s</url>' % rec['url'])
    print('</product>')

    return True


print('<?xml version="1.0" encoding="UTF-8"?>')
print('<products>')

DBC = MongoClient().sklgen.benzin
for _rec in DBC.find():
    print_prod(_rec)
DBC = MongoClient().sklgen.diesel
for _rec in DBC.find():
    print_prod(_rec)
DBC = MongoClient().sklgen.svarka
for _rec in DBC.find():
    print_prod(_rec)
DBC = MongoClient().sklgen.gas
for _rec in DBC.find():
    print_prod(_rec)

print('</products>')
