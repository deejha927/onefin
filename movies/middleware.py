from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin


class RequestCounterMiddleware(MiddlewareMixin):
    """
    Middleware to count and store the number of incoming requests in the cache.

    This middleware increments a request count stored in Redis cache for each incoming request.
    The request count can be accessed in views via `request.custom_request_count`.
    """

    def process_request(self, request):
        if not cache.get('request_count'):
            cache.set('request_count', 0, None)
        request_count = cache.incr('request_count')
        request.custom_request_count = request_count
