import os
import pytest
import asyncio
import step1
import step2
import step3
import pytest


KUV_BASE_URL = os.getenv('KUV_BASE_URL')


@pytest.mark.asyncio
async def test_step1():
    assert(await step1.main('{}/catalog/9775/'.format(KUV_BASE_URL)))

@pytest.mark.asyncio
async def test_step2():
    res = await step2.main(group_id=8964, base_group_id=8964,
                           position=1, dbi=False, dbp=False)
    assert(isinstance(res, list))

@pytest.mark.asyncio
async def test_step3():
    res = await step3.main(url='/catalog/9673/product-60255/', position=1)
    # TODO: res assert
