"""Notion Slip box property names and option values (spec §2).

Every step that reads or writes the Slip box imports names from here, so a
rename in Notion is a one-line change.
"""

from __future__ import annotations

from typing import Final

SLIP_BOX_DATA_SOURCE: Final = "collection://f6109065-d567-40c1-9719-2630dac385bc"

# --- existing properties -------------------------------------------------
TITLE: Final = "Title"
NOTE_TYPE: Final = "note type"
STATUS: Final = "status"
PARENT_ITEM: Final = "Parent item"
CREATE_DATE: Final = "create date"

NOTE_TYPE_LITERATURE: Final = "literature note"
NOTE_TYPE_PERMANENT: Final = "permanant note"  # spelled as in the existing option

# The spec says status=To-do / Complete; the existing status options are
# "To be reviewed" (to_do group) and "Reviewed" (complete group).
STATUS_LITERATURE: Final = "To be reviewed"
STATUS_PERMANENT: Final = "Reviewed"

# --- literature note (machine, one per session) --------------------------
SOURCE: Final = "source"
SOURCE_MANUAL: Final = "manual"
SOURCE_AGENT_SESSION: Final = "agent-session"
SOURCE_OPTIONS: Final = (SOURCE_MANUAL, SOURCE_AGENT_SESSION)

SESSION_ID: Final = "session id"

ORIGIN: Final = "origin"
ORIGIN_PERSONAL: Final = "personal"
ORIGIN_CLIENT: Final = "client"
ORIGIN_OPTIONS: Final = (ORIGIN_PERSONAL, ORIGIN_CLIENT)

P_TRAP: Final = "p_trap"
P_INSIGHT: Final = "p_insight"
P_PATTERN: Final = "p_pattern"
P_SIGNALS: Final = (P_TRAP, P_INSIGHT, P_PATTERN)

DUP_OF: Final = "dup_of"
DUP_OF_CONFIDENCE: Final = "dup_of_confidence"
DUP_OF_NONE: Final = "none"

JEV_P_TRAP: Final = "jev_p_trap"
JEV_P_INSIGHT: Final = "jev_p_insight"
JEV_P_PATTERN: Final = "jev_p_pattern"
JEV_P_SIGNALS: Final = (JEV_P_TRAP, JEV_P_INSIGHT, JEV_P_PATTERN)
JEV_DUP_OF: Final = "jev_dup_of"

JEV_LABEL: Final = "jev_label"
JEV_LABEL_UP: Final = "👍"
JEV_LABEL_DOWN: Final = "👎"
JEV_LABEL_OPTIONS: Final = (JEV_LABEL_UP, JEV_LABEL_DOWN)

TOPIC_OF: Final = "topic_of"
TOPIC_NEW: Final = "new"

PRIVACY_FLAG: Final = "privacy_flag"
PRIVACY_REASON: Final = "privacy_reason"

READER_QUESTIONS: Final = "reader_questions"
READER_QUESTION_KINDS: Final = ("fix", "understand", "design", "improve", "decide", "none")

MARKET_HEAT: Final = "market_heat"
MARKET_PAIN: Final = "market_pain"
MARKET_STATUS: Final = "market_status"
MARKET_STATUS_B: Final = "b"
MARKET_STATUS_A_B: Final = "a+b"
MARKET_STATUS_INSUFFICIENT: Final = "insufficient"
MARKET_STATUS_OPTIONS: Final = (MARKET_STATUS_B, MARKET_STATUS_A_B, MARKET_STATUS_INSUFFICIENT)

PICK_STATUS: Final = "pick_status"
PICK_NOT_LISTED: Final = "未推薦"
PICK_LISTED: Final = "推薦過"
PICK_PICKED: Final = "挑中"
PICK_ABANDONED: Final = "放棄"
PICK_STATUS_OPTIONS: Final = (PICK_NOT_LISTED, PICK_LISTED, PICK_PICKED, PICK_ABANDONED)
PICK_POOL_STATES: Final = (PICK_NOT_LISTED, PICK_LISTED)

LAST_LISTED_AT: Final = "last_listed_at"
LISTED_COUNT: Final = "listed_count"

SCORE: Final = "score"

# --- permanent note (human, drafting session) ----------------------------
BLOG_STATUS: Final = "blog status"
BLOG_WRITING: Final = "寫作中"
BLOG_PUBLISHED: Final = "已發表"
BLOG_ABANDONED: Final = "放棄"
BLOG_STATUS_OPTIONS: Final = (BLOG_WRITING, BLOG_PUBLISHED, BLOG_ABANDONED)

DRAFT_PATH: Final = "draft path"
PUBLISHED_URL: Final = "published url"
PUBLISHED_DATE: Final = "published date"
NOTE_PENDING: Final = "note pending"
SLUG: Final = "slug"

# --- views ---------------------------------------------------------------
VIEW_AGENT_SESSIONS: Final = "agent-session"
VIEW_CANDIDATE_POOL: Final = "候補池"

# Property name -> Notion type, for every property this pipeline adds.
ADDED_PROPERTIES: Final = {
    SOURCE: "select",
    SESSION_ID: "rich_text",
    ORIGIN: "select",
    P_TRAP: "number",
    P_INSIGHT: "number",
    P_PATTERN: "number",
    DUP_OF: "rich_text",
    DUP_OF_CONFIDENCE: "number",
    JEV_P_TRAP: "number",
    JEV_P_INSIGHT: "number",
    JEV_P_PATTERN: "number",
    JEV_DUP_OF: "rich_text",
    JEV_LABEL: "select",
    TOPIC_OF: "rich_text",
    PRIVACY_FLAG: "checkbox",
    PRIVACY_REASON: "rich_text",
    READER_QUESTIONS: "rich_text",
    MARKET_HEAT: "number",
    MARKET_PAIN: "number",
    MARKET_STATUS: "select",
    PICK_STATUS: "select",
    LAST_LISTED_AT: "date",
    LISTED_COUNT: "number",
    SCORE: "number",
    BLOG_STATUS: "select",
    DRAFT_PATH: "rich_text",
    PUBLISHED_URL: "url",
    PUBLISHED_DATE: "date",
    NOTE_PENDING: "checkbox",
    SLUG: "rich_text",
}

# Select property name -> allowed options.
SELECT_OPTIONS: Final = {
    SOURCE: SOURCE_OPTIONS,
    ORIGIN: ORIGIN_OPTIONS,
    JEV_LABEL: JEV_LABEL_OPTIONS,
    MARKET_STATUS: MARKET_STATUS_OPTIONS,
    PICK_STATUS: PICK_STATUS_OPTIONS,
    BLOG_STATUS: BLOG_STATUS_OPTIONS,
}
