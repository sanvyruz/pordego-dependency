from requests import HTTPError
from requests.auth import HTTPBasicAuth

try:
    auth = HTTPBasicAuth()
except HTTPError:
    pass
