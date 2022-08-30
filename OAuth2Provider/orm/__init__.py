from OAuth2Provider.orm.OAuth2Provider import (
    OAuth2Client,
    OAuth2AuthorizationCode,
    OAuth2Token,
)

from sqlalchemy.orm import configure_mappers
from climmob.models.schema import initialize_schema

configure_mappers()


def includeme(config):
    initialize_schema()
