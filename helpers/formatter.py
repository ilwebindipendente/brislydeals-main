def format_caption(p, amazon_tag):
    src = p.get('source','amazon')
    title = p['title']

    header = "🟢 [AMAZON]" if src == "amazon" else "🧧 [ALIEXPRESS]"
    header_line = f"<b>{header} {title}</b>"

    # Prezzi
    price_now = p.get('price_now')
    price_old = p.get('price_old')
    price_old_txt = f"{price_old:.2f}€" if price_old else "—"
    price_line = f"💰 Prezzo: <b>{price_now:.2f}€</b> <s>{price_old_txt}</s>"

    # Risparmio + punteggio
    risp = int(p.get('discount_pct',0))
    score = p.get('score', 0)
    risp_line = f"🎯 Sconto/Risparmio: <b>{risp}%</b> • <b>Punteggio BrislyDeals: {score}/5</b>"

    # Valutazioni
    stars = p.get('stars') or p.get('rating')
    reviews = p.get('reviews') or p.get('review_count',0)
    stars_line = f"⭐ Valutazione: {stars:.1f} ★ ({reviews:,}+)" if stars else ""

    # Categoria / Rank (Amazon + Keepa)
    cat_name = p.get('category_name') or p.get('category')
    rank = p.get('rank') or p.get('sales_rank')
    cat_line = f"🏷️ Categoria: <b>#{rank} in {cat_name}</b>" if (rank and cat_name) else ""

    # Prime/BuyBox (Amazon)
    ship_line = ""
    if src == "amazon":
        ship_line = f"🚚 <b>Prime</b> • 🏆 Buy Box: {'Amazon' if p.get('buybox_amazon') else 'Marketplace'}"

    # Keepa (Amazon)
    keepa_bits = []
    if src == "amazon":
        if p.get("min_price"): keepa_bits.append(f"📉 Min: {p['min_price']:.0f}€")
        if p.get("max_price"): keepa_bits.append(f"📈 Max: {p['max_price']:.0f}€")
        if p.get("avg_90"):    keepa_bits.append(f"📊 Media 90g: {p['avg_90']:.0f}€")
    keepa_line = ""
    if keepa_bits:
        keepa_line = "📈 Storico prezzi (Keepa):\n" + " — ".join(keepa_bits)

    # AliExpress specific (opzionali)
    ali_bits = []
    if src == "aliexpress":
        if stars: ali_bits.append(f"⭐ {stars:.1f} ★")
        if reviews: ali_bits.append(f"🛒 Ordini: {reviews:,}+")
        if p.get("store_positive"): ali_bits.append(f"🏪 Store: {p['store_positive']}% positivo")
        if p.get("shipping_label"): ali_bits.append(f"🚚 {p['shipping_label']}")
        if p.get("coupon_label"): ali_bits.append(f"🏷️ Coupon: {p['coupon_label']}")
        if p.get("choice"): ali_bits.append("🧿 AliExpress Choice")
    ali_line = " • ".join(ali_bits)

    # Link + tag affiliato Amazon
    link = p['url']
    if src == "amazon" and "tag=" not in link:
        sep = '&' if '?' in link else '?'
        link = f"{link}{sep}tag={amazon_tag}"

    cta = '🔗 Apri su Amazon (App)' if src == "amazon" else '🔗 ➡️ Guarda su AliExpress, conviene!'

    tags = " ".join(f"#{t}" for t in p.get("tags", []) if t)

    parts = [header_line, "", price_line, risp_line, stars_line, cat_line]
    if ship_line: parts.append(ship_line)
    if keepa_line: parts.extend(["", keepa_line])
    if ali_line: parts.extend(["", ali_line])
    parts.extend(["", f'<a href="{link}">{cta}</a>', "", tags])

    return "\n".join([s for s in parts if s]).strip()
