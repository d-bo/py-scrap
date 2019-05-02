# -*- coding: utf-8 -*-
""" Step1: get product pages """

import os
import asyncio
import aiohttp
from pymongo import MongoClient
from bs4 import BeautifulSoup as bsoup


KUV_BASE_URL = os.getenv('KUV_BASE_URL')


async def parse_response(txt, url):

    """ Parse response """

    soup = bsoup(txt, "lxml")
    prods = soup.find_all('a', attrs={'class': 'promo-groups__item'})
    if prods:
        for product in prods:
            await main('{}{}'.format(KUV_BASE_URL, product['href']))
    items = soup.find_all('a', attrs={'class': 'snippet__photo-source'})
    if items:
        group = soup.find('catalog')
        if group:
            if group.has_attr('v-bind:base_group'):
                print("FROM <CATALOG>", group['v-bind:base_group'],
                      group['group'])
                task = {'group': group['group'],
                        'base_group': group['v-bind:base_group']}
            else:
                raise Exception('Can\'t find v-bind:base_group')
                """
                purl = url.split('/')[4]
                purl = ''.join(i for i in purl if i.isdigit())
                print("NOT PAGED", url)
                task = {'group': url, 'base_group': False, 'url': purl}
                """

        try:
            double = DB.find_one(task)
            if double is None:
                DB.insert_one(task)
        except:
            pass

    return task


async def main(url='{}/catalog'.format(KUV_BASE_URL)):

    """ Get product page recursive """

    print("URL: ", url)
    parsed = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    txt = await resp.text()
                    parsed = await parse_response(txt, url)
    except:  # noqa: E722 # pylint: disable=bare-except
        raise Exception('ERR AT: {}'.format(url))
        try:
            DBP.insert_one({'err': url})
        except:
            pass

    return parsed


if __name__ == '__main__':

    DB = MongoClient().kuv.group_ids_alter_1
    DBP = MongoClient().kuv.not_paged
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(main())
