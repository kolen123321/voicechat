import os
from django.http.response import HttpResponseNotFound
import mimetypes
from django.http import HttpResponse

def get_response(file):
    rb = open(file, "rb").read()
    response = HttpResponse(rb, content_type=mimetypes.types_map['.' + file.split(".")[-1]].lower())
    print(response)
    return response

from . import settings

def static(req):
    path = settings.MEDIA_ROOT / req.environ['PATH_INFO'].replace(settings.MEDIA_URL, "")
    if not os.path.exists(path):
        return HttpResponseNotFound("Not found")
    return get_response(str(path))



