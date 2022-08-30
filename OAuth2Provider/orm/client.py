import time
import logging
from sqlalchemy.exc import IntegrityError
import secrets
from OAuth2Provider.orm.OAuth2Provider import (
    OAuth2Client,
    OAuth2AuthorizationCode,
    OAuth2Token,
    OAOAuthUser,
)


# werkzeug
SALT_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def gen_salt(length: int) -> str:
    # werkzeug
    """Generate a random string of SALT_CHARS with specified ``length``."""
    if length <= 0:
        raise ValueError("Salt length must be positive")

    return "".join(secrets.choice(SALT_CHARS) for _ in range(length))


log = logging.getLogger("myproj1")


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


def get_clients(request, user_id):
    res = (
        request.dbsession.query(OAuth2Client)
        .filter(OAuth2Client.user_id == user_id)
        .all()
    )
    return res


def get_client_logo(request, client_id):
    res = (
        request.dbsession.query(OAuth2Client.client_logo_file)
        .filter(OAuth2Client.client_id == client_id)
        .first()
    )
    if res is not None:
        return res.client_logo_file
    return None


def get_client_name(request, client_id):
    res = (
        request.dbsession.query(OAuth2Client.client_name)
        .filter(OAuth2Client.client_id == client_id)
        .first()
    )
    if res is not None:
        return res.client_name
    return None


def update_client_logo(request, user_id, client_id, logo_data):
    _ = request.translate
    try:
        request.dbsession.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id
        ).filter(OAuth2Client.user_id == user_id).update(logo_data)
        return True, ""
    except Exception as e:
        request.dbsession.rollback()
        log.error("Unable to delete client {}. Error: {}".format(client_id, str(e)))
        return False, _("ClimMob was not able to delete the client")


def delete_client(request, user_id, client_id):
    _ = request.translate
    try:
        request.dbsession.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id
        ).filter(OAuth2Client.user_id == user_id).delete()
        request.dbsession.query(OAuth2AuthorizationCode).filter(
            OAuth2AuthorizationCode.client_id == client_id
        ).filter(OAuth2AuthorizationCode.user_id == user_id).delete()
        request.dbsession.query(OAuth2Token).filter(
            OAuth2Token.client_id == client_id
        ).filter(OAuth2Token.user_id == user_id).delete()
        return True, ""
    except Exception as e:
        request.dbsession.rollback()
        log.error("Unable to delete client {}. Error: {}".format(client_id, str(e)))
        return False, _("ClimMob was not able to delete the client")


def client_uri_exist(request, client_ui):
    res = (
        request.dbsession.query(OAuth2Client.id)
        .filter(OAuth2Client.client_uri == client_ui)
        .count()
    )
    if res == 0:
        return False
    else:
        return True


def register_client(request, data, user_id):
    _ = request.translate
    client_id = gen_salt(24)
    client = OAuth2Client(
        client_id,
        gen_salt(48),
        int(time.time()),
        data["client_uri"],
        data["client_name"],
        data["client_logo_file"],
        data["client_logo_mimetype"],
        user_id,
    )

    client_metadata = {
        "client_name": data["client_name"],
        "client_uri": data["client_uri"],
        "grant_types": split_by_crlf(data["grant_type"]),
        "redirect_uris": split_by_crlf(data["redirect_uri"]),
        "response_types": split_by_crlf(data["response_type"]),
        "scope": data["scope"],
        "token_endpoint_auth_method": data["token_endpoint_auth_method"],
    }
    client.set_client_metadata(client_metadata)
    try:
        request.dbsession.add(client)
        request.dbsession.flush()
        return True, client_id
    except IntegrityError:
        request.dbsession.rollback()
        log.error(
            "Duplicated client {} with URI {}".format(
                data["client_name"], data["client_uri"]
            )
        )
        return False, _("Client URI already defined")
    except Exception as e:
        request.dbsession.rollback()
        log.error(
            "Error {} when inserting client {}".format(
                str(e), client_metadata["client_name"]
            )
        )
        return False, str(e)


def get_user_by_token(request, token):
    res_user = (
        request.dbsession.query(OAuth2Token)
        .filter(OAuth2Token.access_token == token)
        .first()
    )
    if res_user is not None:
        user_id = res_user.user_id
        res = (
            request.dbsession.query(OAOAuthUser)
            .filter(OAOAuthUser.user_name == user_id)
            .filter(OAOAuthUser.user_active == 1)
            .first()
        )
        return res
    return None
