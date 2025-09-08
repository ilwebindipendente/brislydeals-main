def get_score_comment(score):
    """Restituisce un commento interpretativo basato sul punteggio"""
    if score >= 4.5:
        return "Affare eccezionale", "Prezzo stracciato, occasione imperdibile"
    elif score >= 4.0:
        return "Ottimo acquisto", "Prezzo molto conveniente per la qualità"
    elif score >= 3.5:
        return "Buon affare", "Prezzo interessante e competitivo"
    elif score >= 3.0:
        return "Discreto", "Prezzo nella media, da valutare"
    elif score >= 2.5:
        return "Mediocre", "Prezzo poco conveniente"
    else:
        return "Sconsigliato", "Prezzo troppo alto per il valore offerto"

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
    Formatta il post con layout pulito, sezione BrislyDeals Score e senza link testuale
    """
    src = p.get('source', 'amazon')
    title = (p.get('title') or '').strip() or 'Offerta'
    
    # === HEADER ===
    header = "🟢 [AMAZON]" if src == "amazon" else "🧧 [ALIEXPRESS]"
    header_line = f"<b>{header} {title}</b>"
    
    # === SEZIONE PREZZO ===
    price_now = float(p.get('price_now') or 0.0)
    price_old = p.get('price_old')
    
    if price_old:
        price_line = f"💰 <b>{price_now:.2f}€</b> <s>{price_old:.2f}€</s>"
        discount_pct = int(p.get('discount_pct', 0))
        discount_line = f"🎯 <b>{discount_pct}% di sconto</b>"
    else:
        price_line = f"💰 <b>{price_now:.2f}€</b>"
        discount_line = None
    
    # === SEZIONE BRISLYDEALS SCORE ===
    score = p.get('score', 0)
    score_title, score_comment = get_score_comment(score)
    
    score_section = [
        "🎯 <b>BrislyDeals Score™</b>",
        "Il nostro algoritmo analizza sconto, storico prezzi, rating e posizione in classifica per valutare ogni offerta.",
        f"📊 <b>A questo prodotto assegno: {score}/5 - \"{score_title}\"</b>",
        f"💡 {score_comment}"
    ]
    
    # === SEZIONE PRODOTTO ===
    product_info = []
    
    # Brand
    if p.get("brand"):
        product_info.append(f"🏷️ <b>{p['brand']}</b>")
    
    # Rating e recensioni
    stars = p.get('stars') or p.get('rating')
    reviews = p.get('reviews') or p.get('review_count', 0)
    if stars:
        product_info.append(f"⭐ <b>{stars:.1f}/5</b> ({reviews:,} recensioni)")
    
    # Categoria e ranking
    cat_name = p.get('category_name') or p.get('category')
    rank = p.get('rank') or p.get('sales_rank')
    if rank and cat_name:
        product_info.append(f"📊 <b>#{rank}</b> in {cat_name}")
    
    # === SEZIONE SERVIZI AMAZON ===
    services = []
    if src == "amazon":
        if p.get("prime"):
            services.append("🚚 <b>Prime</b>")
        
        buybox = p.get("buybox_amazon")
        if buybox is not None:
            buybox_text = "Amazon" if buybox else "Marketplace" 
            services.append(f"🏆 Buy Box: {buybox_text}")
    
    # === SEZIONE KEEPA (STORICO PREZZI) ===
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
    
    # === SEZIONE ALIEXPRESS ===
    ali_section = []
    if src == "aliexpress":
        ali_bits = []
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
    
    # === SEZIONE CARATTERISTICHE ===
    features_section = []
    features = p.get("features") or []
    if features and src == "amazon":
        # Prendi solo le prime 2 features più importanti per risparmiare spazio
        top_features = features[:2]
        for feat in top_features:
            # Accorcia le features troppo lunghe
            if len(feat) > 80:
                feat = feat[:77] + "..."
            features_section.append(f"• {feat}")
    
    # === HASHTAGS ===
    hashtags = generate_hashtags(p)
    
    # === ASSEMBLAGGIO FINALE ===
    sections = [header_line]
    
    # Prezzo
    sections.extend(["", price_line])
    if discount_line:
        sections.append(discount_line)
    
    # BrislyDeals Score
    sections.extend(["", *score_section])
    
    # Info prodotto
    if product_info:
        sections.extend(["", *product_info])
    
    # Servizi Amazon
    if services:
        sections.extend(["", " • ".join(services)])
    
    # Storico prezzi Keepa
    if keepa_section:
        sections.extend(["", *keepa_section])
    
    # Info AliExpress
    if ali_section:
        sections.extend(["", *ali_section])
    
    # Caratteristiche
    if features_section:
        sections.extend(["", *features_section])
    
    # Hashtags (senza link testuale)
    if hashtags:
        sections.extend(["", hashtags])
    
    return "\n".join(sections)
