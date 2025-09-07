#!/usr/bin/env python3
"""
Test rapido solo per Keepa API
"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_keepa_structure():
    """Test per vedere la struttura dei dati Keepa"""
    try:
        import keepa
        from config import KEEPA_API_KEY
        
        if not KEEPA_API_KEY:
            print("❌ KEEPA_API_KEY non configurata")
            return
            
        print("🔍 Testing Keepa structure...")
        
        # Test con ASIN che sappiamo ha funzionato nella pubblicazione
        test_asin = "B0DC8VPSHV"  # Crucial SSD che ha pubblicato
        
        k = keepa.Keepa(KEEPA_API_KEY)
        print(f"Querying {test_asin}...")
        
        # Query minima per debug
        products = k.query(test_asin, domain="IT", stats=90, history=False, wait=True)
        
        if not products:
            print("❌ Nessun prodotto restituito")
            return
            
        item = products[0]
        print(f"✅ Ricevuto prodotto: {type(item)}")
        
        # Debug completo della struttura
        print("\n=== STRUTTURA OGGETTO ===")
        print(f"Type: {type(item)}")
        
        if isinstance(item, dict):
            print(f"Dict keys: {list(item.keys())}")
            print(f"Dict content preview:")
            for key, value in item.items():
                value_str = str(value)[:200] if value is not None else "None"
                print(f"  {key}: {type(value)} = {value_str}...")
        else:
            print(f"Dir: {[attr for attr in dir(item) if not attr.startswith('_')]}")
            if hasattr(item, '__dict__'):
                print(f"Vars: {list(vars(item).keys())}")
                
        # Test attributi specifici
        attrs_to_test = ['asin', 'stats', 'csv', 'rating', 'reviewCount', 'categoryTree', 'buyBoxIsAmazon']
        
        print("\n=== ATTRIBUTI DISPONIBILI ===")
        for attr in attrs_to_test:
            if isinstance(item, dict):
                if attr in item:
                    value = item[attr]
                    print(f"✅ {attr}: {type(value)} = {str(value)[:100]}...")
                else:
                    print(f"❌ {attr}: Non disponibile nel dict")
            else:
                if hasattr(item, attr):
                    value = getattr(item, attr)
                    print(f"✅ {attr}: {type(value)} = {str(value)[:100]}...")
                else:
                    print(f"❌ {attr}: Non disponibile")
        
        # Test stats se esiste
        stats = item.get('stats') if isinstance(item, dict) else getattr(item, 'stats', None)
        if stats:
            print(f"\n=== STATS OBJECT ===")
            print(f"Stats type: {type(stats)}")
            if isinstance(stats, dict):
                print(f"Stats keys: {list(stats.keys())}")
                for key, value in stats.items():
                    value_str = str(value)[:100] if value is not None else "None" 
                    print(f"  {key}: {type(value)} = {value_str}...")
            else:
                print(f"Stats dir: {[attr for attr in dir(stats) if not attr.startswith('_')]}")
                
        # Test dati CSV se disponibili
        csv_data = item.get('csv') if isinstance(item, dict) else getattr(item, 'csv', None)
        if csv_data:
            print(f"\n=== CSV DATA ===")
            print(f"CSV type: {type(csv_data)}")
            if csv_data:
                print(f"CSV length: {len(csv_data) if hasattr(csv_data, '__len__') else 'Unknown'}")
                if hasattr(csv_data, 'keys'):
                    print(f"CSV keys: {list(csv_data.keys())}")
                elif isinstance(csv_data, (list, tuple)) and csv_data:
                    print(f"CSV first elements: {csv_data[:3] if len(csv_data) > 3 else csv_data}")
        
        # Cerchiamo tutti i possibili campi prezzi
        price_fields = ['price', 'prices', 'current', 'amazon', 'new', 'used', 'buyBox']
        print(f"\n=== RICERCA CAMPI PREZZO ===")
        for field in price_fields:
            if isinstance(item, dict) and field in item:
                value = item[field]
                print(f"✅ Found {field}: {type(value)} = {str(value)[:100]}...")
                
        return True
        
    except Exception as e:
        print(f"❌ Errore: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Keepa Debug Test")
    success = test_keepa_structure()
    print(f"\n{'✅ Success' if success else '❌ Failed'}")
