class NoCacheHTMLMiddleware:
    """Force HTML responses to revalidate so template/CSS changes appear immediately.

    Django does not set Cache-Control on HTML responses by default, which lets
    browsers heuristically cache a stale page (e.g. after a deploy).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get('Content-Type', '')
        if content_type.startswith('text/html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
