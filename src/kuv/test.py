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
    await step2.main(group_id=8964, base_group_id=8964,
                     position=1, dbi=False, dbp=False)

@pytest.mark.asyncio
async def test_step3():
    assert False == await step3.main(url='/catalog/9673/product-60255/', position=1)
