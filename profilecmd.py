"""/profile  -> photo card (level, wager rank, stats) + 'Change Theme' button.

Theme user ke hisaab se save hota hai (prefs 'ptheme'). Card design: profilecard.py
"""
import asyncio
import logging
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import profilecard as pc
import tg
from cardimg import _clean
from database import db, ensure_user, get, pref, set_pref
from ui import Btn, Screen, delete, edit_card, edit_rich_photo, esc, send, send_rich_photo

log = logging.getLogger(__name__)
_cache = {}   # (uid, theme) -> (time, png): theme picker kholne/band karne par dobara render na ho
router = Router(name="profile")


def theme_of(uid):
    t = pref(uid, "ptheme", pc.DEFAULT_THEME)
    return t if t in pc.THEMES else pc.DEFAULT_THEME


def main_buttons(back):
    rows = [[Btn("🎨 Change Theme", "pf:th", style="success")],
            [Btn("📒 Statement", "st:open", style="primary"), Btn("💳 Payments", "pay:open", style="primary")],
            [Btn("👥 Refer & Earn", "ref:open", style="success")]]
    if back:
        rows.append([Btn("⬅️ Back", "home", style="primary")])
    return rows


def picker_buttons(cur):
    ids = pc.theme_ids()
    rows = []
    for i in range(0, len(ids), 2):
        rows.append([Btn(("✅ " if t == cur else "") + pc.THEMES[t]["label"], f"pf:t:{t}",
                         style="success" if t == cur else "primary") for t in ids[i:i + 2]])
    rows.append([Btn("✔ Done", "pf:done", style="success")])
    return rows


def caption(u, tgu, theme):
    li = pc.level_info(u["wagered"])
    name = _clean(tgu.full_name, 24) or "Player"
    return Screen(rich=False, title=f"👤 <b>{esc(name)}</b> · {li['tier']} L{li['level']}",
                  body=[f"Theme: <b>{esc(pc.THEMES[theme]['label'])}</b>"])


async def make_png(u, tgu, theme, use_cache=False):
    hit = _cache.get((u["id"], theme))
    if use_cache and hit and time.time() - hit[0] < 90:
        return hit[1]
    li = pc.level_info(u["wagered"])
    h = db("SELECT COUNT(*) n, COALESCE(SUM(payout>bet),0) w, COALESCE(SUM(payout),0) tw, COALESCE(SUM(bet),0) tb, "
           "COALESCE(MAX(payout-bet),0) bw FROM history WHERE uid=?", (u["id"],), "one")
    rank = None
    if u["wagered"] > 0:
        rank = db("SELECT COUNT(*)+1 c FROM users WHERE wagered>?", (u["wagered"],), "one")["c"]
    av = await tg.avatar(tgu.id) if get("card_avatar") == "1" else None
    p = dict(brand=get("brand"), name=_clean(tgu.full_name, 22) or _clean(tgu.first_name, 22) or "Player",
             username=_clean(tgu.username or "", 24), uid=u["id"], joined=u["joined"], cur=get("currency"),
             tier=li["tier"], level=li["level"], next_label=li["next_label"], progress=li["progress"],
             target=li["target"], wagered=u["wagered"], rank=f"#{rank}" if rank else "—",
             games=h["n"], winrate=(100.0 * h["w"] / h["n"]) if h["n"] else 0.0, biggest=max(h["bw"], 0),
             balance=u["balance"], total_won=h["tw"])
    png = await asyncio.to_thread(pc.render, p, theme, av)
    if len(_cache) > 200:
        _cache.clear()
    _cache[(u["id"], theme)] = (time.time(), png)
    return png


async def send_profile(chat_id, tgu, reply_to=None, back=False):
    u, _ = ensure_user(tgu)
    th = theme_of(u["id"])
    png = await make_png(u, tgu, th)
    cap = caption(u, tgu, th)
    return await send_rich_photo(chat_id, png, Screen(rich=False, title=cap.title, body=cap.body,
                                                      buttons=main_buttons(back)), reply_to)


async def profile_or_text(chat_id, tgu, reply_to=None, back=False):
    """Card bhejo; card na ban paye (Pillow/font issue) to simple text profile."""
    try:
        return await send_profile(chat_id, tgu, reply_to=reply_to, back=back)
    except Exception:
        log.exception("profile card failed -> text fallback")
        u, _ = ensure_user(tgu)
        li = pc.level_info(u["wagered"])
        return await send(chat_id, Screen(rich=False, title="👤 <b>Profile</b>", rows=[
            ("Level", f"{li['tier']} L{li['level']}"), ("Wagered", f"{get('currency')}{u['wagered']:,.2f}"),
            ("Balance", f"{get('currency')}{u['balance']:,.2f}")]), reply_to=reply_to)


async def _refresh(c, theme, buttons, fresh=False):
    """Profile message ko naye theme / buttons ke saath update karo."""
    u, _ = ensure_user(c.from_user)
    cap = caption(u, c.from_user, theme)
    scr = Screen(rich=False, title=cap.title, body=cap.body, buttons=buttons)
    png = await make_png(u, c.from_user, theme, use_cache=not fresh)
    chat, mid = c.message.chat.id, c.message.message_id
    if getattr(c.message, "photo", None):          # purana photo+caption card (fallback mode)
        return await edit_card(chat, mid, png, scr)
    try:
        await edit_rich_photo(chat, mid, png, scr)
    except tg.ApiError as e:
        if "not modified" in e.desc.lower():
            return
        log.warning("rich photo edit failed (%s) -> resend", e)
        await delete(chat, mid)
        await send_rich_photo(chat, png, scr)


@router.message(Command("profile"))
async def profile_cmd(m: Message):
    await profile_or_text(m.chat.id, m.from_user, reply_to=m.message_id, back=m.chat.type == "private")


@router.callback_query(F.data == "profile")
async def profile_cb(c: CallbackQuery):
    await c.answer()
    await delete(c.message.chat.id, c.message.message_id)
    await profile_or_text(c.message.chat.id, c.from_user, back=True)


@router.callback_query(F.data == "pf:th")
async def theme_open(c: CallbackQuery):
    cur = theme_of(c.from_user.id)
    await c.answer("Pick a theme 🎨")
    await _refresh(c, cur, picker_buttons(cur))


@router.callback_query(F.data.startswith("pf:t:"))
async def theme_set(c: CallbackQuery):
    t = c.data[5:]
    if t not in pc.THEMES:
        return await c.answer()
    u, _ = ensure_user(c.from_user)
    if theme_of(u["id"]) == t:
        return await c.answer("Already selected")
    set_pref(u["id"], "ptheme", t)
    await c.answer("Applying…")
    await _refresh(c, t, picker_buttons(t), fresh=True)


@router.callback_query(F.data == "pf:done")
async def theme_done(c: CallbackQuery):
    await c.answer("Theme saved ✅")
    await _refresh(c, theme_of(c.from_user.id), main_buttons(c.message.chat.type == "private"))
