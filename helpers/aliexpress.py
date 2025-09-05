from typing import List, Dict
from config import USE_ALIEXPRESS

def fetch_aliexpress_candidates() -> List[Dict]:
    if not USE_ALIEXPRESS:
        return []
    # TODO: Integrare API/Feed AliExpress quando disponibili.
    # Struttura compatibile con formatter:
    return []
