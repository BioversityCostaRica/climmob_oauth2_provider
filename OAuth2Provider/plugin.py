import climmob.plugins as plugins
import climmob.plugins.utilities as u
from OAuth2Provider.views import (
    OAuthClientListView,
    OAuthAddClientView,
    OAuthClientLogoView,
    OAuthDeleteClientView,
    OAuthEditClientLogoView,
    OAuthAuthorizeView,
    OauthTokenView,
    OauthRevokeView,
    OauthProfileView,
    OAuthLoginView,
)
import sys
import os


class OAuth2Provider(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IDatabase)
    plugins.implements(plugins.IResource)

    def before_mapping(self, config):
        # We don't add any routes before the host application
        return []

    def after_mapping(self, config):
        # We add here a new route /json that returns a JSON
        custom_map = [
            u.addRoute(
                "oauth2_client_list",
                "/oauth2/settings/list",
                OAuthClientListView,
                "oauth2/clients.jinja2",
            ),
            u.addRoute(
                "oauth2_add_client",
                "/oauth2/settings/add_client",
                OAuthAddClientView,
                "oauth2/add_client.jinja2",
            ),
            u.addRoute(
                "oauth2_get_client_logo",
                "/oauth2/{clientid}/logo",
                OAuthClientLogoView,
                None,
            ),
            u.addRoute(
                "oauth2_delete_client",
                "/oauth2/settings/client/{clientid}/delete",
                OAuthDeleteClientView,
                None,
            ),
            u.addRoute(
                "oauth2_edit_client",
                "/oauth2/settings/client/{clientid}/update_logo",
                OAuthEditClientLogoView,
                "oauth2/edit_client.jinja2",
            ),
            u.addRoute(
                "oauth2_client_login",
                "/oauth2/client/{clientid}/login",
                OAuthLoginView,
                "oauth2/login.jinja2",
            ),
            u.addRoute(
                "oauth2_authorize", "/oauth2/authorize", OAuthAuthorizeView, None
            ),
            u.addRoute("oauth2_token", "/oauth2/token", OauthTokenView, "json"),
            u.addRoute("oauth2_revoke", "/oauth2/revoke", OauthRevokeView, None),
            u.addRoute("oauth2_profile", "/oauth2/profile", OauthProfileView, "json"),
        ]

        return custom_map

    def update_config(self, config):
        # We add here the templates of the plugin to the config
        u.addTemplatesDirectory(config, "templates")

    def get_translation_directory(self):
        module = sys.modules["OAuth2Provider"]
        return os.path.join(os.path.dirname(module.__file__), "locale")

    def get_translation_domain(self):
        return "OAuth2Provider"

    def update_orm(self, config):
        config.include("OAuth2Provider.orm")

    def update_extendable_tables(self, tables_allowed):
        tables_allowed.append("OAuth2Provider_example")
        return tables_allowed

    def update_extendable_modules(self, modules_allowed):
        modules_allowed.append("OAuth2Provider.orm.OAuth2Provider")
        return modules_allowed

    # IResource
    def add_libraries(self, config):
        libraries = [u.addLibrary("OAuth2Provider", "resources")]
        return libraries

    def add_js_resources(self, config):
        my_plugin_js = [
            u.addJSResource(
                "OAuth2Provider",
                "bs-custom-file-input",
                "bs-custom-file-input/bs-custom-file-input.min.js",
                None,
            )
        ]
        return my_plugin_js

    def add_css_resources(self, config):
        return []
