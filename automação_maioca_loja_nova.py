#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import pytz
import requests
from datetime import datetime, timedelta

# ——— CONFIGURAÇÃO TELEGRAM ————————————————————————————————
TELEGRAM_TOKEN   = "8064932590:AAFOu6KbR84kYs18SRSpiD5b8pd_vbL9Mv0"
CHAT_ID          = "7024048337"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# ——— HEADERS como browser real —————————————————————————————
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.5845.96 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9"
}

# ——— LISTA COMPLETA DE 14 LOJAS —————————————————————————————
lojas = [
    {"nome": "Maioca João Paulo",         "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-joao-paulo---sorveteria-artesanal-marco/1dac79c4-12ac-4192-b2a9-73c47a732865"},
    {"nome": "Maioca Aeroporto",          "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-aeroporto-belem---sorveteria-artesanal-val-de-caes/b1147043-e9ca-4e65-82cd-759abd3fe2a5"},
    {"nome": "Maioca Doca",               "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-doca---sorveteria-artesanal-umarizal/c759bea8-fea3-445c-bb41-4f39955f6ba4"},
    {"nome": "Maioca Duque",              "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-duque---sorveteria-artesanal-pedreira/7008f4aa-9872-436d-9695-40ebd4293a2f"},
    {"nome": "Maioca Batista Campos",     "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-batista-campos---sorveteria-artesanal-batista-campos/2991e1e3-c04f-4a48-808e-2c14bd551c16"},
    {"nome": "Maioca Marambaia",          "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-sorveteria-artesanal-marambaia-marambaia/0838e072-e3de-4f04-bb22-6982710fb67e"},
    {"nome": "Maioca Metrópole",          "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-metropole---sorveteria-artesanal-coqueiro/c9561ee6-e402-401c-8b0c-759e2fed3ae8"},
    {"nome": "Maioca Vila Maguary",       "url": "https://www.ifood.com.br/delivery/ananindeua-pa/maioca-parque-vila-maguary---sorveteria-artesanal-centro/392e792c-a05c-426e-a41b-50a95c66bc34"},
    {"nome": "Maioca Orla Ananindeua",    "url": "https://www.ifood.com.br/delivery/ananindeua-pa/maioca-orla-ananindeua---sorveteria-artesanal-icui-guajara/7ad1894c-df78-4fd3-9776-98ae48c75aea"},
    {"nome": "Maioca Augusto Montenegro", "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-augusto-montenegro---sorveteria-artesanal-coqueiro/f86e63e1-fd3a-4887-8939-cc40a9edbba0"},
    {"nome": "Maioca Cidade Nova",        "url": "https://www.ifood.com.br/delivery/ananindeua-pa/maioca-cidade-nova---sorveteria-artesanal-cidade-nova/27006a9b-c192-468b-9c59-b5031e9ff579"},
    {"nome": "Maioca Bosque Grão",        "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-bosque-grao---sorveteria-artesanal-mangueirao/783608ed-a2dd-47e9-bf3b-4113a7456b54"},
    {"nome": "Maioca Orla Icoaraci",      "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-orla-icoaraci---sorveteria-artesanal-cruzeiro-icoaraci/a1f95533-2f61-4534-83a7-d71bb34f03ee"},
    {"nome": "Maioca Parauapebas",        "url": "https://www.ifood.com.br/delivery/parauapebas-pa/maioca-paraupebas---sorveteria-artesanal-cidade-jardim/94cd194c-0b0e-4094-89b7-17f6164cd1bb"},
]

def send_to_telegram(text: str):
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    r = requests.post(TELEGRAM_API_URL, data=payload, timeout=15)
    if r.status_code == 200:
        print("✅ Mensagem enviada ao Telegram.")
    else:
        print(f"❌ Telegram erro {r.status_code}: {r.text}")

def checar_status_loja(loja: dict) -> str:
    nome, url = loja["nome"], loja["url"]
    print(f"Checando {nome} …")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return f"❌ ERRO GERAL (HTTP {resp.status_code})"
        html = resp.text

        # 1) Tenta JSON Next.js
        m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                      html, re.DOTALL|re.IGNORECASE)
        if m:
            data = json.loads(m.group(1))
            rest = data.get("props", {})\
                       .get("pageProps", {})\
                       .get("restaurante", {})
            agora  = datetime.now(pytz.timezone("America/Belem"))
            closed = rest.get("closed")
            if closed is True:
                return "❌ FECHADA (JSON: closed=true)"
            if closed is False:
                shifts = rest.get("shifts", [])
                hoje   = agora.strftime("%A").upper()
                for t in shifts:
                    if t.get("dayOfWeek","").upper() == hoje:
                        start, dur = t.get("start"), t.get("duration")
                        if start and isinstance(dur,int):
                            h,m,_ = map(int, start.split(":"))
                            ini = agora.replace(hour=h, minute=m, second=0)
                            fim = ini + timedelta(minutes=dur)
                            if ini <= agora < fim:
                                return f"✅ ABERTA (JSON: {start}→{fim.strftime('%H:%M')})"
                            else:
                                return f"❌ FECHADA (JSON: turno {start}→{fim.strftime('%H:%M')})"
                return "❌ FECHADA (JSON: closed=false, sem turno hoje)"
        # 2) Fallback por texto no HTML
        low = html.lower()
        if "adicionar ao carrinho" in low:
            return "✅ ABERTA (texto encontrado)"
        if "fechado" in low:
            return "❌ FECHADA (texto encontrado)"
        return "❓ STATUS DESCONHECIDO"

    except Exception as e:
        return f"❌ ERRO GERAL ({type(e).__name__})"

def main():
    fuso = pytz.timezone("America/Belem")
    agora = datetime.now(fuso)
    header = (
        "*Relatório de Status das Lojas*\n"
        f"_Atualizado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}_ (Fuso: America/Belem)\n\n"
    )
    lines = []
    for loja in lojas:
        status = checar_status_loja(loja)
        lines.append(f"*{loja['nome']}*: {status}")
    texto = header + "\n".join(lines)
    send_to_telegram(texto)

if __name__ == "__main__":
    main()
