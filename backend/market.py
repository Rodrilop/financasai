import yfinance as yf
from typing import List, Dict
import math

BARSI_STOCKS = [
    {"ticker":"TAEE11","name":"Taesa","sector":"Energia – Transmissão"},
    {"ticker":"EGIE3", "name":"Engie Brasil","sector":"Energia – Geração"},
    {"ticker":"SAPR11","name":"Sanepar","sector":"Saneamento"},
    {"ticker":"VIVT3", "name":"Telefônica Brasil","sector":"Telecomunicações"},
    {"ticker":"BBAS3", "name":"Banco do Brasil","sector":"Banco Público"},
    {"ticker":"GRND3", "name":"Grendene","sector":"Calçados"},
    {"ticker":"GARE3", "name":"Guardian RE","sector":"Real Estate"},
    {"ticker":"CSNA3", "name":"CSN","sector":"Siderurgia"},
    {"ticker":"CPLE6", "name":"Copel","sector":"Energia Elétrica"},
    {"ticker":"PETR4", "name":"Petrobras PN","sector":"Petróleo"},
]

FIIS = [
    {"ticker":"MXRF11","name":"Maxi Renda","segment":"Híbrido"},
    {"ticker":"HGLG11","name":"CSHG Logística","segment":"Logística"},
    {"ticker":"VISC11","name":"Vinci Shopping","segment":"Shoppings"},
    {"ticker":"KNRI11","name":"Kinea Renda Imob.","segment":"Híbrido"},
    {"ticker":"XPML11","name":"XP Malls","segment":"Shoppings"},
]

def signal(dy, pvp):
    if dy is None or pvp is None:
        return "neutral"
    if dy > 6 and pvp < 2:
        return "buy"
    if dy > 4 and pvp < 2.5:
        return "neutral"
    return "wait"

def fetch_batch(items: List[Dict]) -> List[Dict]:
    results = []
    for item in items:
        try:
            t = yf.Ticker(f"{item['ticker']}.SA")
            info = t.info
            hist = t.history(period="5d")
            if hist.empty:
                price = change = None
            else:
                price = round(hist["Close"].iloc[-1], 2)
                prev = hist["Close"].iloc[-2] if len(hist) >= 2 else price
                change = round((price - prev) / prev * 100, 2) if prev else 0

            raw_dy = info.get("dividendYield", None)
            dy = round(raw_dy * 100, 2) if raw_dy else None
            pvp = info.get("priceToBook", None)
            pvp = round(pvp, 2) if pvp else None

            # Sanitize NaN values for JSON
            def clean_nan(val):
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    return None
                return val

            results.append({**item, 
                            "price": clean_nan(price), 
                            "change_pct": clean_nan(change),
                            "dy": clean_nan(dy), 
                            "pvp": clean_nan(pvp), 
                            "signal": signal(dy, pvp)})
        except Exception as e:
            results.append({**item, "price": None, "change_pct": None,
                            "dy": None, "pvp": None, "signal": "neutral", "error": str(e)})
    return results

def get_market_data() -> Dict:
    stocks = fetch_batch(BARSI_STOCKS)
    fiis = fetch_batch(FIIS)
    return {
        "stocks": sorted(stocks, key=lambda x: x.get("dy") or 0, reverse=True),
        "fiis":   sorted(fiis,   key=lambda x: x.get("dy") or 0, reverse=True),
    }

ALLOCATION = {
    "conservador": {"label":"Conservador","tesouro":50,"fiis":20,"acoes":10,"cdb":20,
                    "desc":"Foco em preservação de capital e renda estável."},
    "moderado":    {"label":"Moderado","tesouro":30,"fiis":30,"acoes":30,"cdb":10,
                    "desc":"Equilíbrio entre segurança e crescimento."},
    "agressivo":   {"label":"Agressivo","tesouro":10,"fiis":20,"acoes":60,"cdb":10,
                    "desc":"Foco em crescimento patrimonial no longo prazo."},
}

def get_allocation(profile: str, amount: float) -> Dict:
    alloc = ALLOCATION.get(profile, ALLOCATION["moderado"])
    return {
        "profile": alloc["label"],
        "description": alloc["desc"],
        "total": amount,
        "breakdown": [
            {"name":"Tesouro Selic","pct":alloc["tesouro"],"value":amount*alloc["tesouro"]/100,"color":"#10b981"},
            {"name":"FIIs","pct":alloc["fiis"],"value":amount*alloc["fiis"]/100,"color":"#3b82f6"},
            {"name":"Ações (B3)","pct":alloc["acoes"],"value":amount*alloc["acoes"]/100,"color":"#f59e0b"},
            {"name":"CDB/LCI/LCA","pct":alloc["cdb"],"value":amount*alloc["cdb"]/100,"color":"#8b5cf6"},
        ]
    }
