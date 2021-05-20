from django.template.library import Library
import datetime
register = Library()

@register.filter(expects_localtime=True)
def convert_date(value):
    return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')