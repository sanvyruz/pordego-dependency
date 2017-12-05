from requests import HTTPError
from requests.auth import HTTPBasicAuth
from six.moves import configparser

try:
    auth = HTTPBasicAuth()
except HTTPError:
    pass
