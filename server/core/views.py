import json
import logging

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(name=__name__)


@csrf_exempt
def base_view(request: HttpRequest):
    logger.warning(
        json.loads(
            request.body.decode()
        )
    )
    return HttpResponse(status=200)
