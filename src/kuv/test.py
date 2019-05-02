import pytest
import asyncio
from . import step1

def test_url():
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(step1.main('https://www.kuvalda.ru/catalog/9775/'))
