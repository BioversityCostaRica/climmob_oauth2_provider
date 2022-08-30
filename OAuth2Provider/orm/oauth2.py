from OAuth2Provider.processes import (
    AuthorizationServer,
)
from authlib.oauth2 import (
    ResourceProtector,
)
from authlib.integrations.sqla_oauth2 import (
    create_query_client_func,
    create_revocation_endpoint,
    create_bearer_token_validator,
)
from OAuth2Provider.processes.inte_sqla2_functions import (
    create_save_token_func1,
)
from OAuth2Provider.processes.grants_authorization_code import (
    AuthorizationCodeGrant as AuthorizationCodeGrant_base,
)
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import CodeChallenge
from OAuth2Provider.orm.OAuth2Provider import (
    OAOAuthUser,
    OAuth2Client,
    OAuth2AuthorizationCode,
    OAuth2Token,
)
from climmob.models.schema import mapFromSchema


class AuthorizationCodeGrant(AuthorizationCodeGrant_base):
    TOKEN_ENDPOINT_AUTH_METHODS = [
        "client_secret_basic",
        "client_secret_post",
        "none",
    ]

    def save_authorization_code(self, code, request, req):
        code_challenge = request.data.get("code_challenge")
        code_challenge_method = request.data.get("code_challenge_method")
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=request.client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.login,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        req.dbsession.add(auth_code)
        req.dbsession.flush()
        return auth_code

    def query_authorization_code(self, code, client, req):
        res = mapFromSchema(client)
        auth_code = (
            req.dbsession.query(OAuth2AuthorizationCode)
            .filter(OAuth2AuthorizationCode.code == code)
            .filter(OAuth2AuthorizationCode.client_id == res["client_id"])
            .first()
        )
        if auth_code and not auth_code.is_expired():
            return auth_code

    def delete_authorization_code(self, authorization_code, req):
        req.dbsession.delete(authorization_code)
        req.dbsession.flush()

    def authenticate_user(self, authorization_code, req):
        return (
            req.dbsession.query(OAOAuthUser)
            .filter(OAOAuthUser.user_name == authorization_code.user_id)
            .first()
        )


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        user = OAOAuthUser.query.filter_by(username=username).first()
        if user is not None and user.check_password(password):
            return user


class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token):
        token = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if token and token.is_refresh_token_active():
            return token

    def authenticate_user(self, credential):
        return OAOAuthUser.query.get(credential.user_id)

    def revoke_old_credential(self, credential):
        credential.revoked = True
        self.request.dbsession.add(credential)
        self.request.dbsession.commit()


def authorization_function(self):
    query_client = create_query_client_func(self.request.dbsession, OAuth2Client)
    save_token = create_save_token_func1(self.request.dbsession, OAuth2Token)
    authorization = AuthorizationServer(
        query_client=query_client,
        save_token=save_token,
    )
    return authorization


require_oauth = ResourceProtector()


def config_oauth(self, authorization):

    # support all grants
    authorization.register_grant(grants.ImplicitGrant)
    authorization.register_grant(grants.ClientCredentialsGrant)
    authorization.register_grant(AuthorizationCodeGrant, [CodeChallenge(required=True)])
    authorization.register_grant(PasswordGrant)
    authorization.register_grant(RefreshTokenGrant)

    # support revocation
    revocation_cls = create_revocation_endpoint(self.request.dbsession, OAuth2Token)
    authorization.register_endpoint(revocation_cls)

    # protect resource
    bearer_cls = create_bearer_token_validator(self.request.dbsession, OAuth2Token)
    require_oauth.register_token_validator(bearer_cls())
