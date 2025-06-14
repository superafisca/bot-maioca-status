#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import re
import json
import pytz
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_telegram(mensagem: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID como variáveis de ambiente.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code != 200:
            print(f"❌ ERRO Telegram: HTTP {resp.status_code} / {resp.text}")
        else:
            print("✅ Mensagem enviada.")
    except Exception as e:
        print(f"❌ Exceção Telegram: {e}")

# ========== LISTA DE LOJAS (NOME + URL) ==========
lojas = [
    {"nome": "Maioca João Paulo",         "url": "https://www.i...teria-artesanal-marco/1dac79c4-12ac-4192-b2a9-73c47a732865"},
    {"nome": "Maioca Aeroporto",          "url": "https://www.i...ia-artesanal-val-de-caes/b1147043-e9ca-4e65-82cd-759abd3fe2a5"},
    {"nome": "Maioca Doca",               "url": "https://www.i...teria-artesanal-umarizal/c759bea8-fea3-445c-bb41-4f39955f6ba4"},
    {"nome": "Maioca Duque",              "url": "https://www.i...teria-artesanal-pedreira/7008f4aa-9872-436d-9695-40ebd4293a2f"},
    {"nome": "Maioca Batista Campos",     "url": "https://www.i...artesanal-batista-campos/2991e1e3-c04f-4a48-808e-2c14bd551c16"},
    {"nome": "Maioca Marambaia",          "url": "https://www.i...anal-marambaia-marambaia/0838e072-e3de-4f04-bb22-6982710fb67e"},
    {"nome": "Maioca Metrópole",          "url": "https://www.i...teria-artesanal-coqueiro/c9561ee6-e402-401c-8b0c-759e2fed3ae8"},
    {"nome": "Maioca Vila Maguary",       "url": "https://www.i...veteria-artesanal-centro/392e792c-a05c-426e-a41b-50a95c66bc34"},
    {"nome": "Maioca Orla Ananindeua",    "url": "https://www.i...a-artesanal-icui-guajara/7ad1894c-df78-4fd3-9776-98ae48c75aea"},
    {"nome": "Maioca Augusto Montenegro", "url": "https://www.i...teria-artesanal-coqueiro/f86e63e1-fd3a-4887-8939-cc40a9edbba0"},
    {"nome": "Maioca Cidade Nova",        "url": "https://www.i...ia-artesanal-cidade-nova/27006a9b-c192-468b-9c59-b5031e9ff579"},
    {"nome": "Maioca Alcindo",            "url": "https://www.i...teria-artesanal-umarizal/1763b6b7-b983-4ac8-bad6-d612a72ead05"},
]

def checar_status_loja(url: str, loja_nome: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return f"❌ ERRO HTTP {resp.status_code}"
        html = resp.text

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                      html, re.DOTALL)
        if not m:
            return "❌ ERRO: não encontrou __NEXT_DATA__"
        dados = json.loads(m.group(1))

        detalhes = (
            dados.get("props", {})
                 .get("pageProps", {})
                 .get("initialState", {})
                 .get("restaurant", {})
                 .get("details", {})
        )
        if not detalhes:
            return "❌ ERRO: JSON sem restaurant.details"
        if detalhes.get("closed"):
            return "❌ FECHADA (closed=true)"

        tz = pytz.timezone(detalhes.get("timezone", "America/Belem"))
        agora = datetime.now(tz)
        dias = ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY",
                "SATURDAY","SUNDAY"]
        hoje = dias[agora.weekday()]

        for turno in detalhes.get("shifts", []):
            if turno.get("dayOfWeek","").upper() != hoje:
                continue
            start = turno.get("start")
            dur   = turno.get("duration")
            if not start or not isinstance(dur, int):
                continue
            h, m, s = map(int, start.split(":"))
            inicio = agora.replace(hour=h, minute=m, second=s,
                                   microsecond=0)
            fim    = inicio + timedelta(minutes=dur)
            if inicio <= agora < fim:
                return f"✅ ABERTA ({start}→{fim.strftime('%H:%M')})"
            else:
                return f"❌ FECHADA (fora {start}→{fim.strftime('%H:%M')})"

        return "❌ FECHADA (sem turno hoje)"

    except Exception as e:
        ts   = datetime.now(pytz.timezone("America/Belem")) \
                       .strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r'[^0-9A-Za-z_-]', '_', loja_nome)
        pasta = "debug_html"
        os.makedirs(pasta, exist_ok=True)
        fname = f"{pasta}/{safe}_{ts}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
        return f"❌ ERRO em '{loja_nome}': {e}. HTML salvo em {fname}"

def gerar_relatorio() -> str:
    agora = datetime.now(pytz.timezone("America/Belem"))
    cab   = (f"*Relatório de Status das Lojas*\n"
             f"`{agora.strftime('%Y-%m-%d %H:%M:%S')}`\n\n")
    linhas = []
    for loja in lojas:
        status = checar_status_loja(loja["url"], loja["nome"])
        linhas.append(f"*{loja['nome']}*: {status}")
    return cab + "\n".join(linhas)

if __name__ == "__main__":
    while True:
        try:
            texto = gerar_relatorio()
            enviar_telegram(texto)
        except Exception as e:
            print(f"❌ Erro principal: {e}")
        print("⏱️ Esperando 30 min…")
        time.sleep(30 * 60)
