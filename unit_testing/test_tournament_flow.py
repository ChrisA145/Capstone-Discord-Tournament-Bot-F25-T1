import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from controller.signup_shared_logic import SharedLogic


@pytest.fixture
def test_player_data():
    with open("combined_player_data.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_load_player_data(test_player_data):
    # Basic sanity check for the test data
    assert "bronze" in test_player_data
    assert isinstance(test_player_data["bronze"], list)
    assert len(test_player_data["bronze"]) > 0


@pytest.mark.asyncio
async def test_execute_signup_model_calls_send_modal_and_deletes_message():
    # Patch the RegisterModal constructed inside SharedLogic so we control the object
    def fake_modal_factory():
        return MagicMock()

    with patch("controller.signup_shared_logic.RegisterModal", side_effect=fake_modal_factory), \
         patch("asyncio.sleep", AsyncMock()):

        mock_interaction = MagicMock()
        mock_interaction.user = "TestUser"

        # Mock response.send_modal to return a message with an async delete()
        message_mock = MagicMock()
        message_mock.delete = AsyncMock()

        mock_response = MagicMock()
        mock_response.send_modal = AsyncMock(return_value=message_mock)
        mock_interaction.response = mock_response

        # Execute the signup flow (timeout patched by asyncio.sleep)
        await SharedLogic.execute_signup_model(mock_interaction, timeout=0.01)

        mock_interaction.response.send_modal.assert_called_once()
        message_mock.delete.assert_awaited()


@pytest.mark.asyncio
async def test_execute_checkin_signup_model_calls_send_modal_and_deletes_message():
    def fake_modal_factory():
        return MagicMock()

    with patch("controller.signup_shared_logic.Checkin_RegisterModal", side_effect=fake_modal_factory), \
         patch("asyncio.sleep", AsyncMock()):

        mock_interaction = MagicMock()
        mock_interaction.user = "TestUser"

        message_mock = MagicMock()
        message_mock.delete = AsyncMock()

        mock_response = MagicMock()
        mock_response.send_modal = AsyncMock(return_value=message_mock)
        mock_interaction.response = mock_response

        await SharedLogic.execute_checkin_signup_model(mock_interaction, timeout=0.01)

        mock_interaction.response.send_modal.assert_called_once()
        message_mock.delete.assert_awaited()
