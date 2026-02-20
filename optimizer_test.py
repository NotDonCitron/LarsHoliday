import re

def test_final_parser(markdown_file):
    with open(markdown_file, "r") as f:
        text = f.read()
    
    # 1. Finde alle Room-IDs in Links
    # Format: https://www.airbnb.com/rooms/1491270913639212879
    # Wir nehmen nur die numerische ID
    raw_links = re.findall(r'https://www\.airbnb\.com/rooms/(\d+)', text)
    
    deals = []
    seen_ids = set()
    
    # 2. Wir iterieren über den Text und suchen nach IDs und Preisen
    for room_id in raw_links:
        if room_id in seen_ids: continue
        seen_ids.add(room_id)
        
        # Suche die Position dieser ID im Text
        pos = text.find(room_id)
        # Suche im Umkreis von 1000 Zeichen nach einem Preis
        context = text[pos:pos+1000]
        
        price_match = re.search(r'€\s*([\d\.,]+)|([\d\.,]+)\s*€', context)
        price = 100
        if price_match:
            val_str = price_match.group(1) or price_match.group(2)
            price = int(val_str.replace('.', '').replace(',', ''))
            # Wenn Preis für 7 Tage ist (hoch), dividieren
            if price > 300: price = round(price / 7)

        # Name finden: Oft steht der Name vor oder nach dem Link in fett oder als Überschrift
        # In diesem Markdown schwer, wir nehmen eine Heuristik
        name = f"Airbnb Unterkunft {room_id[:5]}"
        
        # Bild finden (das ![](URL) direkt vor dem Link)
        image_url = ""
        img_context = text[max(0, pos-500):pos]
        img_match = re.search(r'https://a0\.muscache\.com/im/pictures/[^\s\)]+', img_context)
        if img_match:
            image_url = img_match.group(0).split('?')[0]

        deals.append({
            "id": room_id,
            "price": price,
            "name": name,
            "image": bool(image_url)
        })

    print(f"✅ Lokaler Test: {len(deals)} Deals gefunden!")
    for d in deals[:5]:
        print(f"   - ID: {d['id']} | Preis: {d['price']}€ | Bild: {d['image']}")
    
    return len(deals)

if __name__ == "__main__":
    test_final_parser("debug_content.md")
