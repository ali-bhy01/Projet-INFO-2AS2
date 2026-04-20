import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout

from src.service.collector.api_client import CapitalClient
from src.service.collector.session_manager import SessionManager


@pytest.fixture
def mock_session():
    session = MagicMock(spec=SessionManager)
    session.get_headers.return_value = {"CST": "test_cst", "X-SECURITY-TOKEN": "test_token"}
    return session


@pytest.fixture
def client(mock_session):
    return CapitalClient(mock_session)


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data
    r.text = str(json_data)
    r.content = b"content"
    return r


# ------------------------------------------------------------------ get_instrument

class TestGetInstrument:
    def test_success(self, client):
        with patch("requests.get", return_value=_mock_response({"markets": []})) as mock_get:
            result = client.get_instrument("UK 100")
            assert result == {"markets": []}
            mock_get.assert_called_once()

    def test_passes_search_term(self, client):
        with patch("requests.get", return_value=_mock_response({})) as mock_get:
            client.get_instrument("DE40")
            _, kwargs = mock_get.call_args
            assert kwargs["params"]["searchTerm"] == "DE40"

    def test_raises_on_error(self, client):
        with patch("requests.get", return_value=_mock_response({}, status_code=401)):
            with pytest.raises(ValueError, match="401"):
                client.get_instrument("DE40")


# ------------------------------------------------------------------ get_candles

class TestGetCandles:
    def test_success(self, client):
        payload = {"prices": [{"snapshotTimeUTC": "2025-01-01T09:15:00"}]}
        with patch("requests.get", return_value=_mock_response(payload)):
            result = client.get_candles("DE40", max=5)
            assert "prices" in result

    def test_passes_resolution_and_max(self, client):
        with patch("requests.get", return_value=_mock_response({"prices": []})) as mock_get:
            client.get_candles("DE40", resolution="HOUR", max=20)
            _, kwargs = mock_get.call_args
            assert kwargs["params"]["resolution"] == "HOUR"
            assert kwargs["params"]["max"] == 20

    def test_raises_on_error(self, client):
        with patch("requests.get", return_value=_mock_response({}, status_code=404)):
            with pytest.raises(ValueError, match="404"):
                client.get_candles("DE40")


# ------------------------------------------------------------------ get_candles_range

class TestGetCandlesRange:
    def test_success(self, client):
        payload = {"prices": []}
        with patch("requests.get", return_value=_mock_response(payload)):
            result = client.get_candles_range("DE40", "2025-01-01T09:00:00", "2025-01-01T10:00:00")
            assert result == payload

    def test_retries_on_timeout(self, client):
        success = _mock_response({"prices": []})
        with patch("requests.get", side_effect=[Timeout(), success]):
            result = client.get_candles_range("DE40", "2025-01-01T09:00:00", "2025-01-01T10:00:00")
            assert result == {"prices": []}

    def test_raises_after_max_retries(self, client):
        with patch("requests.get", side_effect=Timeout()):
            with pytest.raises(ValueError, match="Timeout"):
                client.get_candles_range(
                    "DE40", "2025-01-01T09:00:00", "2025-01-01T10:00:00", retries=2
                )

    def test_raises_on_http_error(self, client):
        with patch("requests.get", return_value=_mock_response({}, status_code=500)):
            with pytest.raises(ValueError, match="500"):
                client.get_candles_range("DE40", "2025-01-01T09:00:00", "2025-01-01T10:00:00")


# ------------------------------------------------------------------ get_working_orders

class TestGetWorkingOrders:
    def test_returns_list(self, client):
        payload = {"workingOrders": [{"id": "1"}, {"id": "2"}]}
        with patch("requests.get", return_value=_mock_response(payload)):
            assert len(client.get_working_orders()) == 2

    def test_empty_orders(self, client):
        with patch("requests.get", return_value=_mock_response({"workingOrders": []})):
            assert client.get_working_orders() == []

    def test_raises_on_error(self, client):
        with patch("requests.get", return_value=_mock_response({}, status_code=403)):
            with pytest.raises(ValueError):
                client.get_working_orders()


# ------------------------------------------------------------------ cancel_working_order

class TestCancelWorkingOrder:
    def test_success_with_content(self, client):
        with patch("requests.delete", return_value=_mock_response({"status": "ok"})):
            result = client.cancel_working_order("deal123")
            assert result == {"status": "ok"}

    def test_success_empty_response(self, client):
        r = MagicMock()
        r.status_code = 204
        r.content = b""
        with patch("requests.delete", return_value=r):
            assert client.cancel_working_order("deal123") == {}

    def test_raises_on_error(self, client):
        with patch("requests.delete", return_value=_mock_response({}, status_code=404)):
            with pytest.raises(ValueError):
                client.cancel_working_order("bad_id")


# ------------------------------------------------------------------ get_open_positions

class TestGetOpenPositions:
    def test_returns_list(self, client):
        with patch("requests.get", return_value=_mock_response({"positions": [{"id": "p1"}]})):
            result = client.get_open_positions()
            assert result == [{"id": "p1"}]

    def test_empty_positions(self, client):
        with patch("requests.get", return_value=_mock_response({"positions": []})):
            assert client.get_open_positions() == []

    def test_raises_on_error(self, client):
        with patch("requests.get", return_value=_mock_response({}, status_code=500)):
            with pytest.raises(ValueError):
                client.get_open_positions()


# ------------------------------------------------------------------ close_position

class TestClosePosition:
    def test_success_with_content(self, client):
        with patch("requests.delete", return_value=_mock_response({"dealReference": "abc"})):
            result = client.close_position("pos123")
            assert result == {"dealReference": "abc"}

    def test_raises_on_error(self, client):
        with patch("requests.delete", return_value=_mock_response({}, status_code=404)):
            with pytest.raises(ValueError):
                client.close_position("bad_pos")
