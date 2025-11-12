from __future__ import annotations

from typing import Dict


class Translator:
    """Simple key-based translator for two supported languages."""

    _messages: Dict[str, Dict[str, str]] = {
        "start_description": {
            "ru": (
                "Добро пожаловать в ELF OTC — надёжный P2P-гарант\n\n"
                "Покупайте и продавайте всё, что угодно — безопасно.\n"
                "Сделки проходят легко и без риска."
            ),
            "en": (
                "Welcome to ELF OTC — your trusted P2P escrow.\n\n"
                "Buy and sell anything safely.\n"
                "Deals are fast and risk-free."
            ),
        },
        "wallet_prompt_ton": {
            "ru": "✍ Введите реквизиты для TON (они будут сохранены).",
            "en": "✍ Enter your TON wallet details (they will be saved).",
        },
        "wallet_prompt_rub": {
            "ru": "✍ Введите реквизиты для RUB (они будут сохранены).",
            "en": "✍ Enter your RUB bank details (they will be saved).",
        },
        "wallet_saved": {
            "ru": "✅ Реквизиты сохранены!",
            "en": "✅ Details saved!",
        },
        "balance": {
            "ru": "💰 Ваш баланс TON: {ton}\n{rub_line}",
            "en": "💰 Your TON balance: {ton}\n{rub_line}",
        },
        "balance_no_wallet_rub": {
            "ru": "❌ Кошелёк RUB не привязан",
            "en": "❌ RUB wallet is not linked",
        },
        "balance_wallet_rub": {
            "ru": "💵 Ваш баланс RUB: {rub}",
            "en": "💵 Your RUB balance: {rub}",
        },
        "balance_error": {
            "ru": "❌ Сбой в системе. Попробуйте позже.",
            "en": "❌ System error. Please try again later.",
        },
        "topup_instructions": {
            "ru": (
                "Чтобы пополнить баланс, отправьте средства на указанные реквизиты "
                "и сообщите в поддержку."
            ),
            "en": (
                "To top up your balance, transfer funds to the provided details "
                "and contact support."
            ),
        },
        "deal_amount_prompt": {
            "ru": "💰 Напишите сумму сделки (например: 1000):",
            "en": "💰 Enter the deal amount (for example: 1000):",
        },
        "deal_description_prompt": {
            "ru": "🧾 Теперь напишите название подарка:",
            "en": "🧾 Now write the gift name:",
        },
        "deal_created": {
            "ru": (
                "✅ Сделка создана!\nСумма: {amount}\nОписание: {description}\n"
                "Ссылка для покупателя: {link}"
            ),
            "en": (
                "✅ Deal created!\nAmount: {amount}\nDescription: {description}\n"
                "Buyer link: {link}"
            ),
        },
        "deal_cancelled": {
            "ru": "❌ Сделка отменена.",
            "en": "❌ Deal cancelled.",
        },
        "deal_already_processed": {
            "ru": "⚠️ Сделка уже обработана.",
            "en": "⚠️ Deal already processed.",
        },
        "deal_not_found": {
            "ru": "❌ Сделка не найдена.",
            "en": "❌ Deal not found.",
        },
        "buyer_view": {
            "ru": (
                "🛒 Сделка от @{seller}\n"
                "Описание: {description}\n"
                "Сумма: {amount}\n"
                "Реквизиты для оплаты: {address}\n"
                "Комментарий (memo): {memo}\n\n"
                "⚠ Пожалуйста, убедитесь в правильности данных перед оплатой. "
                "Комментарий обязателен."
            ),
            "en": (
                "🛒 Deal from @{seller}\n"
                "Description: {description}\n"
                "Amount: {amount}\n"
                "Payment details: {address}\n"
                "Comment (memo): {memo}\n\n"
                "⚠ Double-check the data before paying. Memo is required."
            ),
        },
        "insufficient_funds": {
            "ru": "❌ Недостаточно средств. Пополните баланс и попробуйте снова.",
            "en": "❌ Not enough funds. Top up your balance and try again.",
        },
        "payment_success": {
            "ru": "✅ Оплата прошла успешно!",
            "en": "✅ Payment successful!",
        },
        "ref_main": {
            "ru": (
                "🎁 Реферальная система\nВаши рефералы: {total}\n"
                "Ваша реферальная ссылка: {link}\n"
                "За каждого приглашённого друга вы получаете бонусы!"
            ),
            "en": (
                "🎁 Referral system\nYour referrals: {total}\n"
                "Your referral link: {link}\n"
                "Invite friends and earn rewards!"
            ),
        },
        "ref_stats": {
            "ru": "📊 Количество рефералов: {total}",
            "en": "📊 Number of referrals: {total}",
        },
        "ref_share": {
            "ru": "Присоединяйся к ELF OTC! 🔥\nБезопасные P2P-сделки с гарантом\n{link}",
            "en": "Join ELF OTC! 🔥\nSecure P2P deals with escrow\n{link}",
        },
        "support": {
            "ru": "📞 Поддержка: @ElfGiftsSup",
            "en": "📞 Support: @ElfGiftsSup",
        },
        "language_prompt": {
            "ru": "🌐 Выберите язык:",
            "en": "🌐 Choose a language:",
        },
    }

    def get(self, key: str, language: str = "ru", **kwargs: str | float) -> str:
        translations = self._messages[key]
        text = translations.get(language) or translations["ru"]
        if kwargs:
            return text.format(**kwargs)
        return text


def translate(key: str, language: str = "ru", **kwargs: str | float) -> str:
    return Translator().get(key, language, **kwargs)
