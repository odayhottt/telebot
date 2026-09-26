"""
بوت تيليجرام - نسخة موسّعة
المميزات: تسجيل القنوات، نشر متعدد (Multipost)، منشورات مجدولة متكررة،
ترحيب ووداع لأعضاء المجموعات، فلتر انضمام (Captcha)، سجل أحداث،
اختيار اللغة (عربي/إنجليزي)، دليل ودعم فني.
"""

import asyncio
import os
import logging
import time
import json
from datetime import datetime

from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.enums import ChatMemberStatus, ChatType

import database as db
from texts import t
import keyboards as kb

# ---------------------------------------------------------
# الإعدادات الأساسية
# ---------------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))  # Render يمرر رقم المنفذ عبر هذا المتغير

if not BOT_TOKEN:
    raise RuntimeError(
        "لم يتم العثور على BOT_TOKEN. أضف متغير بيئة باسم BOT_TOKEN يحتوي على توكن البوت."
    )

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


def lang_of(user_id: int) -> str:
    return db.get_language(user_id)


# ---------------------------------------------------------
# حالات المحادثة (FSM)
# ---------------------------------------------------------

class MultipostStates(StatesGroup):
    waiting_text = State()
    choosing_channels = State()


class ScheduleStates(StatesGroup):
    waiting_text = State()
    choosing_channels = State()
    choosing_interval = State()


class EditMessageStates(StatesGroup):
    waiting_welcome_text = State()
    waiting_goodbye_text = State()


class SignatureStates(StatesGroup):
    waiting_text = State()


class AutoButtonStates(StatesGroup):
    waiting_input = State()


class CrosspostStates(StatesGroup):
    choosing_targets = State()


class AutodeleteStates(StatesGroup):
    waiting_minutes = State()


class GatedPostStates(StatesGroup):
    waiting_content = State()
    choosing_channel = State()


# ---------------------------------------------------------
# القائمة الرئيسية
# ---------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    lang = lang_of(message.from_user.id)
    await message.answer(
        t("welcome_dm", lang, name=message.from_user.full_name),
        reply_markup=kb.main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu_main")
async def cb_menu_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = lang_of(callback.from_user.id)
    await callback.message.edit_text(
        t("welcome_dm", lang, name=callback.from_user.full_name),
        reply_markup=kb.main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu_guide")
async def cb_guide(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    await callback.message.edit_text(t("guide_text", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "menu_support")
async def cb_support(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    await callback.message.edit_text(t("support_text", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "menu_language")
async def cb_language(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    await callback.message.edit_text(t("language_menu", lang), reply_markup=kb.language_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("setlang_"))
async def cb_set_language(callback: CallbackQuery):
    new_lang = callback.data.split("_")[1]
    db.set_language(callback.from_user.id, new_lang)
    await callback.message.edit_text(
        t("language_set", new_lang),
        reply_markup=kb.main_menu_keyboard(new_lang),
    )
    await callback.answer()


# ---------------------------------------------------------
# تسجيل القنوات (عند إضافة البوت كمشرف أو عند رسالة في القناة)
# ---------------------------------------------------------

@router.channel_post()
async def on_channel_post(message: Message):
    """
    أي رسالة تُنشر في قناة يديرها البوت:
    1) تُستخدم لتسجيل القناة تلقائياً إن لم تكن مسجلة.
    2) يُطبَّق عليها التوقيع/الأزرار التلقائية إن كانت مفعّلة.
    3) تُنسخ لقنوات النشر المتبادل إن وُجدت.
    4) تُجدوَل للحذف التلقائي إن كان مفعّلاً.
    """
    chat = message.chat

    # تجاهل الرسائل التي عدّلها البوت نفسه (لإضافة التوقيع/الأزرار) لمنع التكرار
    if db.was_processed(chat.id, message.message_id):
        return
    db.mark_processed(chat.id, message.message_id)

    try:
        admins = await bot.get_chat_administrators(chat.id)
        owner_ids = [m.user.id for m in admins if m.status == ChatMemberStatus.CREATOR]
        owner_id = owner_ids[0] if owner_ids else 0
    except Exception:
        owner_id = 0

    existing = db.get_channel(chat.id)
    if not existing:
        db.add_channel(chat.id, chat.title or str(chat.id), owner_id)
        db.log_event(chat.id, "channel_registered", chat.title or "")

    cfg = db.get_channel_settings(chat.id)

    # --- التوقيع التلقائي + الأزرار التلقائية (تعديل نفس الرسالة) ---
    needs_signature = cfg["signature_enabled"] and cfg["signature_text"] and message.text
    needs_buttons = cfg["buttons_enabled"] and json.loads(cfg["buttons_json"] or "[]")

    if needs_signature or needs_buttons:
        try:
            new_text = message.text or ""
            if needs_signature:
                new_text = f"{new_text}\n\n{cfg['signature_text']}"

            markup = None
            if needs_buttons:
                buttons = json.loads(cfg["buttons_json"])
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [kb.styled_button(b["text"], url=b["url"], icon_custom_emoji_id=b.get("emoji_id"))]
                    for b in buttons
                ])

            if needs_signature:
                await bot.edit_message_text(
                    chat_id=chat.id, message_id=message.message_id,
                    text=new_text, reply_markup=markup,
                )
            elif needs_buttons:
                await bot.edit_message_reply_markup(
                    chat_id=chat.id, message_id=message.message_id, reply_markup=markup,
                )
        except Exception as e:
            logging.warning(f"فشل تعديل المنشور لإضافة التوقيع/الأزرار: {e}")

    # --- النشر المتبادل (نسخ لقنوات أخرى) ---
    targets = json.loads(cfg["crosspost_targets"] or "[]")
    for target_id in targets:
        try:
            await bot.copy_message(target_id, chat.id, message.message_id)
        except Exception as e:
            logging.warning(f"فشل النشر المتبادل إلى {target_id}: {e}")

    # --- جدولة الحذف التلقائي ---
    if cfg["autodelete_enabled"]:
        delete_at = int(time.time()) + cfg["autodelete_minutes"] * 60
        db.add_scheduled_deletion(chat.id, message.message_id, delete_at)


@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated):
    """يلتقط لحظة إضافة البوت كمشرف في قناة أو مجموعة، ويربطها بمن أضافه."""
    new_status = event.new_chat_member.status
    if new_status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER):
        if event.chat.type in (ChatType.CHANNEL, ChatType.GROUP, ChatType.SUPERGROUP):
            db.add_channel(event.chat.id, event.chat.title or str(event.chat.id), event.from_user.id)
            db.log_event(event.chat.id, "bot_added", event.chat.title or "")
    elif new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        db.remove_channel(event.chat.id)


@router.callback_query(F.data == "menu_channels")
async def cb_channels(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    channels = db.get_channels_for_user(callback.from_user.id)
    if not channels:
        await callback.message.edit_text(t("no_channels", lang), reply_markup=kb.back_keyboard(lang))
    else:
        await callback.message.edit_text(
            "🗂 " + t("btn_channels", lang),
            reply_markup=kb.channels_list_keyboard(channels, lang),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("view_channel_"))
async def cb_view_channel(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    channel = db.get_channel(chat_id)
    title = channel["title"] if channel else str(chat_id)
    await callback.message.edit_text(
        t("channel_settings_menu", lang, title=title),
        reply_markup=kb.channel_settings_menu_keyboard(chat_id, lang),
    )
    await callback.answer()


# --- التوقيع التلقائي ---

@router.callback_query(F.data.startswith("chset_sig_"))
async def cb_signature_menu(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    status = t("status_on", lang) if cfg["signature_enabled"] else t("status_off", lang)
    text = cfg["signature_text"] or t("none_set", lang)
    await callback.message.edit_text(
        t("signature_menu", lang, status=status, text=text),
        reply_markup=kb.toggle_and_edit_keyboard(
            lang, f"sigtoggle_{chat_id}", f"sigedit_{chat_id}", f"view_channel_{chat_id}"
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sigtoggle_"))
async def cb_signature_toggle(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    db.update_channel_settings(chat_id, signature_enabled=0 if cfg["signature_enabled"] else 1)
    await cb_signature_menu(callback)


@router.callback_query(F.data.startswith("sigedit_"))
async def cb_signature_edit(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    await state.update_data(target_chat_id=chat_id)
    await state.set_state(SignatureStates.waiting_text)
    await callback.message.edit_text(t("ask_signature_text", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.message(SignatureStates.waiting_text)
async def signature_receive_text(message: Message, state: FSMContext):
    data = await state.get_data()
    db.update_channel_settings(data["target_chat_id"], signature_text=message.text)
    await state.clear()
    await message.answer(t("message_updated", lang_of(message.from_user.id)))


# --- الأزرار التلقائية ---

@router.callback_query(F.data.startswith("chset_btn_"))
async def cb_autobuttons_menu(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    status = t("status_on", lang) if cfg["buttons_enabled"] else t("status_off", lang)
    buttons = json.loads(cfg["buttons_json"] or "[]")
    labels = "\n".join(f"• {b['text']}" for b in buttons) if buttons else t("none_set", lang)
    await callback.message.edit_text(
        t("autobuttons_menu", lang, status=status, count=len(buttons), labels=labels),
        reply_markup=kb.toggle_and_edit_keyboard(
            lang, f"btntoggle_{chat_id}", f"btnedit_{chat_id}", f"view_channel_{chat_id}"
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("btntoggle_"))
async def cb_autobuttons_toggle(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    db.update_channel_settings(chat_id, buttons_enabled=0 if cfg["buttons_enabled"] else 1)
    await cb_autobuttons_menu(callback)


@router.callback_query(F.data.startswith("btnedit_"))
async def cb_autobuttons_edit(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    await state.update_data(target_chat_id=chat_id, new_buttons=[])
    await state.set_state(AutoButtonStates.waiting_input)
    await callback.message.edit_text(t("ask_button_label", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


def _extract_custom_emoji_id(message: Message) -> str | None:
    """يستخرج معرّف أول إيموجي مميز (بريميوم) موجود بنص الرسالة، إن وُجد."""
    for entity in (message.entities or []):
        if entity.type == "custom_emoji" and getattr(entity, "custom_emoji_id", None):
            return entity.custom_emoji_id
    return None


@router.message(AutoButtonStates.waiting_input)
async def autobuttons_receive_input(message: Message, state: FSMContext):
    lang = lang_of(message.from_user.id)
    if not message.text or "|" not in message.text:
        await message.answer(t("invalid_button_format", lang))
        return

    label, url = message.text.split("|", 1)
    label, url = label.strip(), url.strip()
    if url.startswith("t.me/") or url.startswith("www.t.me/"):
        url = "https://" + url
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(t("invalid_button_format", lang))
        return

    emoji_id = _extract_custom_emoji_id(message)

    data = await state.get_data()
    new_buttons = list(data.get("new_buttons", []))
    new_buttons.append({"text": label, "url": url, "emoji_id": emoji_id})
    await state.update_data(new_buttons=new_buttons)

    await message.answer(
        t("button_added", lang, count=len(new_buttons)),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [kb.styled_button(t("btn_save_buttons", lang), callback_data="autobtn_finish", style="success")],
            [kb.styled_button(t("btn_cancel_all", lang), callback_data="autobtn_cancel_all", style="danger")],
        ]),
    )


@router.callback_query(AutoButtonStates.waiting_input, F.data == "autobtn_finish")
async def cb_autobuttons_finish(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    data = await state.get_data()
    new_buttons = data.get("new_buttons", [])

    if not new_buttons:
        await callback.answer(t("buttons_need_at_least_one", lang), show_alert=True)
        return

    db.update_channel_settings(data["target_chat_id"], buttons_json=json.dumps(new_buttons))
    await state.clear()
    await callback.message.edit_text(
        t("buttons_saved", lang, count=len(new_buttons)), reply_markup=kb.back_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(AutoButtonStates.waiting_input, F.data == "autobtn_cancel_all")
async def cb_autobuttons_cancel(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(t("buttons_cancelled", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


# --- النشر المتبادل ---

@router.callback_query(F.data.startswith("chset_cross_"))
async def cb_crosspost_menu(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    target_ids = json.loads(cfg["crosspost_targets"] or "[]")
    all_channels = db.get_channels_for_user(callback.from_user.id)
    names = [c["title"] for c in all_channels if c["chat_id"] in target_ids]
    targets_text = "\n".join(f"• {n}" for n in names) if names else t("none_set", lang)

    await callback.message.edit_text(
        t("crosspost_menu", lang, targets=targets_text),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=t("btn_crosspost", lang), callback_data=f"crosschoose_{chat_id}"
            )],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"view_channel_{chat_id}")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("crosschoose_"))
async def cb_crosspost_choose(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    source_chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(source_chat_id)
    current_targets = set(json.loads(cfg["crosspost_targets"] or "[]"))

    await state.update_data(source_chat_id=source_chat_id, selected=current_targets)
    await state.set_state(CrosspostStates.choosing_targets)

    all_channels = [c for c in db.get_channels_for_user(callback.from_user.id) if c["chat_id"] != source_chat_id]
    await callback.message.edit_text(
        t("crosspost_choose", lang),
        reply_markup=kb.channels_list_keyboard(all_channels, lang, select_mode=True, selected=current_targets),
    )
    await callback.answer()


@router.callback_query(CrosspostStates.choosing_targets, F.data.startswith("toggle_channel_"))
async def cb_crosspost_toggle(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = set(data.get("selected", set()))
    selected.symmetric_difference_update({chat_id})
    await state.update_data(selected=selected)

    lang = lang_of(callback.from_user.id)
    all_channels = [c for c in db.get_channels_for_user(callback.from_user.id)
                     if c["chat_id"] != data["source_chat_id"]]
    await callback.message.edit_reply_markup(
        reply_markup=kb.channels_list_keyboard(all_channels, lang, select_mode=True, selected=selected)
    )
    await callback.answer()


@router.callback_query(CrosspostStates.choosing_targets, F.data == "confirm_selection")
async def cb_crosspost_confirm(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    data = await state.get_data()
    db.update_channel_settings(
        data["source_chat_id"], crosspost_targets=json.dumps(list(data.get("selected", set())))
    )
    await state.clear()
    await callback.message.edit_text(t("crosspost_saved", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


# --- الحذف التلقائي ---

@router.callback_query(F.data.startswith("chset_del_"))
async def cb_autodelete_menu(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    status = t("status_on", lang) if cfg["autodelete_enabled"] else t("status_off", lang)
    await callback.message.edit_text(
        t("autodelete_menu", lang, status=status, minutes=cfg["autodelete_minutes"]),
        reply_markup=kb.toggle_and_edit_keyboard(
            lang, f"deltoggle_{chat_id}", f"deledit_{chat_id}", f"view_channel_{chat_id}"
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("deltoggle_"))
async def cb_autodelete_toggle(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    db.update_channel_settings(chat_id, autodelete_enabled=0 if cfg["autodelete_enabled"] else 1)
    await cb_autodelete_menu(callback)


@router.callback_query(F.data.startswith("deledit_"))
async def cb_autodelete_edit(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    await state.update_data(target_chat_id=chat_id)
    await state.set_state(AutodeleteStates.waiting_minutes)
    await callback.message.edit_text(t("ask_autodelete_minutes", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.message(AutodeleteStates.waiting_minutes)
async def autodelete_receive_minutes(message: Message, state: FSMContext):
    lang = lang_of(message.from_user.id)
    if not message.text.strip().isdigit():
        await message.answer(t("invalid_number", lang))
        return
    minutes = int(message.text.strip())
    data = await state.get_data()
    db.update_channel_settings(data["target_chat_id"], autodelete_minutes=minutes)
    await state.clear()
    await message.answer(t("message_updated", lang))


# --- الموافقة التلقائية على طلبات الانضمام ---

@router.callback_query(F.data.startswith("chset_jr_"))
async def cb_joinrequest_menu(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    status = t("status_on", lang) if cfg["joinrequest_autoapprove"] else t("status_off", lang)
    await callback.message.edit_text(
        t("joinrequest_menu", lang, status=status),
        reply_markup=kb.toggle_only_keyboard(lang, f"jrtoggle_{chat_id}", f"view_channel_{chat_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("jrtoggle_"))
async def cb_joinrequest_toggle(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[-1])
    cfg = db.get_channel_settings(chat_id)
    db.update_channel_settings(chat_id, joinrequest_autoapprove=0 if cfg["joinrequest_autoapprove"] else 1)
    await cb_joinrequest_menu(callback)


@router.chat_join_request()
async def on_chat_join_request(update):
    cfg = db.get_channel_settings(update.chat.id)
    if cfg["joinrequest_autoapprove"]:
        try:
            await bot.approve_chat_join_request(update.chat.id, update.from_user.id)
            db.log_event(update.chat.id, "join_request_approved", update.from_user.full_name)
        except Exception as e:
            logging.warning(f"فشل قبول طلب الانضمام: {e}")


# --- نمو المشتركين ---

@router.callback_query(F.data.startswith("chset_stats_"))
async def cb_stats(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    chat_id = int(callback.data.split("_")[-1])
    history = db.get_subscriber_history(chat_id, limit=2)

    if not history:
        await callback.message.edit_text(
            t("stats_no_data", lang),
            reply_markup=kb.back_keyboard(lang, target=f"view_channel_{chat_id}"),
        )
        await callback.answer()
        return

    current = history[0]["member_count"]
    previous = history[1]["member_count"] if len(history) > 1 else current
    channel = db.get_channel(chat_id)
    title = channel["title"] if channel else str(chat_id)

    await callback.message.edit_text(
        t("stats_result", lang, title=title, current=current, previous=previous, diff=current - previous),
        reply_markup=kb.back_keyboard(lang, target=f"view_channel_{chat_id}"),
    )
    await callback.answer()


# ---------------------------------------------------------
# النشر المتعدد (Multipost)
# ---------------------------------------------------------

@router.callback_query(F.data == "menu_multipost")
async def cb_multipost_start(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    channels = db.get_channels_for_user(callback.from_user.id)
    if not channels:
        await callback.message.edit_text(t("no_channels", lang), reply_markup=kb.back_keyboard(lang))
        await callback.answer()
        return
    await state.set_state(MultipostStates.waiting_text)
    await callback.message.edit_text(t("multipost_intro", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.message(MultipostStates.waiting_text)
async def multipost_receive_text(message: Message, state: FSMContext):
    lang = lang_of(message.from_user.id)
    await state.update_data(post_text=message.text, selected=set())
    channels = db.get_channels_for_user(message.from_user.id)
    await state.set_state(MultipostStates.choosing_channels)
    await message.answer(
        t("multipost_choose_channels", lang),
        reply_markup=kb.channels_list_keyboard(channels, lang, select_mode=True, selected=set()),
    )


@router.callback_query(MultipostStates.choosing_channels, F.data.startswith("toggle_channel_"))
async def multipost_toggle_channel(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = set(data.get("selected", set()))
    selected.symmetric_difference_update({chat_id})
    await state.update_data(selected=selected)

    lang = lang_of(callback.from_user.id)
    channels = db.get_channels_for_user(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=kb.channels_list_keyboard(channels, lang, select_mode=True, selected=selected)
    )
    await callback.answer()


@router.callback_query(MultipostStates.choosing_channels, F.data == "confirm_selection")
async def multipost_confirm(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    data = await state.get_data()
    selected = data.get("selected", set())
    post_text = data.get("post_text", "")

    if not selected:
        await callback.answer(t("multipost_no_selection", lang), show_alert=True)
        return

    sent = 0
    for chat_id in selected:
        try:
            await bot.send_message(chat_id, post_text)
            sent += 1
        except Exception as e:
            logging.warning(f"فشل الإرسال إلى {chat_id}: {e}")

    await state.clear()
    await callback.message.edit_text(
        t("multipost_sent", lang, count=sent),
        reply_markup=kb.back_keyboard(lang),
    )
    await callback.answer()


# ---------------------------------------------------------
# المنشورات المجدولة (Scheduled / Recurring Posts)
# ---------------------------------------------------------

@router.callback_query(F.data == "menu_schedule")
async def cb_schedule_start(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    channels = db.get_channels_for_user(callback.from_user.id)
    if not channels:
        await callback.message.edit_text(t("no_channels", lang), reply_markup=kb.back_keyboard(lang))
        await callback.answer()
        return
    await state.set_state(ScheduleStates.waiting_text)
    await callback.message.edit_text(t("schedule_intro", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.message(ScheduleStates.waiting_text)
async def schedule_receive_text(message: Message, state: FSMContext):
    lang = lang_of(message.from_user.id)
    await state.update_data(post_text=message.text, selected=set())
    channels = db.get_channels_for_user(message.from_user.id)
    await state.set_state(ScheduleStates.choosing_channels)
    await message.answer(
        t("schedule_choose_channels", lang),
        reply_markup=kb.channels_list_keyboard(channels, lang, select_mode=True, selected=set()),
    )


@router.callback_query(ScheduleStates.choosing_channels, F.data.startswith("toggle_channel_"))
async def schedule_toggle_channel(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = set(data.get("selected", set()))
    selected.symmetric_difference_update({chat_id})
    await state.update_data(selected=selected)

    lang = lang_of(callback.from_user.id)
    channels = db.get_channels_for_user(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=kb.channels_list_keyboard(channels, lang, select_mode=True, selected=selected)
    )
    await callback.answer()


@router.callback_query(ScheduleStates.choosing_channels, F.data == "confirm_selection")
async def schedule_channels_confirmed(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    data = await state.get_data()
    if not data.get("selected"):
        await callback.answer(t("multipost_no_selection", lang), show_alert=True)
        return
    await state.set_state(ScheduleStates.choosing_interval)
    await callback.message.edit_text(
        t("schedule_choose_interval", lang), reply_markup=kb.interval_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(ScheduleStates.choosing_interval, F.data.startswith("interval_"))
async def schedule_interval_chosen(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    interval_type = callback.data.split("_")[1]  # minute / hour / day
    seconds_map = {"minute": 60, "hour": 3600, "day": 86400}
    interval_seconds = seconds_map[interval_type]

    data = await state.get_data()
    selected = list(data.get("selected", set()))
    post_text = data.get("post_text", "")

    next_run = int(time.time()) + interval_seconds
    db.add_scheduled_post(
        owner_id=callback.from_user.id,
        chat_ids=selected,
        text=post_text,
        interval_type=interval_type,
        interval_value=interval_seconds,
        next_run=next_run,
    )

    await state.clear()
    await callback.message.edit_text(
        t("schedule_confirmed", lang, interval=t(f"interval_{interval_type}", lang), count=len(selected)),
        reply_markup=kb.back_keyboard(lang),
    )
    await callback.answer()


# ---------------------------------------------------------
# الترحيب والوداع (تعمل داخل المجموعات)
# ---------------------------------------------------------

async def is_group_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR)
    except Exception:
        return False


@router.message(Command("welcome"))
async def cmd_welcome(message: Message):
    lang = lang_of(message.from_user.id)
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.answer(t("not_admin_here", lang))
        return
    if not await is_group_admin(message.chat.id, message.from_user.id):
        await message.answer(t("not_admin_here", lang))
        return

    cfg = db.get_welcome(message.chat.id)
    status = t("status_on", lang) if cfg["enabled"] else t("status_off", lang)
    await message.answer(
        t("welcome_menu", lang, status=status, message=cfg["message"]),
        reply_markup=kb.toggle_edit_keyboard(lang, "welcome"),
    )


@router.message(Command("goodbye"))
async def cmd_goodbye(message: Message):
    lang = lang_of(message.from_user.id)
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.answer(t("not_admin_here", lang))
        return
    if not await is_group_admin(message.chat.id, message.from_user.id):
        await message.answer(t("not_admin_here", lang))
        return

    cfg = db.get_goodbye(message.chat.id)
    status = t("status_on", lang) if cfg["enabled"] else t("status_off", lang)
    await message.answer(
        t("goodbye_menu", lang, status=status, message=cfg["message"]),
        reply_markup=kb.toggle_edit_keyboard(lang, "goodbye"),
    )


@router.message(Command("joinfilter"))
async def cmd_joinfilter(message: Message):
    lang = lang_of(message.from_user.id)
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.answer(t("not_admin_here", lang))
        return
    if not await is_group_admin(message.chat.id, message.from_user.id):
        await message.answer(t("not_admin_here", lang))
        return

    cfg = db.get_joinfilter(message.chat.id)
    status = t("status_on", lang) if cfg["enabled"] else t("status_off", lang)
    await message.answer(
        t("joinfilter_menu", lang, status=status, timeout=cfg["timeout_seconds"]),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_toggle", lang), callback_data="joinfilter_toggle")],
        ]),
    )


@router.callback_query(F.data == "welcome_toggle")
async def cb_welcome_toggle(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    cfg = db.get_welcome(callback.message.chat.id)
    db.set_welcome(callback.message.chat.id, enabled=not cfg["enabled"])
    cfg = db.get_welcome(callback.message.chat.id)
    status = t("status_on", lang) if cfg["enabled"] else t("status_off", lang)
    await callback.message.edit_text(
        t("welcome_menu", lang, status=status, message=cfg["message"]),
        reply_markup=kb.toggle_edit_keyboard(lang, "welcome"),
    )
    await callback.answer()


@router.callback_query(F.data == "goodbye_toggle")
async def cb_goodbye_toggle(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    cfg = db.get_goodbye(callback.message.chat.id)
    db.set_goodbye(callback.message.chat.id, enabled=not cfg["enabled"])
    cfg = db.get_goodbye(callback.message.chat.id)
    status = t("status_on", lang) if cfg["enabled"] else t("status_off", lang)
    await callback.message.edit_text(
        t("goodbye_menu", lang, status=status, message=cfg["message"]),
        reply_markup=kb.toggle_edit_keyboard(lang, "goodbye"),
    )
    await callback.answer()


@router.callback_query(F.data == "joinfilter_toggle")
async def cb_joinfilter_toggle(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    cfg = db.get_joinfilter(callback.message.chat.id)
    db.set_joinfilter(callback.message.chat.id, enabled=not cfg["enabled"])
    cfg = db.get_joinfilter(callback.message.chat.id)
    status = t("status_on", lang) if cfg["enabled"] else t("status_off", lang)
    await callback.message.edit_text(
        t("joinfilter_menu", lang, status=status, timeout=cfg["timeout_seconds"]),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_toggle", lang), callback_data="joinfilter_toggle")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "welcome_edit")
async def cb_welcome_edit(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    await state.update_data(target_chat_id=callback.message.chat.id)
    await state.set_state(EditMessageStates.waiting_welcome_text)
    await callback.message.edit_text(t("ask_new_message", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "goodbye_edit")
async def cb_goodbye_edit(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    await state.update_data(target_chat_id=callback.message.chat.id)
    await state.set_state(EditMessageStates.waiting_goodbye_text)
    await callback.message.edit_text(t("ask_new_message", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.message(EditMessageStates.waiting_welcome_text)
async def welcome_new_text(message: Message, state: FSMContext):
    data = await state.get_data()
    db.set_welcome(data["target_chat_id"], message=message.text)
    await state.clear()
    await message.answer(t("message_updated", lang_of(message.from_user.id)))


@router.message(EditMessageStates.waiting_goodbye_text)
async def goodbye_new_text(message: Message, state: FSMContext):
    data = await state.get_data()
    db.set_goodbye(data["target_chat_id"], message=message.text)
    await state.clear()
    await message.answer(t("message_updated", lang_of(message.from_user.id)))


# ---------------------------------------------------------
# استقبال انضمام/مغادرة الأعضاء (ترحيب، وداع، فلتر انضمام)
# ---------------------------------------------------------

@router.chat_member()
async def on_chat_member_update(event: ChatMemberUpdated):
    chat = event.chat
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    user = event.new_chat_member.user

    if user.is_bot:
        return

    joined = old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED) and \
        new_status == ChatMemberStatus.MEMBER
    left = old_status == ChatMemberStatus.MEMBER and \
        new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)

    if joined:
        db.log_event(chat.id, "member_joined", user.full_name)

        join_cfg = db.get_joinfilter(chat.id)
        if join_cfg["enabled"]:
            timeout = join_cfg["timeout_seconds"]
            try:
                # كتم العضو مؤقتاً لحين تأكيد أنه ليس بوت
                await bot.restrict_chat_member(
                    chat.id, user.id,
                    permissions={"can_send_messages": False},
                )
            except Exception:
                pass

            deadline = int(time.time()) + timeout
            db.add_pending_captcha(chat.id, user.id, deadline)

            lang = lang_of(user.id)
            await bot.send_message(
                chat.id,
                t("captcha_prompt", lang, name=user.full_name, timeout=timeout),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    kb.styled_button(
                        t("captcha_button", lang),
                        callback_data=f"captcha_ok_{user.id}",
                        style="success",
                    )
                ]]),
            )

        welcome_cfg = db.get_welcome(chat.id)
        if welcome_cfg["enabled"]:
            text = welcome_cfg["message"].format(name=user.full_name, chat=chat.title or "")
            await bot.send_message(chat.id, text)

    elif left:
        db.log_event(chat.id, "member_left", user.full_name)
        goodbye_cfg = db.get_goodbye(chat.id)
        if goodbye_cfg["enabled"]:
            text = goodbye_cfg["message"].format(name=user.full_name, chat=chat.title or "")
            await bot.send_message(chat.id, text)


@router.callback_query(F.data.startswith("captcha_ok_"))
async def cb_captcha_ok(callback: CallbackQuery):
    target_user_id = int(callback.data.split("_")[-1])
    lang = lang_of(callback.from_user.id)

    if callback.from_user.id != target_user_id:
        await callback.answer(t("captcha_not_yours", lang), show_alert=True)
        return

    chat_id = callback.message.chat.id
    try:
        await bot.restrict_chat_member(
            chat_id, target_user_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
            },
        )
    except Exception:
        pass

    db.remove_pending_captcha(chat_id, target_user_id)
    await callback.message.edit_text(t("captcha_passed", lang))
    await callback.answer()


# ---------------------------------------------------------
# منشور مشروط بالانضمام (Join-gated post)
# ---------------------------------------------------------

@router.callback_query(F.data == "menu_gated_post")
async def cb_gated_post_start(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    channels = db.get_channels_for_user(callback.from_user.id)
    if not channels:
        await callback.message.edit_text(t("no_channels", lang), reply_markup=kb.back_keyboard(lang))
        await callback.answer()
        return
    await state.set_state(GatedPostStates.waiting_content)
    await callback.message.edit_text(t("gated_intro", lang), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


@router.message(GatedPostStates.waiting_content)
async def gated_receive_content(message: Message, state: FSMContext):
    lang = lang_of(message.from_user.id)
    await state.update_data(content_text=message.text)
    channels = db.get_channels_for_user(message.from_user.id)
    await state.set_state(GatedPostStates.choosing_channel)
    await message.answer(
        t("gated_choose_channel", lang),
        reply_markup=kb.gated_channel_choice_keyboard(channels, lang),
    )


@router.callback_query(GatedPostStates.choosing_channel, F.data.startswith("gatedch_"))
async def gated_channel_chosen(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    required_chat_id = int(callback.data.split("_")[-1])

    try:
        invite = await bot.create_chat_invite_link(required_chat_id, member_limit=None)
        invite_link = invite.invite_link
    except Exception as e:
        logging.warning(f"فشل إنشاء رابط دعوة: {e}")
        await callback.message.edit_text(t("gated_no_invite_link", lang), reply_markup=kb.back_keyboard(lang))
        await state.clear()
        await callback.answer()
        return

    data = await state.get_data()
    post_id = db.add_gated_post(
        owner_id=callback.from_user.id,
        content_text=data["content_text"],
        required_chat_id=required_chat_id,
        invite_link=invite_link,
    )
    await state.clear()

    await callback.message.edit_text(t("gated_created", lang), reply_markup=kb.back_keyboard(lang))
    await callback.message.answer(
        "🔒 " + (data["content_text"][:60] + "..." if len(data["content_text"]) > 60 else data["content_text"]),
        reply_markup=kb.gated_post_delivery_keyboard(post_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gated_get_"))
async def cb_gated_get_content(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    post_id = int(callback.data.split("_")[-1])
    post = db.get_gated_post(post_id)
    if not post:
        await callback.answer()
        return

    try:
        member = await bot.get_chat_member(post["required_chat_id"], callback.from_user.id)
        is_member = member.status in (
            ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR
        )
    except Exception:
        is_member = False

    if is_member:
        await callback.answer()
        await bot.send_message(callback.from_user.id, post["content_text"])
    else:
        await callback.answer(t("gated_not_member", lang), show_alert=True)
        try:
            await callback.message.edit_reply_markup(
                reply_markup=kb.gated_join_prompt_keyboard(post_id, post["invite_link"], lang)
            )
        except Exception:
            pass


# ---------------------------------------------------------
# سجل الأحداث
# ---------------------------------------------------------

@router.callback_query(F.data == "menu_eventlog")
async def cb_eventlog(callback: CallbackQuery):
    lang = lang_of(callback.from_user.id)
    events = db.get_recent_events(limit=15)
    if not events:
        await callback.message.edit_text(t("eventlog_empty", lang), reply_markup=kb.back_keyboard(lang))
        await callback.answer()
        return

    lines = [t("eventlog_title", lang)]
    for e in events:
        when = datetime.fromtimestamp(e["created_at"]).strftime("%Y-%m-%d %H:%M")
        lines.append(f"• [{when}] {e['event_type']} — {e['details']}")

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.back_keyboard(lang))
    await callback.answer()


# ---------------------------------------------------------
# مهمة خلفية: تنفيذ المنشورات المجدولة + طرد من لم يجتز الكابتشا
# ---------------------------------------------------------

_last_stats_run = 0  # آخر مرة سُجلت فيها إحصائيات المشتركين (بالثواني)
STATS_INTERVAL_SECONDS = 3600  # تسجيل عدد المشتركين كل ساعة تقريباً


async def background_scheduler():
    global _last_stats_run
    while True:
        now = int(time.time())

        # المنشورات المجدولة المستحقة
        for post in db.get_due_posts(now):
            chat_ids = json.loads(post["chat_ids"])
            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id, post["text"])
                except Exception as e:
                    logging.warning(f"فشل نشر المنشور المجدول في {chat_id}: {e}")
            db.update_next_run(post["id"], now + post["interval_value"])

        # الأعضاء الذين لم يضغطوا زر الكابتشا في الوقت المحدد
        for pending in db.get_expired_captchas(now):
            chat_id, user_id = pending["chat_id"], pending["user_id"]
            try:
                await bot.ban_chat_member(chat_id, user_id)
                await bot.unban_chat_member(chat_id, user_id)  # طرد بدون حظر دائم
                db.log_event(chat_id, "captcha_timeout_kick", str(user_id))
            except Exception:
                pass
            db.remove_pending_captcha(chat_id, user_id)

        # حذف المنشورات المستحقة للحذف التلقائي
        for deletion in db.get_due_deletions(now):
            try:
                await bot.delete_message(deletion["chat_id"], deletion["message_id"])
            except Exception:
                pass
            db.remove_scheduled_deletion(deletion["id"])

        # تسجيل عدد المشتركين دورياً لكل قناة مسجلة
        if now - _last_stats_run >= STATS_INTERVAL_SECONDS:
            _last_stats_run = now
            with db.get_conn() as conn:
                all_channels = [dict(r) for r in conn.execute("SELECT chat_id FROM channels").fetchall()]
            for ch in all_channels:
                try:
                    count = await bot.get_chat_member_count(ch["chat_id"])
                    db.record_subscriber_count(ch["chat_id"], count)
                except Exception:
                    pass

        await asyncio.sleep(15)


# ---------------------------------------------------------
# سيرفر HTTP بسيط لإبقاء الخدمة حية على Render (Web Service)
# ---------------------------------------------------------

async def handle_health(request):
    return web.Response(text="Bot is running.")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"HTTP keep-alive server running on port {PORT}")


# ---------------------------------------------------------
# نقطة التشغيل
# ---------------------------------------------------------

async def main():
    db.init_db()
    await start_web_server()
    asyncio.create_task(background_scheduler())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
