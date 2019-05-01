# -*- coding: utf-8 -*-
""" Resource parse module """

import os
import asyncio
from multiprocessing import Pool
import urllib.request
import aiohttp
from bs4 import BeautifulSoup as bsoup
from pymongo import MongoClient


SKLAD_BASE_URL = os.getenv('SKLAD_BASE_URL')


def parse_brand(soup):

    """ Extract brand """

    crumbs = soup.find_all('span',
                           {'class': 'bread_crumbs__no-right-padding'})
    if crumbs:
        _brand = crumbs[len(crumbs)-1].find('span', {'itemprop': 'name'})
        if _brand:
            brand = _brand.text
    return brand


def parse_chars(soup):

    """ Extract characteristics """

    characteristics = {}
    chars = soup.find('div', {'class': 'technical_characteristics_table'})
    if chars:
        tr_label = None
        tr_value = None
        trs = chars.find_all('tr')
        if trs:
            for trc in trs:
                tr_label = trc.find('div',
                                    {'class': 'fl f-label no_margin'})
                if tr_label:
                    tr_label = tr_label.text.strip().replace(':', '')

                if tr_label is None:
                    tr_label = trc.find('div',
                                        {'class': 'f-label no_margin'})
                    if tr_label:
                        tr_label = tr_label.text.strip().replace(':', '')

                tr_value = trc.find('td', {'class': 'params_value'})
                if tr_value:
                    tr_value = tr_value.text.strip().replace("\n", '') \
                        .replace("\t", ' ').replace("         ", '')
                if tr_value != '' and tr_label is not None:
                    characteristics[tr_label.replace('.', '')] = tr_value
    return characteristics


def parse_analog(soup):

    """ Extract analog products """

    analog_prods = []
    analog = soup.find('table',
                       class_='product_list variant_table \
                       product_list__table-fix-bg')
    if analog is not None:
        analogs = analog.find_all('tr')
        for anal in analogs:
            proda = anal.find_all('a')
            if proda is not None:
                j = 0
                for ahref in proda:
                    if j == 1:
                        analog_prods.append(ahref.text.strip()
                                            .replace("\n", '')
                                            .replace("\t", ''))
                    j += 1
    return analog_prods


async def extract_prod(session, url, dbc, prefix):

    """ Extract single product """

    async with session.get(url) as resp:
        if resp.status != 200:
            return False
        txt = await resp.text()
        soup = bsoup(txt, "lxml")

        # brand
        brand = parse_brand(soup)

        # name
        name = soup.find_all('meta', {'itemprop': 'name'})
        if name:
            name = name[0]['content']

        # characteristics table
        characteristics = parse_chars(soup)

        # prod type
        prod_type = name.replace(characteristics['Модель'], '').strip()

        # desription
        desc = soup.find('div',
                         {'class': 'page_content product_useful_content'})
        if desc:
            desc = desc.text.strip().replace("\n", '').replace("\t", ' ')

        # price
        price = soup.find('span', class_='blue_bold price')
        if price:
            price = price.text.strip().replace("\n", '').replace(" ", '')

        # img
        img = soup.find('div', class_='product_photo baguetteBox')
        if img:
            img = img.find('img')
            if img is not None:
                img = img['src']

        # analog prods
        analog_prods = parse_analog(soup)

        path = img.replace("/", '.')
        urllib.request.urlretrieve("{}{}".format(SKLAD_BASE_URL, img),
                                   "img/main{}".format(path))

        # final product
        final_prod = {
            'name': name,
            'type': prod_type,
            'brand': brand,
            'price': price,
            'chars': characteristics,
            'desc': desc,
            'img_original': "{}{}".format(SKLAD_BASE_URL, img),
            'analog': analog_prods,
            'url': url,
            'category': prefix
        }

        task = {'name': name}
        double = dbc.find_one(task)

        if double is None:
            dbc.insert_one(final_prod)
        else:
            pass

        print("\t", name)

        return True


async def extract_page(session, url, page_number, dbc, prefix):

    """ Products list extract """

    url = url % page_number
    print(url)

    async with session.get(url) as resp:
        if resp.status != 200:
            return False
        txt = await resp.text()
        soup = bsoup(txt, "lxml")
        prods = soup.find_all('article', attrs={'class': 'block__product'})

        for product in prods:
            link = product.find('a', {'class': 'b_product--link __title'})
            if link:
                # check for double before request
                task = {'url': url}
                double = dbc.find_one(task)
                if double is not None:
                    print("DOUBLE: %s" % url)
                    return
                status = await extract_prod(session, link['href'], dbc, prefix)

        return status


async def main(url, dbc, prefix):

    """ Event loop enter point """

    async with aiohttp.ClientSession() as session:

        _i = 1
        http_success = True

        while http_success is True:
            http_success = await extract_page(session, url, _i, dbc, prefix)
            _i += 1
        return 'Done'


def init_process_event_loop(key, url):

    """ Initiate event loop in current proccess instance """

    dbc = MongoClient().sklgen.all
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(url, dbc, key))


if __name__ == '__main__':

    URLS = {
        '_diesel': '{}elektrostancii/dizelnye/page-%d/'.format(SKLAD_BASE_URL),
        '_gas': '{}elektrostancii/gazovye/page-%d/'.format(SKLAD_BASE_URL),
        '_benzin': '{}elektrostancii/benzinovye/page-%d'.format(SKLAD_BASE_URL),
        '_svarka': '{}elektrostancii/svarochnye/page-%d/'.format(SKLAD_BASE_URL)
        }

    i = 1
    RESULTS = []
    with Pool(4) as pool:
        for _key in URLS:
            data = (_key, URLS[_key])
            result = pool.apply_async(init_process_event_loop, data)
            RESULTS.append(result)
            i += 1
        HOLD = [result.wait() for result in RESULTS]
