# Event Outbox Example

## Bounded Contexts

### Booking

![Booking bounded context](docs/bounded-contexts/booking.png)

### Rapid testing

![Rapid testing bounded context.png](docs/bounded-contexts/rapid-testing.png)

### Reporting

![Reporting bounded context.png](docs/bounded-contexts/reporting.png)

## Installation

With [poetry](https://python-poetry.org/):

```bash
poetry install
```

## Running

```bash
poetry run uvicorn example.infrastructure.http_server:create_app --factory
```

## Development

```bash
bash cleanup.sh
```
