import re

def test_ultimate_parser(markdown_file):
    with open(markdown_file, "r") as f:
        text = f.read()
    
    room_ids = re.findall(r'/rooms/(\d+)', text)
    seen_ids = []
    for rid in room_ids:
        if rid not in seen_ids: seen_ids.append(rid)
    
    deals = []
    for i, room_id in enumerate(seen_ids):
        pos = text.find(f"/rooms/{room_id}")
        # Suche 2000 Zeichen DAVOR und 500 DANACH
        block = text[max(0, pos-2000):pos+500]
        
        price_matches = re.findall(r'€\s*([\d\.,]+)|([\d\.,]+)\s*€', block)
        
        price = 100
        if price_matches:
            vals = []
            for m in price_matches:
                val_str = m[0] or m[1]
                vals.append(int(val_str.replace('.', '').replace(',', '')))
            
            # Heuristik: Nachtpreis finden
            # Airbnb Markdown: "114€ pro Nacht ... 798€ Gesamt"
            possible = [v for v in vals if 30 < v < 400]
            if possible:
                price = possible[-1] # Oft ist der letzte kleine Wert der aktuelle
            else:
                price = round(max(vals) / 7)

        deals.append({"id": room_id, "price": price})

    print(f"📊 Ergebnis: {len(deals)} Deals verarbeitet.")
    for d in deals[:10]:
        print(f"   - {d['id']} | {d['price']}€")
    
    return deals

if __name__ == "__main__":
    test_ultimate_parser("debug_content.md")
