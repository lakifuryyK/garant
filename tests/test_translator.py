from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bot.i18n import translate


def test_translate_returns_russian_by_default():
    text = translate("wallet_saved")
    assert "Реквизиты" in text


def test_translate_handles_parameters():
    text = translate("deal_created", language="en", amount=100, description="Gift", link="url")
    assert "Deal created" in text
    assert "100" in text
