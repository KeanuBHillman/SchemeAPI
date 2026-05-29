# SchemeAPI

A lightweight, typed HTTP API client built on top of `requests` with optional request decorators and Pydantic-based response validation.

---

## Features

- Simple wrapper around `requests`
- Global defaults for headers, params, and cookies
- Request decorators (middleware-style hooks)
- Automatic JSON validation using Pydantic `TypeAdapter`

---

## Installation

```bash
uv add git+https://github.com/<your-username>/<your-repo>.git
```

---

## Usage

### Create an API client

```python
from SchemeAPI import SchemeAPI

api = SchemeAPI(
    name="ExampleAPI",
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer TOKEN"},
)
```

### Request with validation

```python
from SchemeAPI import SchemeModel

class User(SchemeModel):
    id: int
    name: str

user = api.get("/user/1", type=User)
print(user["name"])
```

## Decorators

SchemeAPI uses decorators to handle logging, rate limiting, and retries.

### Built-in

The library includes the following built-in decorators:

- **`backoff`**: Retries a function call using exponential backoff with jitter.
- **`RateLimit`**: Enforces a maximum number of calls per second using a token bucket algorithm.

### Example

```python
from scheme_api import SchemeAPI, backoff, RateLimit

def log_requests(func):
    def wrapper(method, url, **kwargs):
        print(f"[SchemeAPI] {method} {url}")
        return func(method, url, **kwargs)
    return wrapper

api = SchemeAPI(
    name="ExampleAPI",
    base_url="https://api.example.com",
    decorators=[
        log_requests,
        RateLimit(tokens_per_second=3, capacity=5),
        backoff(max_attempts=5, base_delay=1.0)
    ],
)
```
