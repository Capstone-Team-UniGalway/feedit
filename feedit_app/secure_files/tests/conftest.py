import pytest
from django.test.utils import override_settings


@pytest.fixture(scope="function", autouse=True)
def temp_media_root(tmp_path):
    """Use a temporary MEDIA_ROOT during tests and clean up after."""
    with override_settings(
        MEDIA_ROOT=tmp_path,
        AUTHENTICATION_BACKENDS=[
            "django.contrib.auth.backends.ModelBackend",  # default backend for tests
        ],
    ):
        yield
