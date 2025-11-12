from __future__ import annotations

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard(language: str = "ru"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Управление реквизитами", callback_data="menu:wallets")
    builder.button(text="💼 Создать сделку", callback_data="menu:create_deal")
    builder.button(text="👥 Реферальная система", callback_data="menu:referrals")
    builder.button(text="🌐 Change the Language", callback_data="menu:language")
    builder.button(text="📞 Поддержка", callback_data="menu:support")
    builder.adjust(1)
    return builder.as_markup()


def wallets_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💎 TON", callback_data="wallet:ton"),
        InlineKeyboardButton(text="💵 RUB", callback_data="wallet:rub"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Проверить баланс", callback_data="wallet:balance"),
    )
    builder.row(
        InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="wallet:topup"),
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def language_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def deal_currency_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💎 TON-кошелек", callback_data="deal:ton"))
    builder.row(InlineKeyboardButton(text="💳 На карту", callback_data="deal:card"))
    builder.row(InlineKeyboardButton(text="⭐ Звёзды", callback_data="deal:stars"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def deal_manage_keyboard(token: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отменить сделку", callback_data=f"deal-cancel:{token}"))
    builder.row(InlineKeyboardButton(text="⬅ Главное меню", callback_data="go:home"))
    return builder.as_markup()


def buyer_keyboard(token: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Оплатить", callback_data=f"buyer:pay:{token}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=f"buyer:cancel:{token}"))
    return builder.as_markup()


def referral_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Моя статистика", callback_data="ref:stats"))
    builder.row(InlineKeyboardButton(text="🔗 Поделиться ссылкой", callback_data="ref:share"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()
