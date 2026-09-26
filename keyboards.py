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
            InlineKeyboardButton(text=t("btn_gated_post", lang), callback_data="menu_gated_post"),
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


def channel_settings_menu_keyboard(chat_id: int, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_signature", lang), callback_data=f"chset_sig_{chat_id}")],
        [InlineKeyboardButton(text=t("btn_autobuttons", lang), callback_data=f"chset_btn_{chat_id}")],
        [InlineKeyboardButton(text=t("btn_crosspost", lang), callback_data=f"chset_cross_{chat_id}")],
        [InlineKeyboardButton(text=t("btn_autodelete", lang), callback_data=f"chset_del_{chat_id}")],
        [InlineKeyboardButton(text=t("btn_joinrequest", lang), callback_data=f"chset_jr_{chat_id}")],
        [InlineKeyboardButton(text=t("btn_stats", lang), callback_data=f"chset_stats_{chat_id}")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_channels")],
    ])


def toggle_only_keyboard(lang: str, callback_data: str, back_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_toggle", lang), callback_data=callback_data)],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data=back_data)],
    ])


def toggle_and_edit_keyboard(lang: str, toggle_cb: str, edit_cb: str, back_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_toggle", lang), callback_data=toggle_cb)],
        [InlineKeyboardButton(text=t("btn_edit_message", lang), callback_data=edit_cb)],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data=back_data)],
    ])


def gated_channel_choice_keyboard(channels: list, lang: str = "ar") -> InlineKeyboardMarkup:
    """قائمة اختيار القناة المطلوبة للانضمام، بمساحة أسماء مستقلة (gatedch_)
    حتى لا تتعارض مع أزرار عرض القناة العادية (view_channel_)."""
    rows = [
        [InlineKeyboardButton(text=ch["title"], callback_data=f"gatedch_{ch['chat_id']}")]
        for ch in channels
    ]
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def gated_post_delivery_keyboard(post_id: int, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("gated_button_text", lang), callback_data=f"gated_get_{post_id}")]
    ])


def gated_join_prompt_keyboard(post_id: int, invite_link: str, lang: str = "ar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("gated_join_button", lang), url=invite_link)],
        [InlineKeyboardButton(text=t("gated_check_again_button", lang), callback_data=f"gated_get_{post_id}")],
    ])
