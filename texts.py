"""
نصوص الواجهة بلغتين (عربي / إنجليزي).
استخدم t(key, lang) لجلب النص المناسب.
"""

TEXTS = {
    "welcome_dm": {
        "ar": "👋 أهلاً <b>{name}</b>!\n\nاختر أحد الأزرار بالأسفل للتحكم في البوت:",
        "en": "👋 Hello <b>{name}</b>!\n\nChoose an option below to control the bot:",
    },
    "btn_channels": {"ar": "🗂 قنواتي", "en": "🗂 My Channels"},
    "btn_multipost": {"ar": "📚 نشر متعدد", "en": "📚 Multipost"},
    "btn_schedule": {"ar": "🕒 منشور مجدول", "en": "🕒 Scheduled Post"},
    "btn_welcome": {"ar": "📲 الترحيب", "en": "📲 Welcome"},
    "btn_goodbye": {"ar": "🏃 الوداع", "en": "🏃 Goodbye"},
    "btn_joinfilter": {"ar": "🛡 فلتر الانضمام", "en": "🛡 Join Filter"},
    "btn_eventlog": {"ar": "🖥 سجل الأحداث", "en": "🖥 Event Log"},
    "btn_language": {"ar": "🌐 اللغة", "en": "🌐 Language"},
    "btn_settings": {"ar": "⚙️ الإعدادات", "en": "⚙️ Settings"},
    "btn_support": {"ar": "🔧 الدعم الفني", "en": "🔧 Support"},
    "btn_guide": {"ar": "📖 الدليل", "en": "📖 Guide"},
    "btn_back": {"ar": "⬅️ رجوع", "en": "⬅️ Back"},
    "btn_add_channel": {"ar": "➕ إضافة قناة", "en": "➕ Add Channel"},

    "no_channels": {
        "ar": "لا توجد قنوات مضافة بعد.\n\nلإضافة قناة: أضف هذا البوت كمشرف (Admin) في قناتك، "
              "ثم أرسل أي رسالة في القناة — سيتم تسجيلها تلقائياً.",
        "en": "No channels added yet.\n\nTo add one: make this bot an admin in your channel, "
              "then send any message there — it will be registered automatically.",
    },
    "channel_registered": {
        "ar": "✅ تم تسجيل القناة: {title}",
        "en": "✅ Channel registered: {title}",
    },

    "multipost_intro": {
        "ar": "✏️ أرسل الآن نص المنشور الذي تريد نشره في عدة قنوات دفعة واحدة.",
        "en": "✏️ Send the post text you want to publish to multiple channels at once.",
    },
    "multipost_choose_channels": {
        "ar": "اختر القنوات التي تريد النشر فيها (يمكنك اختيار أكثر من واحدة)، ثم اضغط ✅ نشر الآن:",
        "en": "Select the channels to post to (you can pick more than one), then press ✅ Post Now:",
    },
    "multipost_sent": {
        "ar": "✅ تم إرسال المنشور إلى {count} قناة/قنوات.",
        "en": "✅ Post sent to {count} channel(s).",
    },
    "multipost_no_selection": {
        "ar": "⚠️ اختر قناة واحدة على الأقل.",
        "en": "⚠️ Select at least one channel.",
    },

    "schedule_intro": {
        "ar": "✏️ أرسل نص المنشور الذي تريد جدولته.",
        "en": "✏️ Send the text of the post you want to schedule.",
    },
    "schedule_choose_channels": {
        "ar": "اختر القنوات المستهدفة للجدولة:",
        "en": "Select the target channels for scheduling:",
    },
    "schedule_choose_interval": {
        "ar": "كل كم مدة تريد إعادة النشر؟",
        "en": "How often should this repeat?",
    },
    "schedule_confirmed": {
        "ar": "✅ تم جدولة المنشور — سيتم نشره {interval} في {count} قناة/قنوات.",
        "en": "✅ Post scheduled — it will publish {interval} to {count} channel(s).",
    },
    "interval_minute": {"ar": "كل دقيقة", "en": "every minute"},
    "interval_hour": {"ar": "كل ساعة", "en": "every hour"},
    "interval_day": {"ar": "كل يوم", "en": "every day"},

    "welcome_menu": {
        "ar": "📲 إعدادات الترحيب لهذه المجموعة:\nالحالة: {status}\nالرسالة الحالية:\n{message}",
        "en": "📲 Welcome settings for this group:\nStatus: {status}\nCurrent message:\n{message}",
    },
    "goodbye_menu": {
        "ar": "🏃 إعدادات الوداع لهذه المجموعة:\nالحالة: {status}\nالرسالة الحالية:\n{message}",
        "en": "🏃 Goodbye settings for this group:\nStatus: {status}\nCurrent message:\n{message}",
    },
    "status_on": {"ar": "✅ مفعّل", "en": "✅ Enabled"},
    "status_off": {"ar": "❌ معطّل", "en": "❌ Disabled"},
    "btn_toggle": {"ar": "🔁 تفعيل/تعطيل", "en": "🔁 Toggle"},
    "btn_edit_message": {"ar": "✏️ تعديل الرسالة", "en": "✏️ Edit Message"},
    "ask_new_message": {
        "ar": "أرسل الرسالة الجديدة الآن. يمكنك استخدام {name} لاسم العضو و {chat} لاسم المجموعة.",
        "en": "Send the new message now. You can use {name} for member name and {chat} for group name.",
    },
    "message_updated": {"ar": "✅ تم تحديث الرسالة.", "en": "✅ Message updated."},

    "joinfilter_menu": {
        "ar": "🛡 فلتر الانضمام لهذه المجموعة:\nالحالة: {status}\n\n"
              "عند التفعيل: أي عضو جديد يجب أن يضغط زر تأكيد خلال {timeout} ثانية "
              "وإلا سيتم طرده تلقائياً (لمنع الحسابات الوهمية والسبام).",
        "en": "🛡 Join filter for this group:\nStatus: {status}\n\n"
              "When enabled: any new member must press a confirm button within {timeout} "
              "seconds or they'll be auto-kicked (blocks bots/spam accounts).",
    },
    "captcha_prompt": {
        "ar": "مرحباً {name}! اضغط الزر بالأسفل لتأكيد أنك لست بوت، خلال {timeout} ثانية.",
        "en": "Welcome {name}! Press the button below to confirm you're not a bot, within {timeout} seconds.",
    },
    "captcha_button": {"ar": "✅ أنا لست بوت", "en": "✅ I'm not a bot"},
    "captcha_passed": {"ar": "✅ تم التحقق، أهلاً بك!", "en": "✅ Verified, welcome!"},
    "captcha_not_yours": {
        "ar": "هذا الزر ليس لك 🙂",
        "en": "This button isn't for you 🙂",
    },

    "eventlog_empty": {"ar": "لا توجد أحداث مسجلة بعد.", "en": "No events logged yet."},
    "eventlog_title": {"ar": "🖥 آخر الأحداث:", "en": "🖥 Recent events:"},

    "language_menu": {
        "ar": "🌐 اختر لغة الواجهة:",
        "en": "🌐 Choose interface language:",
    },
    "language_set": {"ar": "✅ تم تغيير اللغة إلى العربية.", "en": "✅ Language switched to English."},

    "support_text": {
        "ar": "🔧 لأي استفسار أو مشكلة تقنية، تواصل مع مطور البوت مباشرة.",
        "en": "🔧 For any question or technical issue, contact the bot developer directly.",
    },
    "guide_text": {
        "ar": "📖 دليل الاستخدام:\n"
              "1. أضف البوت كمشرف في قناتك أو مجموعتك\n"
              "2. أرسل رسالة في القناة ليتم تسجيلها\n"
              "3. استخدم 'نشر متعدد' لإرسال منشور لعدة قنوات دفعة واحدة\n"
              "4. استخدم 'منشور مجدول' للنشر التلقائي المتكرر\n"
              "5. فعّل الترحيب/الوداع وفلتر الانضمام من داخل المجموعة",
        "en": "📖 Usage guide:\n"
              "1. Add the bot as admin to your channel or group\n"
              "2. Send a message in the channel to register it\n"
              "3. Use 'Multipost' to send one post to several channels at once\n"
              "4. Use 'Scheduled Post' for recurring auto-posting\n"
              "5. Enable Welcome/Goodbye and Join Filter from inside the group",
    },
    "not_admin_here": {
        "ar": "⚠️ هذا الأمر يعمل فقط داخل مجموعة، ويجب أن تكون مشرفاً فيها.",
        "en": "⚠️ This command only works inside a group, and you must be an admin there.",
    },
}


def t(key: str, lang: str = "ar", **kwargs) -> str:
    entry = TEXTS.get(key, {})
    text = entry.get(lang, entry.get("ar", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
