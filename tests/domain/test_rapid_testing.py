from unittest.mock import Mock, call

import pytest

from example.domain.rapid_testing import (
    Collector,
    EventListener,
    Order,
    RapidTest,
    RapidTestResult,
    Sample,
)


@pytest.fixture
def listener() -> Mock:
    return Mock(spec=EventListener)


@pytest.fixture
def client_id() -> str:
    return "client-1"


@pytest.fixture
def order_id() -> str:
    return "order-1"


@pytest.fixture
def order(order_id: str, client_id: str) -> Order:
    return Order(order_id, client_id)


@pytest.fixture
def collector() -> Collector:
    return Collector()


@pytest.fixture
def rapid_test(order: Order, listener: EventListener) -> RapidTest:
    return RapidTest.schedule(order, listener)


@pytest.fixture
def sample() -> Sample:
    return Sample("sample-1")


@pytest.fixture
def result() -> RapidTestResult:
    return RapidTestResult.NEGATIVE


def test_schedule_rapid_test(order: Order, listener: Mock) -> None:
    rapid_test = RapidTest.schedule(order, listener)

    assert rapid_test.order is order
    assert rapid_test.sample is None
    assert rapid_test.result is None

    listener.assert_has_calls(
        [
            call.rapid_test_scheduled(rapid_test),
        ]
    )


def test_collector_collect_sample(
    collector: Collector, rapid_test: RapidTest, sample: Sample, listener: Mock
) -> None:
    collector.collect_sample(rapid_test, sample, listener)

    assert rapid_test.sample is sample

    listener.assert_has_calls(
        [
            call.sample_collected(rapid_test, sample),
        ]
    )


def test_collector_check_result(
    collector: Collector, rapid_test: RapidTest, result: RapidTestResult, listener: Mock
) -> None:
    collector.check_result(rapid_test, result, listener)

    assert rapid_test.result is result

    listener.assert_has_calls(
        [
            call.result_checked(rapid_test, result),
        ]
    )
