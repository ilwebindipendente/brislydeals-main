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
        print(f"Dir: {[attr for attr in dir(item) if not attr.startswith('_')]}")
        
        if hasattr(item, '__dict__'):
            print(f"Vars: {list(vars(item).keys())}")
            
        # Test attributi specifici
        attrs_to_test = ['asin', 'stats', 'csv', 'rating', 'reviewCount', 'categoryTree', 'buyBoxIsAmazon']
        
        print("\n=== ATTRIBUTI DISPONIBILI ===")
        for attr in attrs_to_test:
            if hasattr(item, attr):
                value = getattr(item, attr)
                print(f"✅ {attr}: {type(value)} = {str(value)[:100]}...")
            else:
                print(f"❌ {attr}: Non disponibile")
        
        # Test stats se esiste
        if hasattr(item, 'stats'):
            stats = getattr(item, 'stats')
            print(f"\n=== STATS OBJECT ===")
            print(f"Stats type: {type(stats)}")
            print(f"Stats dir: {[attr for attr in dir(stats) if not attr.startswith('_')]}")
            
            if hasattr(stats, '__dict__'):
                print(f"Stats vars: {list(vars(stats).keys())}")
                
        # Test dati CSV se disponibili
        if hasattr(item, 'csv'):
            csv_data = getattr(item, 'csv')
            print(f"\n=== CSV DATA ===")
            print(f"CSV type: {type(csv_data)}")
            if csv_data:
                print(f"CSV length: {len(csv_data) if hasattr(csv_data, '__len__') else 'Unknown'}")
                if hasattr(csv_data, 'keys'):
                    print(f"CSV keys: {list(csv_data.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Keepa Debug Test")
    success = test_keepa_structure()
    print(f"\n{'✅ Success' if success else '❌ Failed'}")
