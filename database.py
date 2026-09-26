"""
طبقة قاعدة البيانات - SQLite
تخزن: القنوات المسجلة، رسائل الترحيب/الوداع، فلتر الانضمام،
المنشورات المجدولة، إعدادات اللغة لكل مستخدم.
"""

import sqlite3
import json
import time
from contextlib import contextmanager

DB_PATH = "bot_data.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                added_by INTEGER,
                added_at INTEGER
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS welcome_config (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                message TEXT DEFAULT 'أهلاً بك {name} في {chat}! 👋'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS goodbye_config (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                message TEXT DEFAULT 'وداعاً {name}، نتمنى رؤيتك مجدداً 👋'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS joinfilter_config (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                timeout_seconds INTEGER DEFAULT 60
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS pending_captcha (
                chat_id INTEGER,
                user_id INTEGER,
                deadline INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                chat_ids TEXT,
                text TEXT,
                interval_type TEXT,
                interval_value INTEGER,
                next_run INTEGER,
                active INTEGER DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ar'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS event_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                event_type TEXT,
                details TEXT,
                created_at INTEGER
            )
        """)

        # ميزات القنوات: توقيع تلقائي، أزرار تلقائية، نشر متبادل،
        # حذف تلقائي، موافقة تلقائية على طلبات الانضمام
        c.execute("""
            CREATE TABLE IF NOT EXISTS channel_settings (
                chat_id INTEGER PRIMARY KEY,
                signature_enabled INTEGER DEFAULT 0,
                signature_text TEXT DEFAULT '',
                buttons_enabled INTEGER DEFAULT 0,
                buttons_json TEXT DEFAULT '[]',
                crosspost_targets TEXT DEFAULT '[]',
                autodelete_enabled INTEGER DEFAULT 0,
                autodelete_minutes INTEGER DEFAULT 60,
                joinrequest_autoapprove INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_deletions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                delete_at INTEGER
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS subscriber_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                member_count INTEGER,
                recorded_at INTEGER
            )
        """)

        # منشورات "المهمة": محتوى يُسلَّم فقط لمن ينضم لقناة معينة أولاً
        c.execute("""
            CREATE TABLE IF NOT EXISTS gated_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                content_text TEXT,
                required_chat_id INTEGER,
                invite_link TEXT,
                created_at INTEGER
            )
        """)

        # يمنع تكرار تعديل نفس الرسالة أكثر من مرة (توقيع/أزرار)
        c.execute("""
            CREATE TABLE IF NOT EXISTS processed_posts (
                chat_id INTEGER,
                message_id INTEGER,
                PRIMARY KEY (chat_id, message_id)
            )
        """)


# ---------------------------------------------------------
# القنوات
# ---------------------------------------------------------

def add_channel(chat_id: int, title: str, added_by: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO channels (chat_id, title, added_by, added_at) "
            "VALUES (?, ?, ?, ?)",
            (chat_id, title, added_by, int(time.time())),
        )


def remove_channel(chat_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))


def get_channels_for_user(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM channels WHERE added_by = ? ORDER BY added_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_channel(chat_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM channels WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------
# الترحيب
# ---------------------------------------------------------

def set_welcome(chat_id: int, enabled: bool = None, message: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO welcome_config (chat_id) VALUES (?)", (chat_id,)
        )
        if enabled is not None:
            conn.execute(
                "UPDATE welcome_config SET enabled = ? WHERE chat_id = ?",
                (int(enabled), chat_id),
            )
        if message is not None:
            conn.execute(
                "UPDATE welcome_config SET message = ? WHERE chat_id = ?",
                (message, chat_id),
            )


def get_welcome(chat_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM welcome_config WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else {"enabled": 0, "message": "أهلاً بك {name} في {chat}! 👋"}


# ---------------------------------------------------------
# الوداع
# ---------------------------------------------------------

def set_goodbye(chat_id: int, enabled: bool = None, message: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO goodbye_config (chat_id) VALUES (?)", (chat_id,)
        )
        if enabled is not None:
            conn.execute(
                "UPDATE goodbye_config SET enabled = ? WHERE chat_id = ?",
                (int(enabled), chat_id),
            )
        if message is not None:
            conn.execute(
                "UPDATE goodbye_config SET message = ? WHERE chat_id = ?",
                (message, chat_id),
            )


def get_goodbye(chat_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM goodbye_config WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else {"enabled": 0, "message": "وداعاً {name} 👋"}


# ---------------------------------------------------------
# فلتر الانضمام (Captcha)
# ---------------------------------------------------------

def set_joinfilter(chat_id: int, enabled: bool = None, timeout_seconds: int = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO joinfilter_config (chat_id) VALUES (?)", (chat_id,)
        )
        if enabled is not None:
            conn.execute(
                "UPDATE joinfilter_config SET enabled = ? WHERE chat_id = ?",
                (int(enabled), chat_id),
            )
        if timeout_seconds is not None:
            conn.execute(
                "UPDATE joinfilter_config SET timeout_seconds = ? WHERE chat_id = ?",
                (timeout_seconds, chat_id),
            )


def get_joinfilter(chat_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM joinfilter_config WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else {"enabled": 0, "timeout_seconds": 60}


def add_pending_captcha(chat_id: int, user_id: int, deadline: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pending_captcha (chat_id, user_id, deadline) "
            "VALUES (?, ?, ?)",
            (chat_id, user_id, deadline),
        )


def remove_pending_captcha(chat_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM pending_captcha WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )


def is_pending_captcha(chat_id: int, user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM pending_captcha WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        ).fetchone()
        return row is not None


def get_expired_captchas(now: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pending_captcha WHERE deadline <= ?", (now,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------
# المنشورات المجدولة
# ---------------------------------------------------------

def add_scheduled_post(owner_id: int, chat_ids: list, text: str,
                        interval_type: str, interval_value: int, next_run: int):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO scheduled_posts "
            "(owner_id, chat_ids, text, interval_type, interval_value, next_run) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (owner_id, json.dumps(chat_ids), text, interval_type, interval_value, next_run),
        )
        return cur.lastrowid


def get_due_posts(now: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_posts WHERE active = 1 AND next_run <= ?",
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_next_run(post_id: int, next_run: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE scheduled_posts SET next_run = ? WHERE id = ?",
            (next_run, post_id),
        )


def get_posts_for_user(owner_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_posts WHERE owner_id = ? AND active = 1",
            (owner_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def deactivate_post(post_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE scheduled_posts SET active = 0 WHERE id = ?", (post_id,)
        )


# ---------------------------------------------------------
# إعدادات المستخدم / اللغة
# ---------------------------------------------------------

def set_language(user_id: int, language: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO user_settings (user_id, language) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET language = excluded.language",
            (user_id, language),
        )


def get_language(user_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT language FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["language"] if row else "ar"


# ---------------------------------------------------------
# سجل الأحداث
# ---------------------------------------------------------

def log_event(chat_id: int, event_type: str, details: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO event_log (chat_id, event_type, details, created_at) "
            "VALUES (?, ?, ?, ?)",
            (chat_id, event_type, details, int(time.time())),
        )


def get_recent_events(limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM event_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------
# إعدادات القناة (توقيع، أزرار، نشر متبادل، حذف تلقائي، طلبات انضمام)
# ---------------------------------------------------------

def get_channel_settings(chat_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO channel_settings (chat_id) VALUES (?)", (chat_id,)
        )
        row = conn.execute(
            "SELECT * FROM channel_settings WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row)


def update_channel_settings(chat_id: int, **fields):
    if not fields:
        return
    get_channel_settings(chat_id)  # يضمن وجود الصف
    columns = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [chat_id]
    with get_conn() as conn:
        conn.execute(
            f"UPDATE channel_settings SET {columns} WHERE chat_id = ?", values
        )


def mark_processed(chat_id: int, message_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_posts (chat_id, message_id) VALUES (?, ?)",
            (chat_id, message_id),
        )


def was_processed(chat_id: int, message_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_posts WHERE chat_id = ? AND message_id = ?",
            (chat_id, message_id),
        ).fetchone()
        return row is not None


# ---------------------------------------------------------
# الحذف التلقائي المجدول
# ---------------------------------------------------------

def add_scheduled_deletion(chat_id: int, message_id: int, delete_at: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO scheduled_deletions (chat_id, message_id, delete_at) VALUES (?, ?, ?)",
            (chat_id, message_id, delete_at),
        )


def get_due_deletions(now: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_deletions WHERE delete_at <= ?", (now,)
        ).fetchall()
        return [dict(r) for r in rows]


def remove_scheduled_deletion(row_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM scheduled_deletions WHERE id = ?", (row_id,))


# ---------------------------------------------------------
# إحصائيات المشتركين
# ---------------------------------------------------------

def record_subscriber_count(chat_id: int, count: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO subscriber_stats (chat_id, member_count, recorded_at) VALUES (?, ?, ?)",
            (chat_id, count, int(time.time())),
        )


def get_subscriber_history(chat_id: int, limit: int = 2):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM subscriber_stats WHERE chat_id = ? ORDER BY recorded_at DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------
# منشورات المهمة (Join-gate)
# ---------------------------------------------------------

def add_gated_post(owner_id: int, content_text: str, required_chat_id: int, invite_link: str):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO gated_posts (owner_id, content_text, required_chat_id, invite_link, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (owner_id, content_text, required_chat_id, invite_link, int(time.time())),
        )
        return cur.lastrowid


def get_gated_post(post_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM gated_posts WHERE id = ?", (post_id,)
        ).fetchone()
        return dict(row) if row else None
