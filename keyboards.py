"""
لوحات الأزرار Inline المستخدمة في كل أنحاء البوت.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import t


def main_menu_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_channels", lang), callback_data="menu_channels"),
            InlineKeyboardButton(text=t("btn_multipost", lang), callback_data="menu_multipost"),
        ],
        [
            InlineKeyboardButton(text=t("btn_schedule", lang), callback_data="menu_schedule"),
            InlineKeyboardButton(text=t("btn_eventlog", lang), callback_data="menu_eventlog"),
        ],
        [
            InlineKeyboardButton(text=t("btn_language", lang), callback_data="menu_language"),
            InlineKeyboardButton(text=t("btn_guide", lang), callback_data="menu_guide"),
        ],
        [
            InlineKeyboardButton(text=t("btn_support", lang), callback_data="menu_support"),
        ],
    ])


def back_keyboard(lang: str = "ar", target: str = "menu_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data=target)]
    ])


def channels_list_keyboard(channels: list, lang: str = "ar",
                            select_mode: bool = False,
                            selected: set = None) -> InlineKeyboardMarkup:
    """
    قائمة القنوات. إذا select_mode=True تُستخدم لاختيار متعدد
    (تُظهر ✅ بجانب القنوات المختارة) مع زر تأكيد أسفل القائمة.
    """
    selected = selected or set()
    rows = []
    for ch in channels:
        mark = "✅ " if ch["chat_id"] in selected else ""
        prefix = "toggle_channel" if select_mode else "view_channel"
        rows.append([
            InlineKeyboardButton(
                text=f"{mark}{ch['title']}",
                callback_data=f"{prefix}_{ch['chat_id']}",
            )
        ])

    if select_mode:
        rows.append([
            InlineKeyboardButton(text="✅ " + t("btn_back", lang).split()[-1], callback_data="confirm_selection")
        ])

    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def interval_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("interval_minute", lang), callback_data="interval_minute")],
        [InlineKeyboardButton(text=t("interval_hour", lang), callback_data="interval_hour")],
        [InlineKeyboardButton(text=t("interval_day", lang), callback_data="interval_day")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_schedule")],
    ])


def toggle_edit_keyboard(lang: str, back_target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_toggle", lang), callback_data=f"{back_target}_toggle")],
        [InlineKeyboardButton(text=t("btn_edit_message", lang), callback_data=f"{back_target}_edit")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_main")],
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇸🇦 العربية", callback_data="setlang_ar"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en"),
        ],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu_main")],
    ])


def confirm_post_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ نشر الآن" if lang == "ar" else "✅ Post Now",
                               callback_data="confirm_selection")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_main")],
    ])
