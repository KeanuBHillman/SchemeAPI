from typing import (
    Any,
    Callable,
    ParamSpec,
    TypeVar,
)

import requests
from pydantic import TypeAdapter

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")

Decorator = Callable[[Callable[P, R]], Callable[P, R]]


class SchemeAPI:
    """
    A lightweight HTTP API client wrapper around `requests` with:

    - Base URL handling
    - Global params/headers/cookies
    - Optional request decorators (middleware-style)
    - Pydantic-based response validation via TypeAdapter
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        *,
        decorators: list[Decorator] = [],
        params: dict[str, str] = {},
        cookies: dict[str, Any] = {},
        headers: dict[str, str] = {},
        timeout: float = 10,
    ) -> None:
        """
        Initialize the API client.

        Args:
            name: Human-readable identifier for the API client.
            base_url: Base URL used to prefix all request paths.
            decorators: Optional list of callables that wrap the request function
                (e.g., for logging, retries, auth injection).
            params: Default query parameters applied to all requests.
            cookies: Default cookies applied to all requests.
            headers: Default headers applied to all requests.
            timeout: Default request timeout in seconds.
        """
        self.name = name
        self.base_url = base_url

        self._decorators = decorators
        self.params = params
        self.headers = headers
        self.cookies = cookies
        self.timeout = timeout

        self._last_request_time = 0.0
        self._request = self._build_request()

    def _build_request(self) -> Callable[..., requests.Response]:
        """
        Construct the internal request function with applied decorators.

        Returns:
            A callable that behaves like `requests.request` but with:
            - merged default params/headers/cookies
            - optional decorator wrapping
        """

        def base_request(
            method: str,
            url: str,
            *,
            params: dict[str, str] = {},
            headers: dict[str, str] = {},
            cookies: dict[str, Any] = {},
            timeout: float | None = None,
            **kwargs,
        ) -> requests.Response:
            """
            Core HTTP request function used internally.

            This function merges global and per-request configuration,
            executes the request, and raises an exception for HTTP errors.

            Args:
                method: HTTP method (GET, POST, etc.).
                url: Fully qualified request URL.
                params: Query parameters for this request.
                headers: Request-specific headers.
                cookies: Request-specific cookies.
                timeout: Optional override for request timeout.
                **kwargs: Reserved for future extensions.

            Returns:
                The `requests.Response` object.

            Raises:
                requests.HTTPError: If the HTTP response contains an error status code.
            """
            response = requests.request(
                method,
                url,
                params=self.params | params,
                headers=self.headers | headers,
                cookies=self.cookies | cookies,
                timeout=timeout or self.timeout,
            )
            response.raise_for_status()
            return response

        # Apply decorators in reverse order (so first decorator wraps last)
        func = base_request
        for decorator in reversed(self._decorators):
            func = decorator(func)
        return func

    # ─────────────────────────────
    # Public API
    # ─────────────────────────────

    def request(
        self,
        method: str,
        path: str,
        type: Any,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        cookies: dict[str, Any] = {},
    ):
        """
        Send an HTTP request and validate the JSON response.

        Args:
            method: HTTP method to use (e.g., "GET", "POST").
            path: Endpoint path appended to the base URL.
            type: Pydantic-compatible type used for response validation.
            params: Query parameters for this request.
            headers: Request-specific headers.
            cookies: Request-specific cookies.

        Returns:
            Parsed and validated response object based on `type`.

        Raises:
            requests.HTTPError: If the request fails.
            pydantic.ValidationError: If response JSON does not match `type`.
        """
        response = self._request(
            method,
            self.base_url + path,
            params=params,
            headers=headers,
            cookies=cookies,
        )
        return TypeAdapter(type).validate_python(response.json())

    def get(
        self,
        path: str,
        type: Any,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        cookies: dict[str, Any] = {},
    ):
        """
        Perform a GET request with response validation.

        Args:
            path: Endpoint path appended to the base URL.
            type: Pydantic-compatible type used for response validation.
            params: Query parameters for this request.
            headers: Request-specific headers.
            cookies: Request-specific cookies.

        Returns:
            Parsed and validated response object based on `type`.
        """
        return self.request(
            "GET",
            path,
            type,
            params,
            headers,
            cookies,
        )

    def post(
        self,
        path: str,
        type: Any,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        cookies: dict[str, Any] = {},
    ):
        """
        Perform a POST request with response validation.

        Args:
            path: Endpoint path appended to the base URL.
            type: Pydantic-compatible type used for response validation.
            params: Query parameters for this request.
            headers: Request-specific headers.
            cookies: Request-specific cookies.

        Returns:
            Parsed and validated response object based on `type`.
        """
        return self.request(
            "POST",
            path,
            type,
            params,
            headers,
            cookies,
        )
