import pytest
import tournament
import pytest_asyncio
import asyncio
from colorama import Fore, init

init(autoreset=True)

@pytest_asyncio.fixture(name="bot_setup")
async def bot_setup(capsys):
    print("Setting Up Bot")
    await asyncio.sleep(0.10)  # let output flush
    setup_output = capsys.readouterr().out

    bot_task = asyncio.create_task(tournament.main())
    print("Bot Running")
    await asyncio.sleep(0.01)
    running_output = capsys.readouterr().out

    # Combine output if needed
    captured_setup = setup_output + running_output

    yield captured_setup

    print(f"\n{Fore.GREEN}Bot Shutting Down")
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        print(f"{Fore.GREEN}Bot Task Cancelled")


@pytest.mark.asyncio
async def test_bot_fixture(bot_setup):
    assert "Setting Up Bot" in bot_setup
    assert "Bot Running" in bot_setup



