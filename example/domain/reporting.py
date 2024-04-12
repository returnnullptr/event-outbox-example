from __future__ import annotations

from abc import ABC, abstractmethod


class EventListener(ABC):
    @abstractmethod
    def diagnostic_report_generated(self, diagnostic_report: DiagnosticReport) -> None:
        pass


class Client:
    def __init__(self, client_id: str) -> None:
        self.id = client_id

    def read_diagnostic_report(
        self, diagnostic_report: DiagnosticReport
    ) -> DiagnosticReport:
        if self.id != diagnostic_report.client.id:
            raise AccessDeniedError
        return diagnostic_report


class DiagnosticReport:
    @staticmethod
    def generate(client: Client, listener: EventListener) -> DiagnosticReport:
        diagnostic_report = DiagnosticReport(client)
        listener.diagnostic_report_generated(diagnostic_report)
        return diagnostic_report

    def __init__(self, client: Client) -> None:
        self.client = client


class AccessDeniedError(Exception):
    pass
