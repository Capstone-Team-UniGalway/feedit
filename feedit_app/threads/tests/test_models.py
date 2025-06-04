import pytest
from threads.models import Thread

from .factories import ThreadFactory

pytestmark = pytest.mark.django_db


def test_thread_factory_creates_valid_instance():
    thread = ThreadFactory()
    assert isinstance(thread, Thread)
    assert thread.type == Thread.ThreadType.FORUM
    assert thread.visibility == Thread.ThreadVisibility.INTERNAL
    assert thread.company is not None
    assert thread.author is not None
    assert thread.title
    assert thread.content


def test_thread_type_enum_values():
    for thread_type in Thread.ThreadType.values:
        thread = ThreadFactory(type=thread_type)
        assert thread.type == thread_type


def test_thread_visibility_enum_values():
    for vis in Thread.ThreadVisibility.values:
        thread = ThreadFactory(visibility=vis)
        assert thread.visibility == vis


def test_thread_str_returns_title():
    thread = ThreadFactory(title="Welcome to the Forum")
    assert str(thread) == "Welcome to the Forum"


def test_get_author_name_with_and_without_author():
    thread_with_author = ThreadFactory()
    assert (
        thread_with_author.get_author_name()
        == thread_with_author.author.get_full_name()
    )

    thread_without_author = ThreadFactory(author=None)
    assert thread_without_author.get_author_name() == "Unknown Author"
