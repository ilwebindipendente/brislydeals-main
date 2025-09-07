#!/usr/bin/env python3
"""
Test del nuovo client Keepa
"""

import os
from dotenv import load_dotenv
load_dotenv()

def main():
    print("🔬 Test New Keepa Client")
    
    try:
        from helpers.keepa_new import enrich_with_keepa
        print("✅ Nuovo client importato")
        
        # Test con ASIN che sappiamo funziona
        test_asin = "B0DC8VPSHV"
        print(f"Testing {test_asin}...")
        
        result = enrich_with_keepa(test_asin)
        
        if result:
            print("✅ SUCCESS! Dati ricevuti:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("❌ Nessun dato ricevuto")
            
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    main()
