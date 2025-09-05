# BrislyDeals Main (Cron)

- Cron su Render: `Schedule: 0 * * * *` (UTC), `Command: python main.py`
- Slot (Europe/Rome): Lun–Ven 09,11,13,15,17,19,21; Domenica 12 = report
- Routing: Principale (@BrislyDeals) = Amazon + Ali; Secondario (@FengXpress) = solo Ali (configurabile via ENV)
- Keepa con cache Upstash, report Top 5 settimanale, dedup 4 giorni

## Env principali
Vedi `.env.example`. Imposta su Render: API_ID, API_HASH, BOT_TOKEN, CHANNEL_MAIN, CHANNEL_ALI, TIMEZONE, AMAZON_*,
KEEPA_API_KEY, UPSTASH_* (consigliato), MIN_STARS, MIN_DISCOUNT, POSTS_PER_SLOT, USE_ALIEXPRESS, routing flags.

## Test manuale
- `python main.py publish` (forza una pubblicazione)
- `python main.py weekly-report` (forza il report)

> Nota: i Cron Render non hanno storage locale persistente. Upstash consigliato per dedup/cache/metriche.
