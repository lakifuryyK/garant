from __future__ import annotations

from typing import Optional

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .config import Settings
from .database import Database, Deal
from .i18n import translate
from .keyboards import (
    buyer_keyboard,
    deal_currency_keyboard,
    deal_manage_keyboard,
    language_keyboard,
    main_menu_keyboard,
    referral_keyboard,
    wallets_menu_keyboard,
)
from .states import DealStates, LanguageStates, WalletStates


def _currency_to_balance_column(currency: str) -> str:
    if currency in {"ton", "stars"}:
        return "ton"
    return "rub"


def create_router(db: Database, settings: Settings) -> Router:
    router = Router()

    async def _load_user(user_id: int):
        user = await db.fetch_user(user_id)
        if user is None:
            ref_code = await db.generate_ref_code()
            await db.ensure_user(user_id, None, ref_code, None)
            user = await db.fetch_user(user_id)
        return user

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext, command: CommandObject | None = None) -> None:
        await state.clear()
        payload = command.args if command else None
        invited_by: Optional[int] = None
        ref_code: Optional[str] = None

        existing_user = await db.fetch_user(message.from_user.id)
        if existing_user is None:
            if payload and payload.startswith("ref_"):
                ref = payload.split("ref_", maxsplit=1)[1]
                ref_user = await db.fetch_referrer(ref)
                if ref_user and ref_user != message.from_user.id:
                    invited_by = ref_user
            ref_code = await db.generate_ref_code()
            user = await db.ensure_user(
                message.from_user.id,
                message.from_user.first_name,
                ref_code,
                invited_by,
            )
        else:
            user = existing_user

        if payload and payload.startswith("deal_"):
            token = payload.split("deal_", maxsplit=1)[1]
            await _show_buyer_view(message, token, user.language)
            return

        text = (
            "Telegram P2P Guarantee\n\n"
            f"{translate('start_description', user.language)}\n\n"
            "Выберите раздел:"
        )
        await message.answer(text, reply_markup=main_menu_keyboard(user.language))

    async def _show_buyer_view(message: Message, token: str, language: str) -> None:
        deal = await db.fetch_deal_by_token(token)
        if not deal:
            await message.answer(translate("deal_not_found", language))
            return
        seller = await db.fetch_user(deal.seller_id)
        if seller is None:
            await message.answer(translate("deal_not_found", language))
            return
        address = seller.ton_wallet if deal.currency in {"ton", "stars"} else seller.rub_wallet
        memo = deal.link_token[:6].upper()
        seller_username = message.bot.username or settings.bot_username
        text = translate(
            "buyer_view",
            language,
            seller=seller_username,
            description=deal.description,
            amount=deal.amount,
            address=address or "—",
            memo=memo,
        )
        await message.answer(text, reply_markup=buyer_keyboard(deal.link_token))

    @router.callback_query(F.data == "menu:wallets")
    async def open_wallets(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        user = await _load_user(callback.from_user.id)
        await callback.message.answer("Какой кошелёк хотите добавить/изменить?", reply_markup=wallets_menu_keyboard())
        await callback.answer()

    @router.callback_query(F.data == "wallet:ton")
    async def request_ton(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        await state.set_state(WalletStates.waiting_for_ton)
        await callback.message.answer(translate("wallet_prompt_ton", user.language))
        await callback.answer()

    @router.callback_query(F.data == "wallet:rub")
    async def request_rub(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        await state.set_state(WalletStates.waiting_for_rub)
        await callback.message.answer(translate("wallet_prompt_rub", user.language))
        await callback.answer()

    @router.message(WalletStates.waiting_for_ton)
    async def ton_entered(message: Message, state: FSMContext) -> None:
        await db.update_wallet(message.from_user.id, "ton", message.text.strip())
        user = await _load_user(message.from_user.id)
        await message.answer(translate("wallet_saved", user.language), reply_markup=main_menu_keyboard(user.language))
        await state.clear()

    @router.message(WalletStates.waiting_for_rub)
    async def rub_entered(message: Message, state: FSMContext) -> None:
        await db.update_wallet(message.from_user.id, "rub", message.text.strip())
        user = await _load_user(message.from_user.id)
        await message.answer(translate("wallet_saved", user.language), reply_markup=main_menu_keyboard(user.language))
        await state.clear()

    @router.callback_query(F.data == "wallet:balance")
    async def show_balance(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        try:
            rub_line = (
                translate("balance_wallet_rub", user.language, rub=user.rub_balance)
                if user.rub_wallet
                else translate("balance_no_wallet_rub", user.language)
            )
            text = translate("balance", user.language, ton=user.ton_balance, rub_line=rub_line)
        except Exception:
            text = translate("balance_error", user.language)
        await callback.message.answer(text)
        await callback.answer()

    @router.callback_query(F.data == "wallet:topup")
    async def show_topup(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        await callback.message.answer(translate("topup_instructions", user.language))
        await callback.answer()

    @router.callback_query(F.data == "menu:create_deal")
    async def create_deal_start(callback: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(DealStates.choosing_currency)
        await callback.message.answer("Выберите валюту сделки:", reply_markup=deal_currency_keyboard())
        await callback.answer()

    @router.callback_query(F.data.startswith("deal:"))
    async def deal_currency(callback: CallbackQuery, state: FSMContext) -> None:
        if not await state.get_state():
            await state.set_state(DealStates.choosing_currency)
        data_state = await state.get_state()
        if data_state != DealStates.choosing_currency.state:
            await callback.answer()
            return
        currency = callback.data.split(":", maxsplit=1)[1]
        await state.update_data(currency=currency)
        user = await _load_user(callback.from_user.id)
        await state.set_state(DealStates.entering_amount)
        await callback.message.answer(translate("deal_amount_prompt", user.language))
        await callback.answer()

    @router.message(DealStates.entering_amount)
    async def deal_amount_entered(message: Message, state: FSMContext) -> None:
        try:
            amount = float(message.text.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            user = await _load_user(message.from_user.id)
            await message.answer(translate("deal_amount_prompt", user.language))
            return
        await state.update_data(amount=amount)
        user = await _load_user(message.from_user.id)
        await state.set_state(DealStates.entering_description)
        await message.answer(translate("deal_description_prompt", user.language))

    @router.message(DealStates.entering_description)
    async def deal_description_entered(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        currency = data.get("currency")
        amount = data.get("amount")
        description = message.text.strip()
        user = await _load_user(message.from_user.id)
        deal = await db.create_deal(message.from_user.id, currency, amount, description)
        link = f"https://t.me/{settings.bot_username}?start=deal_{deal.link_token}"
        await message.answer(
            translate(
                "deal_created",
                user.language,
                amount=deal.amount,
                description=deal.description,
                link=link,
            ),
            reply_markup=deal_manage_keyboard(deal.link_token),
        )
        await state.clear()

    @router.callback_query(F.data.startswith("deal-cancel:"))
    async def cancel_deal(callback: CallbackQuery, state: FSMContext) -> None:
        token = callback.data.split(":", maxsplit=1)[1]
        deal = await db.fetch_deal_by_token(token)
        if not deal:
            user = await _load_user(callback.from_user.id)
            await callback.message.answer(translate("deal_not_found", user.language))
            await callback.answer()
            return
        if deal.status in {"paid", "cancelled"}:
            user = await _load_user(callback.from_user.id)
            await callback.message.answer(translate("deal_already_processed", user.language))
            await callback.answer()
            return
        await db.update_deal_status(deal.id, "cancelled")
        user = await _load_user(callback.from_user.id)
        await callback.message.answer(translate("deal_cancelled", user.language))
        await callback.answer()

    @router.callback_query(F.data == "menu:referrals")
    async def open_referrals(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        total = await db.stats_referrals(user.user_id)
        link = f"https://t.me/{settings.bot_username}?start=ref_{user.ref_code}"
        await callback.message.answer(
            translate("ref_main", user.language, total=total, link=link),
            reply_markup=referral_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data == "ref:stats")
    async def referral_stats(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        total = await db.stats_referrals(user.user_id)
        await callback.message.answer(translate("ref_stats", user.language, total=total))
        await callback.answer()

    @router.callback_query(F.data == "ref:share")
    async def referral_share(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        link = f"https://t.me/{settings.bot_username}?start=ref_{user.ref_code}"
        await callback.message.answer(translate("ref_share", user.language, link=link))
        await callback.answer()

    @router.callback_query(F.data == "menu:support")
    async def show_support(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        await callback.message.answer(translate("support", user.language))
        await callback.answer()

    @router.callback_query(F.data == "menu:language")
    async def change_language(callback: CallbackQuery, state: FSMContext) -> None:
        user = await _load_user(callback.from_user.id)
        await state.set_state(LanguageStates.choosing_language)
        await callback.message.answer(translate("language_prompt", user.language), reply_markup=language_keyboard())
        await callback.answer()

    @router.callback_query(F.data.startswith("lang:"))
    async def language_selected(callback: CallbackQuery, state: FSMContext) -> None:
        language = callback.data.split(":", maxsplit=1)[1]
        await db.update_language(callback.from_user.id, language)
        user = await _load_user(callback.from_user.id)
        await callback.message.answer("Язык обновлён!", reply_markup=main_menu_keyboard(user.language))
        await state.clear()
        await callback.answer()

    @router.callback_query(F.data == "cancel")
    async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        user = await _load_user(callback.from_user.id)
        await callback.message.answer("Главное меню", reply_markup=main_menu_keyboard(user.language))
        await callback.answer()

    @router.callback_query(F.data == "go:home")
    async def go_home(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        user = await _load_user(callback.from_user.id)
        await callback.message.answer("Главное меню", reply_markup=main_menu_keyboard(user.language))
        await callback.answer()

    async def _process_buyer_action(callback: CallbackQuery, token: str, action: str) -> None:
        user = await _load_user(callback.from_user.id)
        deal = await db.fetch_deal_by_token(token)
        if not deal:
            await callback.message.answer(translate("deal_not_found", user.language))
            await callback.answer()
            return
        if deal.status == "paid":
            await callback.message.answer(translate("deal_already_processed", user.language))
            await callback.answer()
            return
        if deal.status == "cancelled":
            await callback.message.answer(translate("deal_cancelled", user.language))
            await callback.answer()
            return
        if action == "pay":
            balance_currency = _currency_to_balance_column(deal.currency)
            success = await db.adjust_balances(
                payer_id=callback.from_user.id,
                seller_id=deal.seller_id,
                currency=balance_currency,
                amount=deal.amount,
            )
            if not success:
                await callback.message.answer(translate("insufficient_funds", user.language))
                await callback.answer()
                return
            await db.assign_buyer(deal.id, callback.from_user.id)
            await db.update_deal_status(deal.id, "paid")
            await callback.message.answer(translate("payment_success", user.language))
        else:
            await db.update_deal_status(deal.id, "cancelled")
            await callback.message.answer(translate("deal_cancelled", user.language))
        await callback.answer()

    @router.callback_query(F.data.startswith("buyer:"))
    async def buyer_actions(callback: CallbackQuery, state: FSMContext) -> None:
        _, action, token = callback.data.split(":", maxsplit=2)
        await _process_buyer_action(callback, token, action)

    @router.message()
    async def fallback(message: Message) -> None:
        user = await _load_user(message.from_user.id)
        await message.answer("Пожалуйста, используйте меню.", reply_markup=main_menu_keyboard(user.language))

    return router
