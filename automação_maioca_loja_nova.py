#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pytz
import requests
import re
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ——— Configurações do Telegram ————————————————————————————————
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID           = os.environ.get("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def send_to_telegram(texto: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN ou CHAT_ID não configurados.")
        return
    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(TELEGRAM_API_URL, data=payload, timeout=15)
        if resp.status_code != 200:
            print(f"❌ Erro ao enviar Telegram: HTTP {resp.status_code} / {resp.text}")
        else:
            print("✅ Mensagem enviada ao Telegram com sucesso.")
    except Exception as e:
        print(f"❌ Exceção ao tentar enviar ao Telegram: {e}")

# ========== LISTA DE LOJAS (NOME + URL) ==========
lojas = [
    {"nome": "Maioca João Paulo",         "url": "https://www...rveteria-artesanal-marco/1dac79c4-12ac-4192-b2a9-73c47a732865"},
    {"nome": "Maioca Aeroporto",          "url": "https://www...ia-artesanal-val-de-caes/b1147043-e9ca-4e65-82cd-759abd3fe2a5"},
    {"nome": "Maioca Doca",               "url": "https://www...teria-artesanal-umarizal/c759bea8-fea3-445c-bb41-4f39955f6ba4"},
    {"nome": "Maioca Duque",              "url": "https://www...teria-artesanal-pedreira/7008f4aa-9872-436d-9695-40ebd4293a2f"},
    {"nome": "Maioca Batista Campos",     "url": "https://www...artesanal-batista-campos/2991e1e3-c04f-4a48-808e-2c14bd551c16"},
    {"nome": "Maioca Marambaia",          "url": "https://www...anal-marambaia-marambaia/0838e072-e3de-4f04-bb22-6982710fb67e"},
    {"nome": "Maioca Metrópole",          "url": "https://www...teria-artesanal-coqueiro/c9561ee6-e402-401c-8b0c-759e2fed3ae8"},
    {"nome": "Maioca Vila Maguary",       "url": "https://www...veteria-artesanal-centro/392e792c-a05c-426e-a41b-50a95c66bc34"},
    {"nome": "Maioca Orla Ananindeua",    "url": "https://www...a-artesanal-icui-guajara/7ad1894c-df78-4fd3-9776-98ae48c75aea"},
    {"nome": "Maioca Augusto Montenegro", "url": "https://www...teria-artesanal-coqueiro/f86e63e1-fd3a-4887-8939-cc40a9edbba0"},
    {"nome": "Maioca Cidade Nova",        "url": "https://www...ia-artesanal-cidade-nova/27006a9b-c192-468b-9c59-b5031e9ff579"},
    {"nome": "Maioca Bosque Grão",        "url": "https://www...ria-artesanal-mangueirao/783608ed-a2dd-47e9-bf3b-4113a7456b54"},
    {"nome": "Maioca Orla Icoaraci",      "url": "https://www...esanal-cruzeiro-icoaraci/a1f95533-2f61-4534-83a7-d71bb34f03ee"},
    {"nome": "Maioca Parauapebas",        "url": "https://www...-artesanal-cidade-jardim/94cd194c-0b0e-4094-89b7-17f6164cd1bb"},
]

# ——— Função que checa o status de cada loja ——————————————————————
def checar_status_loja(driver, url: str, loja_nome: str) -> str:
    try:
        driver.get(url)
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        try:
            elem = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//button[contains(., 'Adicionar ao carrinho')]"
                     " | //p[contains(., 'Fechado')]")
                )
            )
        except TimeoutException:
            elem = None

        if elem:
            txt = elem.text.strip().lower()
            if "adicionar ao carrinho" in txt:
                return "✅ ABERTA (botão encontrado)"
            if "fechado" in txt:
                return "❌ FECHADA (texto ‘Fechado’ encontrado)"

        html = driver.page_source
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
            html,
            re.DOTALL
        )
        if match:
            data = json.loads(match.group(1))
            agora = datetime.now(pytz.timezone("America/Belem"))
            restaurante = data.get("props", {})\
                              .get("pageProps", {})\
                              .get("restaurante", {})
            is_closed = restaurante.get("closed", None)
            if is_closed is True:
                return "❌ FECHADA (JSON: closed=true)"
            if is_closed is False:
                shifts = restaurante.get("shifts", [])
                hoje = agora.strftime("%A").upper()
                for turno in shifts:
                    if turno.get("dayOfWeek", "").upper() == hoje:
                        start = turno.get("start")
                        dur   = turno.get("duration")
                        if start and isinstance(dur, int):
                            h, m, _ = map(int, start.split(":"))
                            ini = agora.replace(hour=h, minute=m, second=0, microsecond=0)
                            fim = ini + timedelta(minutes=dur)
                            if ini <= agora < fim:
                                return f"✅ ABERTA (JSON: {start}→{fim.strftime('%H:%M')})"
                            else:
                                return f"❌ FECHADA (JSON: turno {start}→{fim.strftime('%H:%M')})"
                return "❌ FECHADA (JSON: closed=false, sem turno hoje)"
            raise ValueError(f"JSON inesperado: closed={is_closed!r}")

        if re.search(r"fechado", html, re.IGNORECASE):
            return "❌ FECHADA (fallback texto)"
        return "❓ STATUS DESCONHECIDO"

    except Exception as e:
        print(f"❌ Erro geral em '{loja_nome}': {e}")
        return f"❌ ERRO GERAL ({type(e).__name__})"

# ——— Monta o relatório para todas as lojas ——————————————————————
def gerar_relatorio_completo(driver) -> str:
    fuso = pytz.timezone("America/Belem")
    agora = datetime.now(fuso)
    header = (
        "*Relatório de Status das Lojas*\n"
        f"_Atualizado em: {agora.strftime('%d/%m/%Y %H:%M:%S')} "
        "(Fuso: America/Belem)_\n\n"
    )
    linhas = []
    for idx, loja in enumerate(lojas, start=1):
        print(f"({idx}/{len(lojas)}) Checando \"{loja['nome']}\" …")
        status = checar_status_loja(driver, loja["url"], loja["nome"])
        linhas.append(f"*{loja['nome']}*: {status}")
    return header + "\n".join(linhas)

# ——— Ponto de entrada —————————————————————————————————————————
def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    try:
        texto = gerar_relatorio_completo(driver)
        send_to_telegram(texto)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
