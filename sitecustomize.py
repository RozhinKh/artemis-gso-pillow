"""sitecustomize for the GSO pillow-simd bundle.

Serves benchmark fixture images from ./images/ and adds a proper User-Agent
for any download that is not cached yet. Test scripts stay unmodified.
"""

import os
from urllib.parse import unquote, urlparse

import requests
from requests.models import Response

_IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
_orig_get = requests.get
_UA = "artemis-gso-pilot/1.0 (internal benchmarking)"


def _cached_get(url, *args, **kwargs):
    try:
        name = unquote(os.path.basename(urlparse(str(url)).path)) or "download.bin"
    except Exception:
        name = "download.bin"
    local = os.path.join(_IMAGES, name)
    if os.path.exists(local):
        r = Response()
        r.status_code = 200
        r.url = str(url)
        r.headers["Content-Type"] = "application/octet-stream"
        with open(local, "rb") as fh:
            r._content = fh.read()
        return r
    headers = dict(kwargs.get("headers") or {})
    headers.setdefault("User-Agent", _UA)
    kwargs["headers"] = headers
    r = _orig_get(url, *args, **kwargs)
    r.raise_for_status()
    os.makedirs(_IMAGES, exist_ok=True)
    with open(local, "wb") as fh:
        fh.write(r.content)
    return r


requests.get = _cached_get
