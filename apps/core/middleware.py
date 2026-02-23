from django.http.multipartparser import MultiPartParser

class PutPatchMultipartMiddleware:
    """
    Middleware to parse multipart form data for PUT and PATCH requests.
    Django only populates request.POST and request.FILES for POST requests by default.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ['PUT', 'PATCH'] and request.content_type.startswith('multipart/form-data'):
            if not request.POST and not request.FILES:
                try:
                    parser = MultiPartParser(request.META, request.environ['wsgi.input'], request.upload_handlers, request.encoding)
                    post, files = parser.parse()
                    print(f"DEBUG Middleware: Parsed {len(post)} post fields and {len(files)} files. Keys: {list(files.keys())}")
                    request._post = post
                    request._files = files
                except Exception as e:
                    print(f"ERROR Middleware: {str(e)}")
        
        return self.get_response(request)
