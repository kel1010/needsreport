from django.conf import settings
from django.http import HttpResponse

from twilio.util import RequestValidator
from functools import wraps

def validate_twilio(func):
    @wraps(func)
    def dec(request, *args, **kwargs):
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
        data = dict()
        for k, v in request.POST.items():
            data[k] = v
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        if validator.validate(settings.TWILIO_URL, data, signature):
            return func(request, *args, **kwargs)
        else:
            return HttpResponse(status=401)
        
    return dec
