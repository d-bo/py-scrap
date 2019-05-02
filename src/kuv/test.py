import pytest
import asyncio
from . import step1


KUV_BASE_URL = os.getenv('KUV_BASE_URL')


def test_url():
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(step1.main('{}/catalog/9775/').format(KUV_BASE_URL))
