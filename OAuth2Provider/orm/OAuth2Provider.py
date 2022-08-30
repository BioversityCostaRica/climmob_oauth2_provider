from climmob.models.meta import Base
from climmob.models import User
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
import time
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    ForeignKey,
    INTEGER,
    Unicode,
)


class OAOAuthUser(User):
    def get_user_id(self):
        return self.user_name


class OAuth2Client(Base, OAuth2ClientMixin):
    __tablename__ = "oauth2_client"

    id = Column(INTEGER, primary_key=True)
    user_id = Column(Unicode(80), ForeignKey("user.user_name", ondelete="CASCADE"))
    client_uri = Column(Unicode(255), unique=True)
    client_name = Column(Unicode(120))
    client_logo_file = Column(Unicode(64))
    client_logo_mimetype = Column(Unicode(120))
    user = relationship("OAOAuthUser")

    def __init__(
        self,
        client_id,
        client_secret,
        client_id_issued_at,
        client_uri,
        client_name,
        client_logo_file,
        client_logo_mimetype,
        user_id,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_id_issued_at = client_id_issued_at
        self.user_id = user_id
        self.client_uri = client_uri
        self.client_name = client_name
        self.client_logo_file = client_logo_file
        self.client_logo_mimetype = client_logo_mimetype


class OAuth2AuthorizationCode(Base, OAuth2AuthorizationCodeMixin):
    __tablename__ = "oauth2_code"

    id = Column(INTEGER, primary_key=True)
    user_id = Column(Unicode(80), ForeignKey("user.user_name", ondelete="CASCADE"))
    user = relationship("OAOAuthUser")

    def __init__(
        self,
        code,
        client_id,
        redirect_uri,
        scope,
        user_id,
        code_challenge,
        code_challenge_method,
    ):
        self.code = code
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.user_id = user_id
        self.code_challenge = code_challenge
        self.code_challenge_method = code_challenge_method


class OAuth2Token(Base, OAuth2TokenMixin):
    __tablename__ = "oauth2_token"

    id = Column(INTEGER, primary_key=True)
    user_id = Column(Unicode(80), ForeignKey("user.user_name", ondelete="CASCADE"))
    user = relationship("OAOAuthUser")

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()
