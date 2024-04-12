import logging
from typing import Literal

from bson import ObjectId
from event_outbox import Event, EventListener, EventOutbox
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession

from example.domain import booking, rapid_testing, reporting
from example.domain.booking import Order
from example.domain.rapid_testing import RapidTest, RapidTestResult, Sample
from example.domain.reporting import DiagnosticReport
from example.infrastructure.database import Database


class OrderCreated(Event):
    topic: Literal["booking"] = "booking"
    content_schema: Literal["OrderCreated"] = "OrderCreated"
    order_id: str
    client_id: str


class ResultChecked(Event):
    topic: Literal["rapid_testing"] = "rapid_testing"
    content_schema: Literal["ResultChecked"] = "ResultChecked"
    order_id: str
    client_id: str


class RapidTestScheduled(Event):
    topic: Literal["rapid_testing"] = "rapid_testing"
    content_schema: Literal["RapidTestScheduled"] = "RapidTestScheduled"


class DiagnosticReportGenerated(Event):
    topic: Literal["reporting"] = "reporting"
    content_schema: Literal["DiagnosticReportGenerated"] = "DiagnosticReportGenerated"


class SampleCollected(Event):
    topic: Literal["rapid_testing"] = "rapid_testing"
    content_schema: Literal["SampleCollected"] = "SampleCollected"


class BookingEventListener(booking.EventListener):
    def __init__(self, listener: EventListener) -> None:
        self.listener = listener

    def order_created(self, order: Order) -> None:
        self.listener.event_occurred(
            OrderCreated(order_id=order.id, client_id=order.client.id)
        )


class RapidTestingEventListener(rapid_testing.EventListener):
    def __init__(self, listener: EventListener) -> None:
        self.listener = listener

    def rapid_test_scheduled(self, rapid_test: RapidTest) -> None:
        self.listener.event_occurred(RapidTestScheduled())

    def sample_collected(self, rapid_test: RapidTest, sample: Sample) -> None:
        self.listener.event_occurred(SampleCollected())

    def result_checked(self, rapid_test: RapidTest, result: RapidTestResult) -> None:
        self.listener.event_occurred(
            ResultChecked(
                order_id=rapid_test.order.id,
                client_id=rapid_test.order.client_id,
            )
        )


class ReportingEventListener(reporting.EventListener):
    def __init__(self, listener: EventListener) -> None:
        self.listener = listener

    def diagnostic_report_generated(self, diagnostic_report: DiagnosticReport) -> None:
        self.listener.event_occurred(DiagnosticReportGenerated())


async def handle_event(
    event: Event,
    session: AsyncIOMotorClientSession,
    mongo_client: AsyncIOMotorClient,
    outbox: EventOutbox,
) -> None:
    if (event.topic, event.content_schema) == ("booking", "OrderCreated"):
        order_created = OrderCreated.model_validate(event, from_attributes=True)
        database = Database(mongo_client.get_default_database(), session)
        async with outbox.event_listener(session) as listener:
            rapid_test = RapidTest.schedule(
                rapid_testing.Order(
                    order_id=order_created.order_id,
                    client_id=order_created.client_id,
                ),
                RapidTestingEventListener(listener),
            )
            await database.insert_rapid_test(rapid_test)

    if (event.topic, event.content_schema) == ("rapid_testing", "ResultChecked"):
        result_checked = ResultChecked.model_validate(event, from_attributes=True)
        database = Database(mongo_client.get_default_database(), session)
        async with outbox.event_listener(session) as listener:
            diagnostic_report = DiagnosticReport.generate(
                reporting.Client(client_id=result_checked.client_id),
                ReportingEventListener(listener),
            )
            await database.insert_diagnostic_report(
                diagnostic_report,
                ObjectId(result_checked.order_id),
            )

    logging.getLogger(__name__).info("Event handled: %s", event)
