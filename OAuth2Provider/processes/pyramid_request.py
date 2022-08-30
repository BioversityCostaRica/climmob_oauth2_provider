from formencode.variabledecode import variable_decode


def create_oauth_request(request, request_cls, use_json=False):
    if isinstance(request, request_cls):
        return request

    if request.method == "POST":
        if use_json:
            body = request.get_json()
        else:
            body = variable_decode(request.POST)
    else:
        body = None

    url = request.url
    return request_cls(request.method, url, body, request.headers)
