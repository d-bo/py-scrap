# -*- coding: utf-8 -*-
""" Step 2: get product ajax pages """

import os
import asyncio
from multiprocessing import Pool
import requests
from pymongo import MongoClient


KUV_BASE_URL = os.getenv('KUV_BASE_URL')


async def fetch(**kwargs):

    """ Fetch like cURL """

    cookies = {
        'v7_6_location_d': 'www',
        'v7_6_locationUnknown': '1',
        'kuvnew': '9d2slrbnftttefcbjco9lh2vl0',
        '_ga': 'GA1.2.131887699.1555932722',
        '_gid': 'GA1.2.939547448.1555932722',
        '_ym_uid': '1555932723284432972',
        '_ym_d': '1555932723',
        'catalogue-order': 'popularity',
        '_ym_isad': '1',
        'jv_enter_ts_HhpB18oYkg': '1556091590843',
        'jv_visits_count_HhpB18oYkg': '3',
        'jv_refer_HhpB18oYkg': 'https%3A%2F%2Fwww.google.com%2F',
        'jv_utm_HhpB18oYkg': '',
        'v7_6_location': 'msc',
        'v7_6_locationCity': '41',
        '_ym_visorc_962836': 'w',
        '_dc_gtm_UA-1849227-1': '1',
        '_gat_UA-1849227-1': '1',
        'jv_pages_count_HhpB18oYkg': '35',
    }

    headers = {
        'Origin': '{}'.format(KUV_BASE_URL),
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KH\
        TML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json, text/plain, */*',
        'Referer': '{}/catalog'.format(KUV_BASE_URL),
        'Connection': 'keep-alive',
    }

    _data = '{"filter_lists":{},"filter_ranges":{},"sort_order":"popularity",\
    "pagination":{"page":%d,"more":true},"summary":{"items_count":10000,\
    "filters":[]},"group_id":"%s","base_group_id":%s}' % (
        kwargs['page'], kwargs['group_id'], kwargs['base_group_id']
        )
    try:
        response = requests.post(
            '{}/_terminal/api/1.0/catalogue/filter/data/'.format(KUV_BASE_URL),
            headers=headers, cookies=cookies, data=_data)
        if response.status_code == 200:
            return response
        else:
            raise Exception('Error response status code: {}'
                            .format(response.status_code))
    except:  # noqa: E722 # pylint: disable=bare-except
        print("ERR REQUEST PROD")
        kwargs['dbp'].insert_one({'id': kwargs['group_id']})


async def parse(resp, dbi):

    """ Insert product item """

    inserted, passed = 0, 0
    for key, value in enumerate(resp['items']):
        key = key  # flake8 F841
        task = {'url': value['url']}
        try:
            double = dbi.find_one(task)
            if double is None:
                dbi.insert_one(value)
                inserted += 1
            else:
                passed += 1
        except:
            pass
    print("inserted: ", inserted, "passed: ", passed)
    return resp['items']


async def main(**kwargs):

    """ Paginate same data response strategy """

    page = 1
    previous = ''
    next_one = 'initial'
    parse_res = False
    while previous != next_one:
        resp = await fetch(group_id=kwargs['group_id'],
                           base_group_id=kwargs['base_group_id'],
                           page=page, dbp=kwargs['dbp'],
                           dbi=kwargs['dbi'])
        next_one = resp.text
        if previous == next_one:
            break
        print("PAGE", page, "MONGO CURSOR", kwargs['position'])
        parse_res = await parse(resp.json(), kwargs['dbi'])
        previous, next_one = next_one, ''
        page += 1
    return parse_res


def evloop(group_id, base_group_id, counter):

    """ Event loop init """

    dbp = MongoClient().kuv.not_paged
    dbi = MongoClient().kuv.products_1
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(group_id=group_id,
                                 base_group_id=base_group_id,
                                 position=counter, dbi=dbi, dbp=dbp))


if __name__ == '__main__':

    DB = MongoClient().kuv.group_ids_alter
    CURSOR = DB.find()
    if not CURSOR.count():
        raise Exception('No results. First run step1.')
    RESULTS = []
    i = 1
    with Pool() as pool:
        for item in CURSOR:
            if i > 0:
                data = (item['group'], item['base_group'], i)
                result = pool.apply_async(evloop, data)
                RESULTS.append(result)
            i += 1
        HOLD = [result.wait() for result in RESULTS]
