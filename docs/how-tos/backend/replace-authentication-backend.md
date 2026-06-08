# Replacing the authentication backend 
Cashflow was configured to use  [our custom OIDC provider SSO](https://github.com/datasektionen/sso). We use the 
`mozilla-django-oidc` library to handle authentication, by subclassing the built-in `OIDCAuthenticationBackend` (see `cashflow/dauth.py`).

## Use another OIDC provider (recommended)

> [!TIP]
> See the instructions in the [mozilla-django-oidc documentation](https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html) for all configuration options.

1. Change the authentication backend in `settings.py`, either to the built-in `OIDCAuthenticationBackend` or to your own subclass of it.
    ```python
    AUTHENTICATION_BACKENDS = (
        'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    )
    ```
2. Set all necessary configuration options. The backend requires the client credentials and all of the endpoints below (plus `OIDC_OP_JWKS_ENDPOINT` when `OIDC_RP_SIGN_ALGO` is an `RS*`/`ES*` algorithm) — it raises `ImproperlyConfigured` if any are missing. For example:
   ```python
   OIDC_RP_CLIENT_ID = "your-client-id"
   OIDC_RP_CLIENT_SECRET = "your-client-secret"
   OIDC_RP_SIGN_ALGO = "RS256"
   OIDC_OP_AUTHORIZATION_ENDPOINT = "https://your-oidc-provider.com/authorize"
   OIDC_OP_TOKEN_ENDPOINT = "https://your-oidc-provider.com/token"
   OIDC_OP_USER_ENDPOINT = "https://your-oidc-provider.com/userinfo"
   OIDC_OP_JWKS_ENDPOINT = "https://your-oidc-provider.com/jwks"
   ```
   (The endpoint URLs for your provider are listed in its OpenID configuration, available at `https://your-oidc-provider.com/.well-known/openid-configuration`.)
   

## Use another authentication method
It is possible to use any other Django authentication backend, such as the built-in `ModelBackend` for username/password authentication. 

1. Remove `mozilla_django_oidc.middleware.SessionRefresh` from `MIDDLEWARE` in `settings.py`, and remove `mozilla_django_oidc` from `INSTALLED_APPS`.
2. Change the authentication backend in `settings.py` to the desired backend. For example, to use the built-in `ModelBackend`:
    ```python
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
    )
    ```
3. Create any necessary views for authentication and route them in `urls.py`.
    > [!WARNING]  
    > As of writing, the frontend expects the login view to be at `/oidc/authenticate/` and the logout view to be at `/oidc/logout/`. You may need to change the frontend code if you want to use different URLs.