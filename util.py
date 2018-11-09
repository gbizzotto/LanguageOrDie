
import unicodedata
from py2casefold import casefold

def normalize_caseless(text):
    return unicodedata.normalize("NFKD", casefold(text))