import pytest
from company_requests.models import Request, RequestReply
from .factories import RequestFactory, RequestReplyFactory

pytestmark = pytest.mark.django_db


def test_request_factory_creates_valid_instance():
    req = RequestFactory()
    assert isinstance(req, Request)
    assert req.status == "pending"
    assert req.type == "join"
    assert req.author is not None
    assert req.company is not None
    assert req.title
    assert req.content


def test_request_status_and_type_choices():
    for status in Request.RequestStatus.values:
        req = RequestFactory(status=status)
        assert req.status == status

    for type in Request.RequestType:
        req = RequestFactory(type=type)
        assert req.type == type


def test_request_reply_factory_creates_valid_instance():
    reply = RequestReplyFactory()
    assert isinstance(reply, RequestReply)
    assert reply.request is not None
    assert reply.author is not None
    assert reply.content


def test_request_reply_links_to_request():
    req = RequestFactory()
    reply = RequestReplyFactory(request=req)
    assert reply.request == req
    assert reply in req.replies.all()
