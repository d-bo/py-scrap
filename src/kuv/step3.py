# -*- coding: utf-8 -*-
""" Fetch all parsed product pages """

import os
import asyncio
import urllib.error
import urllib.parse
import urllib.request
from multiprocessing import Pool
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup as bsoup


KUV_BASE_URL = os.getenv('KUV_BASE_URL')
KUV_REPLACE_URL = os.getenv('KUV_REPLACE_URL')


def parse_props(soup):

    """ Extract product properties """

    chars = []
    props = soup.find('div', {'class': 'info-block__table hidden'})
    if props:
        trs = props.find_all('tr')
        if trs:
            for tr_el in trs:
                tds = tr_el.find_all('td')
                if tds:
                    prop = []
                    for td_el in tds:
                        prop.append(td_el.text)
                    if prop:
                        chars.append({prop[0]: prop[1]})
    return chars


def parse_brand(soup):

    """ Extract brand """

    brand = soup.find('div', {'class': 'product-header__brand-title'})
    if brand:
        link = brand.find('a')
        if link:
            brand = link.text
    return brand


async def parse(resp, dbc, url):

    """ Extract product additional data """

    soup = bsoup(resp.text, "lxml")

    imgs = []
    chars = []
    suggested = []
    desc = ''
    brand = ''

    # brand
    items = soup.find_all('img',
                          {'class': 'product-photo__controls-image'})
    for _item in items:
        path = _item['src'].replace(KUV_REPLACE_URL, '')
        path = path.replace("/", '.')
        path = "kuv-img/main%s" % path
        print(path)
        urllib.request.urlretrieve("{}{}".format(KUV_BASE_URL, _item['src'])
                                   .replace(KUV_REPLACE_URL, ''), path)
        imgs.append(path)

    chars = parse_props(soup)

    desc = soup.find('div', {'class': 'info-block__text'})
    if desc:
        desc = desc.text

    recommend = soup.find_all('a', {'class': 'snippet__photo-source'})
    if recommend:
        for rec in recommend:
            suggested.append(rec['href'])

    brand = parse_brand(soup)

    summary = {
        'images': imgs,
        'properties': chars,
        'suggested': suggested,
        'description': desc,
        'brand': brand
    }

    try:
        print(dbc.update({'url': url}, {"$set": summary}, upsert=True))
    except:  # noqa: E722 # pylint: disable=bare-except
        print("ERROR MONGO UPDATE")


async def main(**kwargs):

    """ Request product url """

    out = False
    dbp = MongoClient().kuv.not_paged
    dbc = MongoClient().kuv.products_1
    print('{}{}'.format(KUV_BASE_URL, kwargs['url']),
          "POSITION", kwargs['position'])
    try:
        response = requests.get('{}{}'.format(KUV_BASE_URL, kwargs['url']))
    except:  # noqa: E722 # pylint: disable=bare-except
        raise Exception("ERR REQUEST PROD")
        dbp.insert_one({'url': kwargs['url']})

    try:
        if response.status_code == 200:
            out = await parse(response, dbc, kwargs['url'])
        else:
            raise Exception('Status code either than 200: {}'
                            .format(response.status_code))
    except:
        pass

    return out


def evloop(product_url, counter):

    """ Init event loop """

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(url=product_url, position=counter))


if __name__ == '__main__':

    DB = MongoClient().kuv.products_1
    CURSOR = DB.find({"suggested": {"$exists": False}})
    RESULTS = []
    i = 1
    with Pool() as pool:
        for item in CURSOR:
            # Script can break
            # Change `i` position to start from
            if i > 0:
                if 'url' not in item:
                    continue
                data = (item['url'], i)
                result = pool.apply_async(evloop, data)
                RESULTS.append(result)
            i += 1
        HOLD = [result.wait() for result in RESULTS]
