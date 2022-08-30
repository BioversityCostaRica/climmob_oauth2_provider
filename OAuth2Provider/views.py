from climmob.plugins.utilities import publicView, privateView
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from urllib.parse import urlparse
import validators
from climmob.views.basic_views import login_view
import os
import imghdr
import mimetypes
import json
import xml.etree.cElementTree as eT
import logging
from OAuth2Provider.storage import store_file, get_stream, response_stream
from OAuth2Provider.orm.client import (
    client_uri_exist,
    register_client,
    get_clients,
    get_client_logo,
    delete_client,
    update_client_logo,
    get_user_by_token,
    get_client_name,
)
from OAuth2Provider.orm.oauth2 import authorization_function, config_oauth
import uuid
from climmob.config.auth import getUserData
from pyramid.response import Response


log = logging.getLogger("formshare")


class OAuthClientListView(privateView):
    def processView(self):
        return {
            "clients": get_clients(self.request, "bioversity"),
            "sectionActive": "OAuth2Provider",
            "Hello": "Carlos",
        }


def validate_url(url):
    if validators.url(url):
        scheme, netloc, path, params, query, fragment = urlparse(url)
        if scheme.lower() == "https":
            return True
    return False


def is_svg(stream):
    tag = None
    try:
        for event, el in eT.iterparse(stream, ("start",)):
            tag = el.tag
            break
    except eT.ParseError:
        pass
    return tag == "{http://www.w3.org/2000/svg}svg"


class OAuthLoginView(login_view):
    def processView(self):
        client_id = self.request.matchdict["clientid"]
        if get_client_name(self.request, client_id) is None:
            raise HTTPNotFound

        result = login_view.processView(self)

        if type(result) is dict:
            client_id = self.request.matchdict["clientid"]
            result["clientid"] = client_id
            result["clientname"] = get_client_name(self.request, client_id)
        return result


class OAuthAddClientView(privateView):
    def __init__(self, request):
        privateView.__init__(self, request)
        self.errors = []

    def processView(self):
        client_details = {}

        if self.user.login != "bioversity":
            raise HTTPNotFound

        if self.request.method == "POST":
            client_details = self.getPostDict()
            if validate_url(client_details["client_uri"]):
                if validate_url(client_details["redirect_uri"]):
                    scheme, netloc, path, params, query, fragment = urlparse(
                        client_details["client_uri"]
                    )
                    client_uri = scheme + "://" + netloc + path
                    client_details["client_uri"] = client_uri
                    has_file = True
                    input_file_name = ""
                    input_file = ""
                    try:
                        input_file = self.request.POST["file"].file
                        input_file_name = self.request.POST["file"].filename.lower()
                        if os.path.isabs(input_file_name):
                            input_file_name = os.path.basename(input_file_name)
                        slash_index = input_file_name.find("\\")
                        if slash_index >= 0:
                            input_file_name = input_file_name[slash_index + 1 :]
                        input_file.seek(0)
                        input_file_name = input_file_name.replace(" ", "_")
                        has_image = imghdr.what(input_file)
                        if has_image is None:
                            has_image = False
                        else:
                            has_image = True
                        input_file.seek(0)
                        if not has_image:
                            has_image = is_svg(input_file)

                        if not has_image:
                            self.errors.append(
                                self._(
                                    "You uploaded a logo but is not an image or a SVG"
                                )
                            )
                            return {
                                "clientDetails": client_details,
                                "errors": self.errors,
                                "sectionActive": "OAuth2Provider",
                            }
                        input_file.seek(0)
                    except Exception as e:
                        log.info("No file attached. Error {}".format(str(e)))
                        has_file = False
                    if has_file:
                        if not client_uri_exist(self.request, client_uri):
                            mt = mimetypes.guess_type(input_file_name)
                            if mt is not None:
                                client_details["client_logo_mimetype"] = mt[0]
                            client_details["scope"] = "['profile', 'offline_access']"
                            client_details["grant_type"] = "authorization_code"
                            client_details["response_type"] = "code"
                            client_details[
                                "token_endpoint_auth_method"
                            ] = "client_secret_basic"
                            client_details["client_logo_file"] = input_file_name
                            registered, message = register_client(
                                self.request, client_details, "bioversity"
                            )
                            if registered:
                                store_file(
                                    self.request, message, input_file_name, input_file
                                )
                                next_page = self.request.params.get(
                                    "next"
                                ) or self.request.route_url("oauth2_client_list")
                                self.request.session.flash(
                                    self._("The client has been added.")
                                )
                                self.returnRawViewResult = True
                                return HTTPFound(location=next_page)
                            else:
                                self.errors.append(message)
                        self.errors.append(self._("This URI has been already defined"))
                    else:
                        self.errors.append(
                            self._("You need to indicate a logo image file")
                        )
                else:
                    self.errors.append(
                        self._("This Redirect URI is not valid or it's not HTTPS")
                    )
            else:
                self.errors.append(
                    self._("This client URI is not valid or it's not HTTPS")
                )

        return {
            "clientDetails": client_details,
            "errors": self.errors,
            "sectionActive": "OAuth2Provider",
        }


class OAuthClientLogoView(publicView):
    def processView(self):
        unique_request = str(uuid.uuid4())
        client_id = self.request.matchdict["clientid"]
        item_file = get_client_logo(self.request, client_id)
        if item_file is None:
            raise HTTPNotFound

        if item_file is not None:
            stream = get_stream(self.request, client_id, item_file)
            if stream is not None:
                response = Response()
                return response_stream(stream, item_file, response, unique_request)
        raise HTTPNotFound


class OAuthDeleteClientView(privateView):
    def __init__(self, request):
        privateView.__init__(self, request)
        self.checkCrossPost = False
        self.errors = []

    def processView(self):

        client_id = self.request.matchdict["clientid"]
        if self.user.login != "bioversity":
            raise HTTPNotFound
        deleted, message = delete_client(self.request, "bioversity", client_id)
        next_page = self.request.params.get("next") or self.request.route_url(
            "oauth2_client_list"
        )
        self.returnRawViewResult = True
        if deleted:
            self.request.session.flash(self._("The client has been deleted."))
            return HTTPFound(location=next_page)
        else:
            self.errors.append(message)
            return HTTPFound(location=next_page)


class OAuthEditClientLogoView(privateView):
    def __init__(self, request):
        privateView.__init__(self, request)
        self.errors = []

    def processView(self):
        client_details = {}

        client_id = self.request.matchdict["clientid"]
        if self.user.login != "bioversity":
            raise HTTPNotFound

        if self.request.method == "POST":
            client_details = self.getPostDict()
            has_file = True
            input_file_name = ""
            input_file = ""
            try:
                input_file = self.request.POST["file"].file
                input_file_name = self.request.POST["file"].filename.lower()
                if os.path.isabs(input_file_name):
                    input_file_name = os.path.basename(input_file_name)
                slash_index = input_file_name.find("\\")
                if slash_index >= 0:
                    input_file_name = input_file_name[slash_index + 1 :]
                input_file.seek(0)
                input_file_name = input_file_name.replace(" ", "_")
                has_image = imghdr.what(input_file)
                if has_image is None:
                    has_image = False
                else:
                    has_image = True
                input_file.seek(0)
                if not has_image:
                    has_image = is_svg(input_file)
                if not has_image:
                    self.errors.append(
                        self._("You uploaded a logo but is not an image or a SVG")
                    )
                    return {
                        "clientDetails": client_details,
                        "errors": self.errors,
                        "sectionActive": "OAuth2Provider",
                    }
                input_file.seek(0)
            except Exception as e:
                log.info("No file attached. Error {}".format(str(e)))
                has_file = False
            if has_file:
                update_details = {}
                mt = mimetypes.guess_type(input_file_name)
                if mt is not None:
                    update_details["client_logo_mimetype"] = mt[0]
                update_details["client_logo_file"] = input_file_name
                updated, message = update_client_logo(
                    self.request, "bioversity", client_id, update_details
                )
                if updated:
                    store_file(self.request, client_id, input_file_name, input_file)
                    next_page = self.request.params.get(
                        "next"
                    ) or self.request.route_url("oauth2_client_list")
                    self.request.session.flash(
                        self._("The client logo has been edited.")
                    )
                    self.returnRawViewResult = True
                    return HTTPFound(location=next_page)
                else:
                    self.errors.append(message)
            else:
                self.errors.append(self._("You need to indicate a logo image file"))

        return {
            "clientDetails": client_details,
            "errors": self.errors,
            "sectionActive": "OAuth2Provider",
        }


def get_policy(request, policy_name):
    policies = request.policies()
    for policy in policies:
        if policy["name"] == policy_name:
            return policy["policy"]
    return None


class OAuthAuthorizeView(publicView):
    def processView(self):
        policy = get_policy(self.request, "main")
        login_data = policy.authenticated_userid(self.request)
        if login_data is not None:
            current_user = getUserData(login_data, self.request)
            if current_user is not None:
                if self.request.method == "GET":
                    authorization = authorization_function(self)
                    config_oauth(self, authorization)

                    return HTTPFound(
                        authorization.create_authorization_response(
                            req=self.request, grant_user=current_user
                        )
                    )

        client_id = self.request.params.get("client_id", "none")
        next_page_oauth = self.request.url
        login_page = self.request.route_url(
            "oauth2_client_login",
            clientid=client_id,
            _query=(("next", next_page_oauth),),
        )
        return HTTPFound(login_page)


class OauthTokenView(publicView):
    def processView(self):
        authorization = authorization_function(self)
        config_oauth(self, authorization)
        res = authorization.create_token_response(req=self.request)
        payload = json.dumps(res["token"])

        self.request.response.text = payload
        self.request.response.header = res["header"]
        return self.request.response


class OauthRevokeView(publicView):
    def processView(self):
        authorization = authorization_function(self)
        config_oauth(self, authorization)
        return authorization.create_endpoint_response("revocation")


class OauthProfileView(publicView):
    def processView(self):
        bearer = self.request.headers.get("Authorization")
        token = bearer.split("Bearer ")[1]
        user = get_user_by_token(self.request, token)
        if user is None:
            raise HTTPNotFound
        user_dict = {
            "id": user.user_name,
            "email": user.user_email,
            "name": user.user_fullname,
            "given_name": user.user_name,
        }

        user_json_data = json.dumps(user_dict)
        self.request.response.text = user_json_data
        return self.request.response
