from django.conf import settings
from django.http import HttpResponse

from twilio.util import RequestValidator
from functools import wraps

import base64
import uuid

def validate_twilio(func):
    @wraps(func)
    def dec(request, *args, **kwargs):
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
        data = dict()
        for k, v in request.REQUEST.items():
            data[k] = v
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        if validator.validate(settings.TWILIO_URL, data, signature):
            return func(request, *args, **kwargs)
        else:
            return HttpResponse(status=401)
        
    return dec

def uid_gen():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]

