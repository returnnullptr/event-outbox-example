import asyncio
from typing import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from example.domain.rapid_testing import RapidTestResult
from example.infrastructure.http_server import config, create_app


@pytest.fixture(scope="session", autouse=True)
def set_test_environment() -> None:
    config.configure(FORCE_ENV_FOR_DYNACONF="test")


@pytest.fixture
async def http_client() -> AsyncIterator[AsyncClient]:
    async with LifespanManager(create_app()) as manager:
        async with AsyncClient(
            base_url="http://test",
            transport=ASGITransport(
                app=manager.app  # type: ignore[arg-type]
            ),
        ) as http_client:
            yield http_client


async def test_main_flow(http_client: AsyncClient) -> None:
    client_id = "yura"

    response = await http_client.post(f"/client/{client_id}/orders")
    assert response.status_code == 200
    order = response.json()
    order_id = order["id"]
    assert order["client_id"] == client_id

    await asyncio.sleep(1)

    response = await http_client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json() == order

    response = await http_client.post(
        f"/orders/{order_id}/sample",
        json={"sample_id": "R31337"},
    )
    assert response.status_code == 200

    await asyncio.sleep(1)

    response = await http_client.post(
        f"/orders/{order_id}/result",
        json={"result": RapidTestResult.POSITIVE},
    )
    assert response.status_code == 200

    await asyncio.sleep(1)

    response = await http_client.get(f"/client/{client_id}/orders/{order_id}/report")
    assert response.status_code == 200
