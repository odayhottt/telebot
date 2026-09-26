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
    """أي رسالة تُنشر في قناة يديرها البوت تُستخدم لتسجيل القناة تلقائياً."""
    chat = message.chat
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
    await callback.message.edit_text(t("ask_new_message", lang))
    await callback.answer()


@router.callback_query(F.data == "goodbye_edit")
async def cb_goodbye_edit(callback: CallbackQuery, state: FSMContext):
    lang = lang_of(callback.from_user.id)
    await state.update_data(target_chat_id=callback.message.chat.id)
    await state.set_state(EditMessageStates.waiting_goodbye_text)
    await callback.message.edit_text(t("ask_new_message", lang))
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
                    InlineKeyboardButton(
                        text=t("captcha_button", lang),
                        callback_data=f"captcha_ok_{user.id}",
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

async def background_scheduler():
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
