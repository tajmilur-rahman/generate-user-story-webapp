"""
Feature flags.

Each flag hides a feature from the interface without removing it. The routes
stay registered and the code paths stay live, so turning one on is a restart
with one environment variable set -- nothing has to be uncommented or rebuilt.

Google sign-in defaults to off for the conference demo, which shows
email/password sign-in only. GitHub integration defaults to on.
"""
import os

_TRUTHY = ('1', 'true', 'yes', 'on')


def _flag(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


def google_login_enabled():
    """Show the "Continue with Google" button on the login page.

    /auth/google and /auth/callback stay registered either way.
    """
    return _flag('SHOW_GOOGLE_LOGIN')


def github_integration_enabled():
    """Show the GitHub panel and the "Integrate Selected" button.

    /auth/github, /auth/github/callback, /api/github-config and
    /api/integrate-selected-github stay registered either way, and the
    github_* columns on the user row are untouched.

    On by default. Set SHOW_GITHUB_INTEGRATION=false to hide the panel again,
    which is worth doing on a public instance where connecting a real GitHub
    account would put an owner name on screen.
    """
    return _flag('SHOW_GITHUB_INTEGRATION', default=True)
