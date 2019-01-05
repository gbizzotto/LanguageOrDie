
import datetime
import unicodedata
import sys
from py2casefold import casefold

APP_NAME = 'NO_APP_NAME'

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", casefold(text))

def log(*argv):
    sys.stdout.write(unicode(datetime.datetime.now()))
    sys.stdout.write(' ['+unicode(APP_NAME)+']')
    for arg in argv:
        sys.stdout.write(u' ' + unicode(arg))
    sys.stdout.write(unicode('\n'))
    
def starts_with_number_and_dot(line):
    pos = line.find('.')
    if pos is -1:
        return None
    s = line[:pos]
    if not s.isdigit():
        return None
    return int(s)
