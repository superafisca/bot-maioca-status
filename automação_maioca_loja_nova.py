#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import pytz
import requests
from datetime import datetime, timedelta

# ——— Configurações do Telegram ——————————————————————————————
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID          = os.environ.get("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# User-Agent para não ser bloqueado
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.5845.96 Safari/537.36"
    )
}

# ——— Lista de lojas ——————————————————————————————————————————
lojas = [
    {"nome": "Maioca João Paulo",         "url": "https://www.ifood.com/.../1dac79c4-12ac-4192-b2a9-73c47a732865"},
    {"nome": "Maioca Aeroporto",          "url": "https://www.ifood.com/.../b1147043-e9ca-4e65-82cd-759abd3fe2a5"},
    {"nome": "Maioca Doca",               "url": "https://www.ifood.com/.../c759bea8-fea3-445c-bb41-4f39955f6ba4"},
    {"nome": "Maioca Duque",              "url": "https://www.ifood.com/.../7008f4aa-9872-436d-9695-40ebd4293a2f"},
    {"nome": "Maioca Batista Campos",     "url": "https://www.ifood.com/.../2991e1e3-c04f-4a48-808e-2c14bd551c16"},
    {"nome": "Maioca Marambaia",          "url": "https://www.ifood.com/.../0838e072-e3de-4f04-bb22-6982710fb67e"},
    {"nome": "Maioca Metrópole",          "url": "https://www.ifood.com/.../c9561ee6-e402-401c-8b0c-759e2fed3ae8"},
    {"nome": "Maioca Vila Maguary",       "url": "https://www.ifood.com/.../392e792c-a05c-426e-a41b-50a95c66bc34"},
    {"nome": "Maioca Orla Ananindeua",    "url": "https://www.ifood.com/.../7ad1894c-df78-4fd3-9776-98ae48c75aea"},
    {"nome": "Maioca Augusto Montenegro", "url": "https://www.ifood.com/.../f86e63e1-fd3a-4887-8939-cc40a9edbba0"},
    {"nome": "Maioca Cidade Nova",        "url": "https://www.ifood.com/.../27006a9b-c192-468b-9c59-b5031e9ff579"},
    {"nome": "Maioca Bosque Grão",        "url": "https://www.ifood.com/.../783608ed-a2dd-47e9-bf3b-4113a7456b54"},
    {"nome": "Maioca Orla Icoaraci",      "url": "https://www.ifood.com/.../a1f95533-2f61-4534-83a7-d71bb34f03ee"},
    {"nome": "Maioca Parauapebas",        "url": "https://www.ifood.com/.../94cd194c-0b0e-4094-89b7-17f6164cd1bb"},
]

def send_to_telegram(texto: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN ou CHAT_ID não configurados.")
        return
    resp = requests.post(
        TELEGRAM_API_URL,
        data={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"},
        timeout=15
    )
    if resp.status_code != 200:
        print(f"❌ Erro ao enviar Telegram: {resp.status_code} / {resp.text}")
    else:
        print("✅ Mensagem enviada ao Telegram.")

def checar_status_loja(loja: dict) -> str:
    nome, url = loja["nome"], loja["url"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return f"❌ ERRO GERAL (HTTP {resp.status_code})"
        html = resp.text

        # Extrai o JSON do Next.js
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
            html, re.DOTALL
        )
        if not m:
            return "❓ STATUS DESCONHECIDO (JSON não encontrado)"
        data = json.loads(m.group(1))
        rest = data.get("props", {})\
                   .get("pageProps", {})\
                   .get("restaurante", {})

        agora = datetime.now(pytz.timezone("America/Belem"))
        closed = rest.get("closed")
        if closed is True:
            return "❌ FECHADA (JSON: closed=true)"
        if closed is False:
            # verifica turnos
            shifts = rest.get("shifts", [])
            hoje = agora.strftime("%A").upper()
            for t in shifts:
                if t.get("dayOfWeek", "").upper() == hoje:
                    start = t.get("start")
                    dur   = t.get("duration")
                    if start and isinstance(dur, int):
                        h, m, _ = map(int, start.split(":"))
                        ini = agora.replace(hour=h, minute=m, second=0, microsecond=0)
                        fim = ini + timedelta(minutes=dur)
                        if ini <= agora < fim:
                            return f"✅ ABERTA (JSON: {start}→{fim.strftime('%H:%M')})"
                        else:
                            return f"❌ FECHADA (JSON: turno {start}→{fim.strftime('%H:%M')})"
            return "❌ FECHADA (JSON: closed=false, sem turno hoje)"

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

    linhas = []
    for idx, loja in enumerate(lojas, start=1):
        print(f"({idx}/{len(lojas)}) Checando {loja['nome']} …")
        status = checar_status_loja(loja)
        linhas.append(f"*{loja['nome']}*: {status}")

    texto = header + "\n".join(linhas)
    send_to_telegram(texto)

if __name__ == "__main__":
    main()
