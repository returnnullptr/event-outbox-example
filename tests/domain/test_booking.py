from unittest.mock import Mock, call

import pytest

from example.domain.booking import Client, EventListener


@pytest.fixture
def listener() -> Mock:
    return Mock(spec=EventListener)


@pytest.fixture
def client() -> Client:
    return Client("client-1")


def test_client_create_order(client: Client, listener: Mock) -> None:
    order_id = "order-1"
    order = client.create_order(order_id, listener)

    assert order.id is order_id
    assert order.client is client

    listener.assert_has_calls(
        [
            call.order_created(order),
        ]
    )
