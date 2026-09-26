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

    "btn_channel_settings": {"ar": "⚙️ إعدادات القناة", "en": "⚙️ Channel Settings"},
    "channel_settings_menu": {
        "ar": "⚙️ إعدادات قناة: {title}\n\nاختر ميزة لضبطها:",
        "en": "⚙️ Settings for: {title}\n\nChoose a feature to configure:",
    },
    "btn_signature": {"ar": "✍️ التوقيع التلقائي", "en": "✍️ Auto-signature"},
    "btn_autobuttons": {"ar": "🔘 الأزرار التلقائية", "en": "🔘 Auto-buttons"},
    "btn_crosspost": {"ar": "🔁 النشر المتبادل", "en": "🔁 Cross-posting"},
    "btn_autodelete": {"ar": "🗑 الحذف التلقائي", "en": "🗑 Auto-delete"},
    "btn_joinrequest": {"ar": "✅ الموافقة التلقائية", "en": "✅ Auto-approve requests"},
    "btn_stats": {"ar": "📈 نمو المشتركين", "en": "📈 Subscriber growth"},

    "signature_menu": {
        "ar": "✍️ التوقيع التلقائي\nالحالة: {status}\nالنص الحالي:\n{text}\n\n"
              "سيُضاف هذا النص تلقائياً في نهاية كل منشور جديد بالقناة.",
        "en": "✍️ Auto-signature\nStatus: {status}\nCurrent text:\n{text}\n\n"
              "This text will be appended automatically to every new post in the channel.",
    },
    "ask_signature_text": {
        "ar": "أرسل نص التوقيع الذي تريد إضافته تلقائياً بنهاية كل منشور:",
        "en": "Send the signature text to append automatically to every post:",
    },

    "autobuttons_menu": {
        "ar": "🔘 الأزرار التلقائية\nالحالة: {status}\nالأزرار الحالية ({count}):\n{labels}\n\n"
              "ستُضاف هذي الأزرار تلقائياً تحت كل منشور جديد بالقناة.",
        "en": "🔘 Auto-buttons\nStatus: {status}\nCurrent buttons ({count}):\n{labels}\n\n"
              "These buttons will be added automatically under every new post.",
    },
    "ask_button_label": {
        "ar": "أرسل الزر الأول: النص ثم الرابط، مفصولين بـ |\n"
              "مثال:\nتابعنا على يوتيوب|https://youtube.com/@اسمك\n\n"
              "✨ عندك اشتراك بريميوم؟ ضيف إيموجي مميز بأول النص وراح يظهر بجانب الزر تلقائياً.\n\n"
              "بعد كل زر ترسله، تقدر ترسل زر إضافي أو تضغط "
              "\"✅ تم الحفظ\" لإنهاء الإضافة — أرسل بأي عدد من الأزرار تبيه.",
        "en": "Send the first button: text then URL, separated by |\n"
              "Example:\nFollow on YouTube|https://youtube.com/@you\n\n"
              "✨ Have Premium? Add a custom emoji at the start of the text and it'll show next to the button automatically.\n\n"
              "After each button, send another one or press \"✅ Save\" to finish — add as many buttons as you like.",
    },
    "button_added": {
        "ar": "✅ تمت إضافة الزر ({count} زر حتى الآن).\nأرسل زر إضافي، أو اضغط \"✅ تم الحفظ\".",
        "en": "✅ Button added ({count} so far).\nSend another one, or press \"✅ Save\".",
    },
    "btn_save_buttons": {"ar": "✅ تم الحفظ", "en": "✅ Save"},
    "btn_cancel_all": {"ar": "❌ إلغاء الكل", "en": "❌ Cancel all"},
    "buttons_saved": {"ar": "✅ تم حفظ {count} زر بنجاح.", "en": "✅ Saved {count} button(s)."},
    "buttons_cancelled": {"ar": "تم إلغاء الإضافة.", "en": "Cancelled."},
    "buttons_need_at_least_one": {
        "ar": "⚠️ أضف زر واحد على الأقل قبل الحفظ.",
        "en": "⚠️ Add at least one button before saving.",
    },
    "invalid_button_format": {
        "ar": "⚠️ الصيغة غير صحيحة. استخدم: النص|الرابط",
        "en": "⚠️ Invalid format. Use: text|url",
    },
    "none_set": {"ar": "لا يوجد", "en": "none"},

    "crosspost_menu": {
        "ar": "🔁 النشر المتبادل\nأي منشور جديد بهذه القناة يُنسخ تلقائياً للقنوات التالية:\n{targets}",
        "en": "🔁 Cross-posting\nAny new post here is automatically copied to:\n{targets}",
    },
    "crosspost_choose": {
        "ar": "اختر القنوات الهدف (تُنسخ لها المنشورات تلقائياً)، ثم اضغط تأكيد:",
        "en": "Select target channels (posts will be copied there automatically), then confirm:",
    },
    "crosspost_saved": {"ar": "✅ تم حفظ إعدادات النشر المتبادل.", "en": "✅ Cross-posting settings saved."},

    "autodelete_menu": {
        "ar": "🗑 الحذف التلقائي\nالحالة: {status}\nيُحذف كل منشور جديد بعد: {minutes} دقيقة",
        "en": "🗑 Auto-delete\nStatus: {status}\nEach new post is deleted after: {minutes} minutes",
    },
    "ask_autodelete_minutes": {
        "ar": "أرسل عدد الدقائق التي يبقى بعدها المنشور قبل حذفه تلقائياً (رقم فقط):",
        "en": "Send the number of minutes a post should stay before auto-deletion (number only):",
    },
    "invalid_number": {"ar": "⚠️ أرسل رقماً صحيحاً.", "en": "⚠️ Please send a valid number."},

    "joinrequest_menu": {
        "ar": "✅ الموافقة التلقائية على طلبات الانضمام\nالحالة: {status}\n\n"
              "عند التفعيل: أي شخص يطلب الانضمام لقناتك الخاصة تتم الموافقة عليه تلقائياً وفوراً.",
        "en": "✅ Auto-approve join requests\nStatus: {status}\n\n"
              "When enabled: anyone requesting to join your private channel is approved instantly.",
    },

    "stats_no_data": {
        "ar": "لا توجد بيانات كافية بعد. البوت يسجل عدد المشتركين تلقائياً كل ساعة تقريباً — راجع لاحقاً.",
        "en": "Not enough data yet. The bot records subscriber count roughly hourly — check back later.",
    },
    "stats_result": {
        "ar": "📈 نمو المشتركين — {title}\nالعدد الحالي: {current}\nالعدد السابق: {previous}\nالتغيّر: {diff}",
        "en": "📈 Subscriber growth — {title}\nCurrent: {current}\nPrevious: {previous}\nChange: {diff}",
    },

    "btn_gated_post": {"ar": "🔒 منشور مشروط بالانضمام", "en": "🔒 Join-gated Post"},
    "gated_intro": {
        "ar": "✏️ أرسل المحتوى الذي تريد تسليمه فقط لمن ينضم لقناة معينة أولاً "
              "(نص، أو رابط، أو أي شيء تريد إرساله).",
        "en": "✏️ Send the content that should only be delivered to those who first join a specific channel.",
    },
    "gated_choose_channel": {
        "ar": "اختر القناة الخاصة التي يجب على المستخدم الانضمام لها أولاً:",
        "en": "Select the private channel the user must join first:",
    },
    "gated_no_invite_link": {
        "ar": "⚠️ تعذّر إنشاء رابط دعوة لهذه القناة. تأكد أن البوت مشرف بصلاحية دعوة المستخدمين.",
        "en": "⚠️ Couldn't create an invite link for this channel. Make sure the bot is admin with invite permission.",
    },
    "gated_created": {
        "ar": "✅ تم إنشاء المنشور المشروط. انسخ الرسالة التالية وانشرها أينما تريد:",
        "en": "✅ Join-gated post created. Copy the message below and share it anywhere:",
    },
    "gated_button_text": {"ar": "🔓 احصل على المحتوى", "en": "🔓 Get the content"},
    "gated_not_member": {
        "ar": "⚠️ يجب عليك الانضمام للقناة أولاً، ثم اضغط الزر مرة أخرى.",
        "en": "⚠️ You must join the channel first, then press the button again.",
    },
    "gated_join_button": {"ar": "📢 انضم للقناة", "en": "📢 Join channel"},
    "gated_check_again_button": {"ar": "🔄 تحقق مرة أخرى", "en": "🔄 Check again"},
}


def t(key: str, lang: str = "ar", **kwargs) -> str:
    entry = TEXTS.get(key, {})
    text = entry.get(lang, entry.get("ar", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
