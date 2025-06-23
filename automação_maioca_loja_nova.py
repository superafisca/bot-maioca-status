#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
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

# ===== CONFIGURAÇÕES TELEGRAM =====
TELEGRAM_TOKEN = "8064932590:AAFOu6KbR84kYs18SRSpiD5b8pd_vbL9Mv0"
CHAT_ID = "7024048337"  # Substitua pelo seu chat_id real
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def send_to_telegram(texto: str):
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

# ===== LISTA COMPLETA DE LOJAS =====
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

# ===== CONFIGURAÇÃO À PROVA DE CRASHES =====
def criar_navegador():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Evita travamentos
    chrome_options.add_argument("window-size=1280,800")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/98.0.4758.102 Safari/537.36"
    )
    return webdriver.Chrome(options=chrome_options)

# ===== FUNÇÃO DE CHECAGEM (MESMA LÓGICA ORIGINAL) =====
def checar_status_loja(url: str, loja_nome: str) -> str:
    driver = criar_navegador()
    try:
        driver.get(url)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Lógica original de verificação (ABERTA/FECHADA)
        html = driver.page_source.lower()
        if "fechado" in html and "adicionar ao carrinho" not in html:
            return "❌ FECHADA"
        elif "adicionar ao carrinho" in html:
            return "✅ ABERTA"
        else:
            return "⚠️ INDETERMINADO"
            
    except Exception as e:
        return f"❌ ERRO ({type(e).__name__})"
    finally:
        driver.quit()  # Fecha o navegador!

# ===== RELATÓRIO + PAUSAS =====
def gerar_relatorio_completo():
    cabecalho = f"*Relatório das Lojas Maioca*\n_Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_\n\n"
    linhas = []
    
    for loja in lojas:
        try:
            status = checar_status_loja(loja["url"], loja["nome"])
            linhas.append(f"*{loja['nome']}*: {status}")
            time.sleep(15)  # Pausa de 15s entre lojas (evita sobrecarga)
        except Exception as e:
            linhas.append(f"*{loja['nome']}*: ❌ ERRO TEMPORÁRIO")
    
    return cabecalho + "\n".join(linhas)

# ===== LOOP PRINCIPAL =====
if __name__ == "__main__":
    while True:
        try:
            print("🔄 Iniciando verificação...")
            relatorio = gerar_relatorio_completo()
            send_to_telegram(relatorio)
        except Exception as e:
            print(f"💥 Erro grave: {e}")
            send_to_telegram(f"⚠️ O script reiniciou. Erro: {str(e)}")
        
        print("⏳ Aguardando 30 minutos...")
        time.sleep(30 * 60)  # Espera 30 minutos
