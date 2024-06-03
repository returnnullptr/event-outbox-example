from unittest.mock import Mock, call

import pytest

from example.domain.reporting import (
    AccessDeniedError,
    Client,
    DiagnosticReport,
    EventListener,
)


@pytest.fixture
def listener() -> Mock:
    return Mock(spec=EventListener)


@pytest.fixture
def client() -> Client:
    return Client("client-1")


@pytest.fixture
def diagnostic_report(client: Client, listener: Mock) -> DiagnosticReport:
    return DiagnosticReport.generate(client, listener)


def test_generate_diagnostic_report(client: Client, listener: Mock) -> None:
    diagnostic_report = DiagnosticReport.generate(client, listener)

    assert diagnostic_report.client is client

    listener.assert_has_calls(
        [
            call.diagnostic_report_generated(diagnostic_report),
        ]
    )


def test_client_read_diagnostic_report(
    client: Client, diagnostic_report: DiagnosticReport
) -> None:
    result = client.read_diagnostic_report(diagnostic_report)

    assert result is diagnostic_report


def test_another_client_can_not_read_diagnostic_report(
    diagnostic_report: DiagnosticReport,
) -> None:
    another_client = Client("another-client")

    with pytest.raises(AccessDeniedError):
        another_client.read_diagnostic_report(diagnostic_report)
