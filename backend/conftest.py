"""Root conftest: re-exports the shared fixtures for every app's test package.

pytest only auto-discovers a `conftest.py`'s fixtures for tests in that
directory or below it, so `core/tests/conftest.py`'s `api_client` and
`app_settings` fixtures need a re-export at the tree root to be visible to
`accounts/tests/`, `prompts/tests/`, and every other app's test package. See
the docstring on `core/tests/conftest.py` for why the fixtures themselves live
there rather than here.
"""

from core.tests.conftest import api_client, app_settings  # noqa: F401
