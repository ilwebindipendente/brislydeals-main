def get_score_comment(score):
    """Restituisce un commento interpretativo basato sul punteggio"""
    if score >= 4.5:
        return "Affare eccezionale"
    elif score >= 4.0:
        return "Ottimo acquisto"
    elif score >= 3.5:
        return "Buon affare"
    elif score >= 3.0:
        return "Discreto"
    elif score >= 2.5:
        return "Mediocre"
    else:
        return "Sconsigliato"

def shorten_title(title):
    """Accorcia il titolo alle prime 8-9 parole chiave, restituisce titolo corto e resto"""
    if not title:
        return "Offerta", ""
    
    words = title.split()
    if len(words) <= 9:
        return title, ""
    
    # Prendi le prime 8-9 parole più significative
    short_title = " ".join(words[:8])
    remaining = " ".join(words[8:])
    
    return short_title, remaining

def generate_hashtags(product):
    """Genera hashtag strutturati: Tipologia + Brand + Categoria"""
    hashtags = []
    
    # Tipologia prodotto (basata su title e features)
    title_lower = (product.get('title', '') or '').lower()
    features = ' '.join(product.get('features', [])).lower()
    
    # Mappatura tipologie
    if any(term in title_lower for term in ['ssd', 'nvme', 'hard disk']):
        hashtags.append('#SSD')
    elif any(term in title_lower for term in ['cuffie', 'auricolari', 'headphone']):
        hashtags.append('#Cuffie')
    elif any(term in title_lower for term in ['monitor', 'display']):
        hashtags.append('#Monitor')
    elif any(term in title_lower for term in ['robot', 'aspirapolvere']):
        hashtags.append('#RobotAspirapolvere')
    elif any(term in title_lower for term in ['tv', 'televisore', 'smart tv']):
        hashtags.append('#TV')
    elif any(term in title_lower for term in ['mouse', 'tastiera', 'keyboard']):
        hashtags.append('#Periferiche')
    elif any(term in title_lower for term in ['smartphone', 'telefono', 'cellulare']):
        hashtags.append('#Smartphone')
    elif any(term in title_lower for term in ['tablet', 'ipad']):
        hashtags.append('#Tablet')
    elif any(term in title_lower for term in ['gaming', 'game', 'gioco']):
        hashtags.append('#Gaming')
    else:
        hashtags.append('#Tech')
    
    # Brand
    brand = product.get('brand')
    if brand:
        # Pulisci il brand per hashtag (rimuovi spazi e caratteri speciali)
        brand_clean = ''.join(c for c in brand if c.isalnum())
        if brand_clean:
            hashtags.append(f'#{brand_clean}')
    
    # Categoria estesa
    category_name = product.get('category_name', '')
    if 'ssd' in title_lower or 'hard disk' in title_lower or 'archiviazione' in category_name.lower():
        hashtags.append('#ComponentiPC')
    elif any(term in title_lower for term in ['cuffie', 'auricolari', 'speaker', 'audio']):
        hashtags.append('#Audio')
    elif 'monitor' in title_lower or 'display' in title_lower:
        hashtags.append('#Display')
    elif 'robot' in title_lower or 'aspirapolvere' in title_lower:
        hashtags.append('#CasaIntelligente')
    elif 'tv' in title_lower or 'smart tv' in title_lower:
        hashtags.append('#Intrattenimento')
    elif any(term in title_lower for term in ['mouse', 'tastiera', 'gaming']):
        hashtags.append('#Gaming')
    elif any(term in title_lower for term in ['smartphone', 'tablet', 'ipad']):
        hashtags.append('#Mobile')
    else:
        hashtags.append('#Elettronica')
    
    return ' '.join(hashtags[:3])  # Massimo 3 hashtag

def format_caption(p, amazon_tag):
    """
    VERSIONE 2 - Formatta il post con nuovo ordine: prezzo+servizi -> storico -> score -> descrizione -> info prodotto
    """
    src = p.get('source', 'amazon')
    full_title = (p.get('title') or '').strip() or 'Offerta'
    
    # Accorcia il titolo
    short_title, title_remainder = shorten_title(full_title)
    
    # === HEADER ===
    header = "🟢 [AMAZON]" if src == "amazon" else "🧧 [ALIEXPRESS]"
    header_line = f"<b>{header} {short_title}</b>"
    
    # === 1. SEZIONE PREZZO E SERVIZI ===
    price_now = float(p.get('price_now') or 0.0)
    price_old = p.get('price_old')
    
    price_services = []
    
    # Prezzo
    if price_old:
        price_services.append(f"💰 <b>{price_now:.2f}€</b> <s>{price_old:.2f}€</s>")
        discount_pct = int(p.get('discount_pct', 0))
        price_services.append(f"🎯 <b>{discount_pct}% di sconto</b>")
    else:
        price_services.append(f"💰 <b>{price_now:.2f}€</b>")
    
    # Servizi Amazon sulla stessa sezione
    if src == "amazon":
        services = []
        if p.get("prime"):
            services.append("🚚 <b>Prime</b>")
        
        buybox = p.get("buybox_amazon")
        if buybox is not None:
            buybox_text = "Amazon" if buybox else "Marketplace" 
            services.append(f"🏆 Buy Box: {buybox_text}")
        
        if services:
            price_services.append(" • ".join(services))
    
    # === 2. SEZIONE KEEPA (STORICO PREZZI) ===
    keepa_section = []
    if src == "amazon":
        keepa_data = []
        
        min_price = p.get("min_price")
        max_price = p.get("max_price")
        avg_90 = p.get("avg_90")
        
        # Gestisci tuple per min/max (datetime, price)
        if isinstance(min_price, (list, tuple)) and len(min_price) > 1:
            min_price = min_price[1]
        if isinstance(max_price, (list, tuple)) and len(max_price) > 1:
            max_price = max_price[1]
        
        if min_price is not None:
            keepa_data.append(f"📉 Min: {min_price:.0f}€")
        if max_price is not None:
            keepa_data.append(f"📈 Max: {max_price:.0f}€")
        if avg_90 is not None:
            keepa_data.append(f"📊 Media 90g: {avg_90:.0f}€")
            
        if keepa_data:
            keepa_section.append("📈 <b>Storico prezzi (Keepa)</b>:")
            keepa_section.append(" • ".join(keepa_data))
    
    # === 3. SEZIONE BRISLYDEALS SCORE ===
    score = p.get('score', 0)
    score_title = get_score_comment(score)
    
    score_section = [
        f"🎯 <b>BrislyDeals Score™: {score}/5 - \"{score_title}\"</b>",
        "Algoritmo basato su sconto, storico prezzi e ranking Amazon"
    ]
    
    # === 4. SEZIONE DESCRIZIONE (titolo rimanente + features) ===
    description_section = []
    
    # Aggiungi il resto del titolo se presente
    if title_remainder:
        description_section.append(f"📝 <b>{title_remainder}</b>")
    
    # Features del prodotto
    features = p.get("features") or []
    if features and src == "amazon":
        top_features = features[:2]
        for feat in top_features:
            if len(feat) > 80:
                feat = feat[:77] + "..."
            description_section.append(f"• {feat}")
    
    # === SEZIONE ALIEXPRESS ===
    ali_section = []
    if src == "aliexpress":
        ali_bits = []
        stars = p.get('stars') or p.get('rating')
        reviews = p.get('reviews') or p.get('review_count', 0)
        if stars:
            ali_bits.append(f"⭐ {stars:.1f}/5")
        if reviews:
            ali_bits.append(f"🛒 {reviews:,}+ ordini")
        if p.get("store_positive"):
            ali_bits.append(f"🏪 Store: {p['store_positive']}% positivo")
        if p.get("shipping_label"):
            ali_bits.append(f"🚚 {p['shipping_label']}")
        if p.get("coupon_label"):
            ali_bits.append(f"🏷️ Coupon: {p['coupon_label']}")
        if p.get("choice"):
            ali_bits.append("🧿 AliExpress Choice")
            
        if ali_bits:
            ali_section.append(" • ".join(ali_bits))
    
    # === ULTIMO BLOCCO: INFO PRODOTTO + HASHTAG (tutto in un blocco compatto) ===
    final_lines = []
    
    # Brand
    if p.get("brand"):
        final_lines.append(f"🏷️ <b>{p['brand']}</b>")
    
    # Categoria e ranking
    cat_name = p.get('category_name') or p.get('category')
    rank = p.get('rank') or p.get('sales_rank')
    if rank and cat_name:
        final_lines.append(f"📊 <b>#{rank}</b> in {cat_name}")
    
    # Rating e recensioni (solo se non AliExpress)
    if src == "amazon":
        stars = p.get('stars') or p.get('rating')
        reviews = p.get('reviews') or p.get('review_count', 0)
        if stars:
            final_lines.append(f"⭐ <b>{stars:.1f}/5</b> ({reviews:,} recensioni)")
    
    # Hashtags (stessa sezione, nessun spazio)
    hashtags = generate_hashtags(p)
    if hashtags:
        final_lines.append(hashtags)
    
    # === ASSEMBLAGGIO FINALE ===
    sections = [header_line]
    
    # 1. Prezzo e servizi
    sections.extend(["", *price_services])
    
    # 2. Storico prezzi Keepa
    if keepa_section:
        sections.extend(["", *keepa_section])
    
    # 3. BrislyDeals Score
    sections.extend(["", *score_section])
    
    # 4. Descrizione
    if description_section:
        sections.extend(["", *description_section])
    
    # Info AliExpress (se presente)
    if ali_section:
        sections.extend(["", *ali_section])
    
    # BLOCCO FINALE COMPATTO (una riga vuota prima, poi tutto attaccato)
    if final_lines:
        sections.append("")  # Una sola riga vuota prima del blocco finale
        for line in final_lines:
            sections.append(line)  # Aggiungi ogni riga senza spazi tra di loro
    
    return "\n".join(sections)
