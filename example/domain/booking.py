from __future__ import annotations

from abc import ABC, abstractmethod


class EventListener(ABC):
    @abstractmethod
    def order_created(self, order: Order) -> None:
        pass


class Client:
    def __init__(self, client_id: str) -> None:
        self.id = client_id

    def create_order(self, order_id: str, listener: EventListener) -> Order:
        order = Order(order_id=order_id, client=self)
        listener.order_created(order)
        return order


class Order:
    def __init__(self, order_id: str, client: Client) -> None:
        self.id = order_id
        self.client = client
