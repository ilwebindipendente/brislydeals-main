#!/usr/bin/env python3
"""
Script di test per debugging del sistema BrislyDeals
Uso: python test_debug.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_config():
    """Test configurazione"""
    print("=== TEST CONFIGURAZIONE ===")
    
    required_vars = [
        "API_ID", "API_HASH", "BOT_TOKEN", 
        "AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY",
        "KEEPA_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Variabili mancanti: {', '.join(missing)}")
        return False
    else:
        print("✅ Tutte le variabili richieste sono configurate")
        return True

def test_imports():
    """Test import dei moduli"""
    print("\n=== TEST IMPORT ===")
    
    modules = [
        ("telethon", "TelegramClient"),
        ("amazon_paapi", "AmazonApi"),  
        ("keepa", "Keepa"),
        ("upstash_redis", "Redis")
    ]
    
    success = True
    for module, cls in modules:
        try:
            mod = __import__(module)
            if hasattr(mod, cls):
                print(f"✅ {module}.{cls}")
            else:
                print(f"⚠️  {module} importato ma {cls} non trovato")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            success = False
    
    return success

def test_amazon_api():
    """Test API Amazon"""
    print("\n=== TEST AMAZON API ===")
    
    try:
        from helpers.amazon import search_candidates_for_keyword
        print("✅ Modulo amazon importato")
        
        # Test con keyword semplice
        print("Testing search con 'cuffie bluetooth'...")
        results = search_candidates_for_keyword("cuffie bluetooth")
        
        if results:
            print(f"✅ Trovati {len(results)} prodotti")
            for i, item in enumerate(results[:3], 1):
                print(f"  {i}. {item['title'][:50]}... - {item['discount_pct']}% - {item['price_now']}€")
        else:
            print("⚠️  Nessun prodotto trovato")
            
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Errore Amazon API: {e}")
        return False

def test_keepa_api():
    """Test API Keepa"""
    print("\n=== TEST KEEPA API ===")
    
    try:
        from helpers.keepa_client import enrich_with_keepa
        print("✅ Modulo keepa importato")
        
        # Test con ASIN di esempio
        test_asin = "B0DC8VPSHV"
        print(f"Testing con ASIN: {test_asin}")
        
        result = enrich_with_keepa(test_asin)
        
        if result:
            print(f"✅ Keepa data ricevuti:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            return True
        else:
            print("⚠️  Nessun dato Keepa ricevuto")
            return False
            
    except Exception as e:
        print(f"❌ Errore Keepa API: {e}")
        return False

def test_redis_connection():
    """Test connessione Redis"""
    print("\n=== TEST REDIS ===")
    
    try:
        from helpers.redis_store import get_client, cache_set, cache_get
        
        client = get_client()
        if client:
            print("✅ Client Redis configurato")
            
            # Test set/get
            test_key = "test_key"
            test_value = {"test": "value"}
            
            cache_set(test_key, test_value, 60)
            retrieved = cache_get(test_key)
            
            if retrieved == test_value:
                print("✅ Cache set/get funziona")
                return True
            else:
                print("⚠️  Cache set/get non funziona correttamente")
                return False
        else:
            print("⚠️  Redis non configurato, usando memoria locale")
            return True
            
    except Exception as e:
        print(f"❌ Errore Redis: {e}")
        return False

def test_full_pipeline():
    """Test pipeline completo"""
    print("\n=== TEST PIPELINE COMPLETO ===")
    
    try:
        from helpers.selector import gather_candidates, enrich_and_rank
        
        print("Gathering candidates...")
        candidates = gather_candidates()
        print(f"✅ Trovati {len(candidates)} candidati")
        
        if candidates:
            print("Enriching and ranking...")
            ranked = enrich_and_rank(candidates)
            print(f"✅ Ranked {len(ranked)} prodotti")
            
            if ranked:
                top = ranked[0]
                print(f"Top product: {top['title'][:50]}... - Score: {top.get('score', 0)}/5")
                return True
                
        return len(candidates) > 0
        
    except Exception as e:
        print(f"❌ Errore pipeline: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 BrislyDeals Debug Test\n")
    
    tests = [
        ("Configurazione", test_config),
        ("Import moduli", test_imports),
        ("Amazon API", test_amazon_api),
        ("Keepa API", test_keepa_api), 
        ("Redis", test_redis_connection),
        ("Pipeline completo", test_full_pipeline)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ ERRORE CRITICO in {name}: {e}")
            results[name] = False
    
    print("\n=== RISULTATI FINALI ===")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
    
    total_pass = sum(results.values())
    total_tests = len(results)
    print(f"\n📊 {total_pass}/{total_tests} test passati")
    
    if total_pass == total_tests:
        print("🎉 Tutti i test passati! Il sistema dovrebbe funzionare.")
    else:
        print("⚠️  Alcuni test falliti. Controllare i log sopra per i dettagli.")

if __name__ == "__main__":
    main()
