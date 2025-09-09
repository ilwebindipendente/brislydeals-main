import urllib.parse

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

        # Prepara URL con tag affiliazione
        url = offer.get('url', '')
        
        # VALIDAZIONE E FIX URL
        if not url:
            print(f"[ERROR] URL mancante per {offer.get('asin', 'unknown')}, skipping...")
            continue
            
        # Assicurati che l'URL inizi con http/https
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Pulisci l'URL da caratteri problematici
        try:
            # Parse e ricostruisci l'URL per pulirlo
            parsed = urllib.parse.urlparse(url)
            
            # Se manca il dominio, skip
            if not parsed.netloc:
                print(f"[ERROR] URL invalido {url} per {offer.get('asin', 'unknown')}, skipping...")
                continue
                
            # Ricostruisci URL pulito
            clean_url = urllib.parse.urlunparse(parsed)
            
            # Limita lunghezza URL (Telegram max 2048)
            if len(clean_url) > 2000:
                print(f"[WARNING] URL troppo lungo per {offer.get('asin', 'unknown')}, troncato")
                clean_url = clean_url[:2000]
                
        except Exception as e:
            print(f"[ERROR] Impossibile parsare URL {url}: {e}, skipping...")
            continue
        
        # Aggiungi tag affiliazione se Amazon
        if offer.get("source") == "amazon" and "tag=" not in clean_url:
            sep = '&' if '?' in clean_url else '?'
            clean_url = f"{clean_url}{sep}tag={AMAZON_PARTNER_TAG}"
        
        # Log dell'URL finale per debug
        print(f"[DEBUG] URL finale per {offer.get('asin', 'unknown')}: {clean_url[:100]}...")

        for ch in targets:
            # Formatta caption (senza link testuale)
            caption = format_caption(offer, AMAZON_PARTNER_TAG)
            
            # Crea pulsanti inline con URL validato
            buttons = create_inline_buttons(clean_url, offer.get("source", "amazon"))
            
            try:
                # Pubblica con immagine e pulsanti
                if offer.get("image"):
                    await client.send_file(
                        ch, 
                        offer["image"], 
                        caption=caption, 
                        parse_mode="html",
                        buttons=buttons
                    )
                else:
                    await client.send_message(
                        ch, 
                        caption, 
                        parse_mode="html",
                        buttons=buttons
                    )
                
                # metriche per report (per canale)
                ocopy = dict(offer); ocopy["channel"] = ch
                metrics_add(wk, ocopy, float(offer.get("score", 0)))
                print(f"✅ Pubblicata ({offer.get('source','?')}) su {ch}: {offer['title']}")
                
            except Exception as e:
                print(f"[ERROR] Impossibile pubblicare su {ch}: {e}")
                print(f"[DEBUG] URL che ha causato l'errore: {clean_url}")
                # Continua con il prossimo canale/prodotto invece di crashare
                continue

        commit_published(offer["asin"])

    await client.disconnect()
