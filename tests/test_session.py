import pytest
from unittest.mock import patch, MagicMock
from src.service.collector.session_manager import SessionManager


def _mock_post(cst: str = "fake_cst", token: str = "fake_token", status: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.headers = {"CST": cst, "X-SECURITY-TOKEN": token}
    r.text = "OK" if status == 200 else "Unauthorized"
    return r


@pytest.fixture
def session():
    with patch("requests.post", return_value=_mock_post()):
        sm = SessionManager(api_key="key", identifier="user@test.com", password="pass")
    return sm


# ------------------------------------------------------------------ ouverture de session

def test_session_stores_cst():
    with patch("requests.post", return_value=_mock_post(cst="my_cst")):
        sm = SessionManager(api_key="k", identifier="u", password="p")
    assert sm.cst == "my_cst"


def test_session_stores_security_token():
    with patch("requests.post", return_value=_mock_post(token="my_token")):
        sm = SessionManager(api_key="k", identifier="u", password="p")
    assert sm.security_token == "my_token"


def test_session_sends_api_key_header():
    with patch("requests.post", return_value=_mock_post()) as mock_post:
        SessionManager(api_key="MY_KEY", identifier="u", password="p")
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["X-CAP-API-KEY"] == "MY_KEY"


def test_session_sends_credentials():
    with patch("requests.post", return_value=_mock_post()) as mock_post:
        SessionManager(api_key="k", identifier="user@test.com", password="secret")
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["identifier"] == "user@test.com"
        assert kwargs["json"]["password"] == "secret"


def test_session_raises_on_failure():
    with patch("requests.post", return_value=_mock_post(status=401)):
        with pytest.raises(ValueError, match="401"):
            SessionManager(api_key="k", identifier="u", password="wrong")


# ------------------------------------------------------------------ get_headers

def test_get_headers_returns_cst_and_token(session):
    headers = session.get_headers()
    assert headers["CST"] == "fake_cst"
    assert headers["X-SECURITY-TOKEN"] == "fake_token"


# ------------------------------------------------------------------ close

def test_close_sets_stop_event(session):
    assert not session._stop_event.is_set()
    session.close()
    assert session._stop_event.is_set()


# ------------------------------------------------------------------ ping (avec ping=True)

def test_ping_thread_starts_with_ping_true():
    with patch("requests.post", return_value=_mock_post()):
        with patch.object(SessionManager, "_start_ping") as mock_ping:
            SessionManager(api_key="k", identifier="u", password="p", ping=True)
            mock_ping.assert_called_once()


def test_no_ping_thread_by_default():
    with patch("requests.post", return_value=_mock_post()):
        with patch.object(SessionManager, "_start_ping") as mock_ping:
            SessionManager(api_key="k", identifier="u", password="p")
            mock_ping.assert_not_called()
