# Event Outbox Example

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
