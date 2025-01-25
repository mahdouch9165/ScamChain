import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    wait_exponential,
    retry_if_exception_type,
)

def retryable_request_fixed(
    method,
    url,
    attempts=3,
    wait_seconds=2,
    **kwargs
):
    """
    Make a request with a FIXED wait time between attempts.
      - attempts: total number of attempts before giving up
      - wait_seconds: the wait duration in seconds between tries
      - **kwargs: additional arguments passed to requests.request()
    """
    @retry(
        stop=stop_after_attempt(attempts),
        wait=wait_fixed(wait_seconds),
        reraise=True,
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _do_request():
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()        
        return response

    return _do_request()

def retryable_request_fixed_basescan(
    method,
    url,
    attempts=3,
    wait_seconds=2,
    **kwargs
):
    """
    Make a request with a FIXED wait time between attempts.
      - attempts: total number of attempts before giving up
      - wait_seconds: the wait duration in seconds between tries
      - **kwargs: additional arguments passed to requests.request()
    """
    @retry(
        stop=stop_after_attempt(attempts),
        wait=wait_fixed(wait_seconds),
        reraise=True,
        retry=retry_if_exception_type((requests.exceptions.RequestException, ValueError)),
    )
    def _do_request():
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        data = response.json()
        if data["result"] == "Max calls per sec rate limit reached (5/sec)":
            # rate limit error
            raise ValueError("Rate limit error")
        elif data["status"] == '0':
            # request failed
            raise ValueError("Request failed")
        return response

    return _do_request()

def retryable_request_exponential(
    method,
    url,
    attempts=3,
    multiplier=1,
    min_wait=1,
    max_wait=60,
    **kwargs
):
    """
    Make a request with an EXPONENTIAL wait time between attempts.
      - attempts: total number of attempts before giving up
      - multiplier: base multiplier for exponential backoff
      - min_wait: minimum wait time in seconds
      - max_wait: maximum wait time in seconds
      - **kwargs: additional arguments passed to requests.request()
    """
    @retry(
        stop=stop_after_attempt(attempts),
        # wait_exponential automatically doubles wait time each retry
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        reraise=True,
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _do_request():
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    return _do_request()
