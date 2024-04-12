from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum


class EventListener(ABC):
    @abstractmethod
    def rapid_test_scheduled(self, rapid_test: RapidTest) -> None:
        pass

    @abstractmethod
    def sample_collected(self, rapid_test: RapidTest, sample: Sample) -> None:
        pass

    @abstractmethod
    def result_checked(self, rapid_test: RapidTest, result: RapidTestResult) -> None:
        pass


class Collector:
    def collect_sample(
        self, rapid_test: RapidTest, sample: Sample, listener: EventListener
    ) -> None:
        # TODO: Check access
        return rapid_test.collect_sample(sample, listener)

    def check_result(
        self, rapid_test: RapidTest, result: RapidTestResult, listener: EventListener
    ) -> None:
        # TODO: Check access
        return rapid_test.check_result(result, listener)


class RapidTest:
    @staticmethod
    def schedule(order: Order, listener: EventListener) -> RapidTest:
        rapid_test = RapidTest(order=order)
        listener.rapid_test_scheduled(rapid_test)
        return rapid_test

    def __init__(
        self,
        order: Order,
        result: RapidTestResult | None = None,
        sample: Sample | None = None,
    ) -> None:
        self.order = order
        self.result = result
        self.sample = sample

    def collect_sample(self, sample: Sample, listener: EventListener) -> None:
        self.sample = sample
        listener.sample_collected(self, sample)

    def check_result(self, result: RapidTestResult, listener: EventListener) -> None:
        self.result = result
        listener.result_checked(self, result)


class Order:
    def __init__(self, order_id: str, client_id: str) -> None:
        self.id = order_id
        self.client_id = client_id


class RapidTestResult(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    INVALID = "invalid"


class Sample:
    def __init__(self, sample_id: str) -> None:
        self.id = sample_id
