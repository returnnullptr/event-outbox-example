import logging.config
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncIterator

import dynaconf
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from bson import ObjectId
from event_outbox import EventOutbox
from fastapi import APIRouter, Depends, FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from example.domain import booking, reporting
from example.domain.rapid_testing import Collector, RapidTestResult, Sample
from example.infrastructure.database import Database
from example.infrastructure.message_queue import (
    BookingEventListener,
    RapidTestingEventListener,
    handle_event,
)

settings_path = Path(__file__).parent.parent.parent / "settings"
config = dynaconf.Dynaconf(
    environments=True,
    settings_files=[
        settings_path / "default.toml",
        settings_path / "test.toml",
        settings_path / "local.toml",
    ],
    load_dotenv=True,
    merge_enabled=True,
)


def get_mongo_client() -> AsyncIOMotorClient:
    raise NotImplementedError


def get_event_outbox() -> EventOutbox:
    raise NotImplementedError


MongoClientDependency = Annotated[AsyncIOMotorClient, Depends(get_mongo_client)]
EventOutboxDependency = Annotated[EventOutbox, Depends(get_event_outbox)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        mongo_client = AsyncIOMotorClient(
            config.mongo.connection_string,
            tz_aware=True,
        )
        stack.callback(mongo_client.close)
        kafka_producer = await stack.enter_async_context(
            # TODO: Configure broker:
            #   min.insync.replicas = len(replicas) - 1
            AIOKafkaProducer(
                bootstrap_servers=config.kafka.bootstrap_servers,
                enable_idempotence=True,
                acks="all",
            )
        )
        kafka_consumer = await stack.enter_async_context(
            AIOKafkaConsumer(
                *("booking", "rapid_testing", "reporting"),
                bootstrap_servers=config.kafka.bootstrap_servers,
                group_id="monolith",
                enable_auto_commit=False,
                auto_offset_reset="earliest",
            )
        )
        event_outbox = EventOutbox(mongo_client, kafka_producer, kafka_consumer)
        await event_outbox.create_indexes()
        await stack.enter_async_context(
            event_outbox.run_event_handler(
                lambda event, session: handle_event(
                    event,
                    session,
                    mongo_client,
                    event_outbox,
                )
            )
        )
        app.dependency_overrides = {
            get_mongo_client: lambda: mongo_client,
            get_event_outbox: lambda: event_outbox,
        }
        logging.config.dictConfig(config.logging.to_dict())
        yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


class CollectSampleRequest(BaseModel):
    sample_id: str


class CheckResultRequest(BaseModel):
    result: RapidTestResult


class OrderResource(BaseModel):
    id: str
    client_id: str


class EmptyResponse(BaseModel):
    pass


router = APIRouter()


@router.post("/client/{client_id}/orders")
async def create_order(
    client_id: str, mongo_client: MongoClientDependency, outbox: EventOutboxDependency
) -> OrderResource:
    client = booking.Client(client_id)

    async with await mongo_client.start_session() as session:
        database = Database(mongo_client.get_default_database(), session)
        async with outbox.event_listener(session) as listener:
            order = client.create_order(str(ObjectId()), BookingEventListener(listener))
            await database.insert_order(order)

    return OrderResource(id=order.id, client_id=order.client.id)


@router.get("/client/{client_id}/orders/{order_id}/report")
async def get_report(
    order_id: str, client_id: str, mongo_client: MongoClientDependency
) -> EmptyResponse:
    client = reporting.Client(client_id)

    async with await mongo_client.start_session() as session:
        database = Database(mongo_client.get_default_database(), session)
        diagnostic_report = await database.get_diagnostic_report_by_order_id(
            ObjectId(order_id)
        )
        client.read_diagnostic_report(diagnostic_report)

    return EmptyResponse()


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str, mongo_client: MongoClientDependency
) -> OrderResource:
    async with await mongo_client.start_session() as session:
        database = Database(mongo_client.get_default_database(), session)
        order = await database.get_order(ObjectId(order_id))

    return OrderResource(
        id=order_id,
        client_id=order.client.id,
    )


@router.post("/orders/{order_id}/sample")
async def collect_sample(
    order_id: str,
    request: CollectSampleRequest,
    mongo_client: MongoClientDependency,
    outbox: EventOutboxDependency,
) -> EmptyResponse:
    collector = Collector()

    async with await mongo_client.start_session() as session:
        database = Database(mongo_client.get_default_database(), session)
        rapid_test = await database.get_rapid_test_by_order_id(ObjectId(order_id))
        async with outbox.event_listener(session) as listener:
            collector.collect_sample(
                rapid_test,
                Sample(sample_id=request.sample_id),
                RapidTestingEventListener(listener),
            )
            await database.update_rapid_test(rapid_test)

    return EmptyResponse()


@router.post("/orders/{order_id}/result")
async def check_result(
    order_id: str,
    request: CheckResultRequest,
    mongo_client: MongoClientDependency,
    outbox: EventOutboxDependency,
) -> EmptyResponse:
    collector = Collector()

    async with await mongo_client.start_session() as session:
        database = Database(mongo_client.get_default_database(), session)
        rapid_test = await database.get_rapid_test_by_order_id(ObjectId(order_id))
        async with outbox.event_listener(session) as listener:
            collector.check_result(
                rapid_test,
                request.result,
                RapidTestingEventListener(listener),
            )
            await database.update_rapid_test(rapid_test)

    return EmptyResponse()
