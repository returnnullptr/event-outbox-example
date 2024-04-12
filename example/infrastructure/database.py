from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorDatabase

from example.domain import booking, rapid_testing, reporting


class Database:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        session: AsyncIOMotorClientSession,
    ) -> None:
        self.db = db
        self.session = session

    async def insert_order(self, order: booking.Order) -> None:
        await self.db["orders"].insert_one(
            {"_id": ObjectId(order.id), "client": order.client.id},
            session=self.session,
        )

    async def get_order(self, order_id: ObjectId) -> booking.Order:
        document = await self.db["orders"].find_one(
            {"_id": order_id},
            session=self.session,
        )
        if not document:
            raise NotImplementedError
        return booking.Order(
            order_id=str(document["_id"]),
            client=booking.Client(
                client_id=document["client"],
            ),
        )

    async def insert_rapid_test(self, rapid_test: rapid_testing.RapidTest) -> None:
        await self.db["rapid_tests"].insert_one(
            {
                "order_id": ObjectId(rapid_test.order.id),
                "client_id": rapid_test.order.client_id,
            },
            session=self.session,
        )

    async def update_rapid_test(self, rapid_test: rapid_testing.RapidTest) -> None:
        await self.db["rapid_tests"].update_one(
            {"order_id": ObjectId(rapid_test.order.id)},
            {
                "$set": {
                    "result": str(rapid_test.result) if rapid_test.result else None,
                    "sample_id": (
                        str(rapid_test.sample.id) if rapid_test.sample else None
                    ),
                }
            },
            session=self.session,
        )

    async def get_rapid_test_by_order_id(
        self, order_id: ObjectId
    ) -> rapid_testing.RapidTest:
        document = await self.db["rapid_tests"].find_one(
            {"order_id": order_id},
            session=self.session,
        )
        if not document:
            raise NotImplementedError
        return rapid_testing.RapidTest(
            order=rapid_testing.Order(
                order_id=str(document["order_id"]),
                client_id=str(document["client_id"]),
            ),
            result=(
                rapid_testing.RapidTestResult(document["result"])
                if document.get("result")
                else None
            ),
            sample=(
                rapid_testing.Sample(sample_id=document["sample_id"])
                if document.get("sample_id")
                else None
            ),
        )

    async def insert_diagnostic_report(
        self,
        diagnostic_report: reporting.DiagnosticReport,
        order_id: ObjectId,
    ) -> None:
        await self.db["diagnostic_reports"].insert_one(
            {
                "order_id": order_id,
                "client_id": diagnostic_report.client.id,
            },
            session=self.session,
        )

    async def get_diagnostic_report_by_order_id(
        self,
        order_id: ObjectId,
    ) -> reporting.DiagnosticReport:
        document = await self.db["diagnostic_reports"].find_one(
            {"order_id": order_id},
            session=self.session,
        )
        if not document:
            raise NotImplementedError
        return reporting.DiagnosticReport(
            client=reporting.Client(
                client_id=document["client_id"],
            )
        )
