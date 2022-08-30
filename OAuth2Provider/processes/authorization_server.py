import json
import sys
import typing as t
from authlib.oauth2 import (
    OAuth2Request,
)
from .authorization_server_base import AuthorizationServer as _AuthorizationServer
from authlib.oauth2.rfc6750 import BearerToken
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata
from authlib.common.security import generate_token
from .pyramid_request import create_oauth_request
from pyramid.response import Response


class ImportStringError(ImportError):
    """werkzeug Provides information about a failed :func:`import_string` attempt."""

    #: String in dotted notation that failed to be imported.
    import_name: str
    #: Wrapped exception.
    exception: BaseException

    def __init__(self, import_name: str, exception: BaseException) -> None:
        self.import_name = import_name
        self.exception = exception
        msg = import_name
        name = ""
        tracked = []
        for part in import_name.replace(":", ".").split("."):
            name = f"{name}.{part}" if name else part
            imported = import_string(name, silent=True)
            if imported:
                tracked.append((name, getattr(imported, "__file__", None)))
            else:
                track = [f"- {n!r} found in {i!r}." for n, i in tracked]
                track.append(f"- {name!r} not found.")
                track_str = "\n".join(track)
                msg = (
                    f"import_string() failed for {import_name!r}. Possible reasons"
                    f" are:\n\n"
                    "- missing __init__.py in a package;\n"
                    "- package or module path not included in sys.path;\n"
                    "- duplicated package or module name taking precedence in"
                    " sys.path;\n"
                    "- missing module, class, function or variable;\n\n"
                    f"Debugged import:\n\n{track_str}\n\n"
                    f"Original exception:\n\n{type(exception).__name__}: {exception}"
                )
                break

        super().__init__(msg)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}({self.import_name!r}, {self.exception!r})>"


def import_string(import_name: str, silent: bool = False) -> t.Any:
    """werkzeug: Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).
    If `silent` is True the return value will be `None` if the import fails.
    :param import_name: the dotted name for the object to import.
    :param silent: if set to `True` import errors are ignored and
                   `None` is returned instead.
    :return: imported object
    """
    import_name = import_name.replace(":", ".")
    try:
        try:
            __import__(import_name)
        except ImportError:
            if "." not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit(".", 1)
        module = __import__(module_name, globals(), locals(), [obj_name])
        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e) from None

    except ImportError as e:
        if not silent:
            raise ImportStringError(import_name, e).with_traceback(
                sys.exc_info()[2]
            ) from None

    return None


class AuthorizationServer(_AuthorizationServer):
    def create_json_request(self, request):
        pass

    metadata_class = AuthorizationServerMetadata

    def __init__(self, query_client=None, save_token=None):
        super(AuthorizationServer, self).__init__(
            query_client=query_client,
            save_token=save_token,
        )
        self.generate_token = self.create_bearer_token_generator()

    def create_oauth2_request(self, request):
        return create_oauth_request(request, OAuth2Request)

    def handle_response(self, status_code, payload, headers):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        return Response(payload, status=status_code, headers=headers)

    def create_bearer_token_generator(self):
        """Default method to create BearerToken generator."""
        access_token_generator = create_token_generator(True, 42)

        # conf = self.config.get('refresh_token_generator', False)
        refresh_token_generator = create_token_generator(True, 48)

        # conf = self.config.get('token_expires_in')
        expires_generator = create_token_expires_in_generator(None)

        return BearerToken(
            access_token_generator=access_token_generator,
            refresh_token_generator=refresh_token_generator,
            expires_generator=expires_generator,
        )


def create_token_expires_in_generator(expires_in_conf=None):
    data = {}
    data.update(BearerToken.GRANT_TYPES_EXPIRES_IN)
    if expires_in_conf:
        data.update(expires_in_conf)

    def expires_in(client, grant_type):
        return data.get(grant_type, BearerToken.DEFAULT_EXPIRES_IN)

    return expires_in


def create_token_generator(token_generator_conf, length=42):
    if callable(token_generator_conf):
        return token_generator_conf

    if isinstance(token_generator_conf, str):
        return import_string(token_generator_conf)
    elif token_generator_conf is True:

        def token_generator(*args, **kwargs):
            return generate_token(length)

        return token_generator
