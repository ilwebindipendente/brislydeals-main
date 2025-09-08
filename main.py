import os, asyncio, argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from telethon import TelegramClient
from config import (API_ID, API_HASH, BOT_TOKEN, CHANNEL_MAIN, CHANNEL_ALI,
                    TIMEZONE, AMAZON_PARTNER_TAG, PUBLISH_HOURS, POSTS_PER_SLOT,
                    AMZ_TO_MAIN, AMZ_TO_ALI, ALI_TO_MAIN, ALI_TO_ALI)
from helpers.selector import gather_candidates, enrich_and_rank, commit_published
from helpers.formatter import format_caption
from helpers.redis_store import metrics_add, metrics_top

from telethon import Button

buttons = [
    [Button.url("🛒 Vedi su Amazon", amazon_url)],
    [Button.url("⚠️ Segnala errori", "https://t.me/BrislyDealsBot")],
    [Button.url("🌐 Visita BrislyDeals", "https://brislydeals.com")]
]

TZ = ZoneInfo(TIMEZONE)
client = TelegramClient("bot", API_ID, API_HASH)
client.parse_mode = 'html'   # <— aggiungi questa riga

def decide_action(now_local: datetime):
    if now_local.weekday() == 6 and now_local.hour == 12:
        return "weekly-report"
    if now_local.weekday() < 5 and now_local.hour in PUBLISH_HOURS:
        return "publish"
    return None

def week_key(dt: datetime) -> str:
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"

async def task_publish():
    cands = await asyncio.to_thread(gather_candidates)
    ranked = await asyncio.to_thread(enrich_and_rank, cands)
    if not ranked:
        print("Nessuna offerta valida per questo slot.")
        return

    to_post = ranked[:POSTS_PER_SLOT]
    wk = week_key(datetime.now(TZ))
    await client.start(bot_token=BOT_TOKEN)

    for offer in to_post:
        # routing per fonte
        targets = []
        if offer.get("source") == "amazon":
            if AMZ_TO_MAIN: targets.append(CHANNEL_MAIN)
            if AMZ_TO_ALI:  targets.append(CHANNEL_ALI)
        else:
            if ALI_TO_MAIN: targets.append(CHANNEL_MAIN)
            if ALI_TO_ALI:  targets.append(CHANNEL_ALI)

        for ch in targets:
            caption = format_caption(offer, AMAZON_PARTNER_TAG)
            if offer.get("image"):
                await client.send_file(ch, offer["image"], caption=caption, parse_mode="html")
            else:
                await client.send_message(ch, caption, parse_mode="html")
            # metriche per report (per canale)
            ocopy = dict(offer); ocopy["channel"] = ch
            metrics_add(wk, ocopy, float(offer.get("score", 0)))
            print(f"Pubblicata ({offer.get('source','?')}) su {ch}: {offer['title']}")

        commit_published(offer["asin"])

    await client.disconnect()

async def task_weekly_report():
    wk = week_key(datetime.now(TZ))
    top_score = metrics_top(wk, "score", topn=5)
    top_disc  = metrics_top(wk, "discount", topn=5)

    def fmt(items):
        lines = []
        for i, it in enumerate(items, 1):
            lines.append(f"{i}) {it['title']} — ⭐{it.get('score',0)}/5 — 💸 {it.get('discount_pct',0)}%")
        return "\n".join(lines) if lines else "Nessun dato disponibile questa settimana."

    text = (
        "<b>📊 Report settimanale BrislyDeals</b>\n\n"
        "<b>🏅 Top 5 per Punteggio</b>\n" + fmt(top_score) + "\n\n" +
        "<b>💥 Top 5 per Risparmio</b>\n" + fmt(top_disc) + "\n\n"
        "Grazie per averci seguito! ❤️"
    )
    await client.start(bot_token=BOT_TOKEN)
    await client.send_message(CHANNEL_MAIN, text, parse_mode="html")
    await client.disconnect()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", help="publish | weekly-report")
    args = parser.parse_args()

    now = datetime.now(TZ)
    action = args.action or decide_action(now)
    if not action:
        print(f"No-op ({now.isoformat()} {TIMEZONE})")
        return

    if action == "publish":
        await task_publish()
    elif action == "weekly-report":
        await task_weekly_report()

if __name__ == "__main__":
    asyncio.run(main())


