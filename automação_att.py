#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import pytz
import requests

from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== CONFIGURAÇÕES TELEGRAM ==========
TELEGRAM_TOKEN = "8064932590:AAFOu6KbR84kYs18SRSpiD5b8pd_vbL9Mv0"
CHAT_ID       = "7024048337"  # <— use o chat_id correto do seu bot

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


# ========== LISTA DE LOJAS (NOME + URL) ==========
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
    {"nome": "Maioca Alcindo",            "url": "https://www.ifood.com.br/delivery/belem-pa/maioca-alcindo---sorveteria-artesanal-umarizal/1763b6b7-b983-4ac8-bad6-d612a72ead05"},
]


# ========== FUNÇÃO DE CHECAGEM DE UMA ÚNICA LOJA ==========
def checar_status_loja(driver, url: str, loja_nome: str) -> str:
    """
    1) Abre a página da loja.
    2) Espera até 25s o <body> carregar.
    3) Espera até 20s para aparecer:
       - O botão “Adicionar ao carrinho”    OU
       - Qualquer texto contendo “Fechado” 
       (os dois em um único XPath).
    4) Se achar o botão “Adicionar ao carrinho” habilitado, retorna “ABERTA”.
    5) Se achar texto “Fechado” (sem botão), retorna “FECHADA”.
    6) Caso nenhum dos dois apareça em 20s, tenta JSON __NEXT_DATA__.
    7) Se JSON falhar, faz fallback textual simples (regex no HTML).
    """

    try:
        driver.get(url)

        # 1) Espera até que o <body> esteja carregado (timeout = 25s)
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 2) Agora aguarda até que EXISTAM no DOM pelo menos UM dos dois:
        #    - Botão “Adicionar ao carrinho”
        #    - Texto “Fechado” (pode ser banner ou mensagem)
        xpath_condicao = "//*[contains(text(),'Adicionar ao carrinho') or contains(text(),'Fechado')]"
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, xpath_condicao))
            )
        except:
            # Se 20s passarem e nenhum aparecer, seguimos adiante mesmo assim
            pass

        html = driver.page_source
        chave = html.lower()

        # 3) Se encontrar texto “fechado” e não houver “adicionar ao carrinho”, retorna FECHADA
        if "fechado" in chave and "adicionar ao carrinho" not in chave:
            return "❌ FECHADA (detectou texto ‘Fechado’ no HTML)"

        # 4) Se encontrar “Adicionar ao carrinho” (botão) e ele estiver habilitado, retorna ABERTA
        #    Vamos tentar pegar especificamente o botão “Adicionar ao carrinho”.
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(text(),'Adicionar ao carrinho')]")
            # Se estiver visível e habilitado, consideramos aberto:
            if btn.is_displayed() and btn.is_enabled():
                return "✅ ABERTA (botão “Adicionar ao carrinho” disponível)"
        except:
            # Se não achar o botão, continua adiante
            pass

        # 5) Se nem “Fechado” nem botão “Adicionar” foi decisivo, tentamos JSON __NEXT_DATA__
        try:
            elem_json = driver.find_element(By.ID, "__NEXT_DATA__")
            json_text = elem_json.get_attribute("textContent")
            dados = json.loads(json_text)

            restaurante = {}
            if (
                "props" in dados
                and "pageProps" in dados["props"]
                and "initialState" in dados["props"]["pageProps"]
            ):
                restaurante = (
                    dados["props"]["pageProps"]
                    .get("initialState", {})
                    .get("restaurant", {})
                    .get("details", {})
                )
            if not restaurante:
                restaurante = (
                    dados.get("props", {})
                    .get("initialState", {})
                    .get("restaurant", {})
                    .get("details", {})
                )

            if not restaurante:
                raise ValueError("JSON carregado, mas não encontrou 'restaurant.details'")

            is_closed = restaurante.get("closed", None)
            tz_loja = restaurante.get("timezone", "America/Belem")
            try:
                store_tz = pytz.timezone(tz_loja)
            except:
                store_tz = pytz.timezone("America/Belem")

            agora = datetime.now(store_tz)
            dia_map = {
                0: "MONDAY", 1: "TUESDAY", 2: "WEDNESDAY",
                3: "THURSDAY", 4: "FRIDAY", 5: "SATURDAY", 6: "SUNDAY"
            }
            hoje_str = dia_map[agora.weekday()]

            # JSON indica fechado?
            if is_closed is True:
                prox = restaurante.get("nextopeninghour", {})
                if prox and "dayofweek" in prox:
                    dias_pt = {
                        "mon": "Seg", "tue": "Ter", "wed": "Qua",
                        "thu": "Qui", "fri": "Sex", "sat": "Sáb", "sun": "Dom"
                    }
                    abertura_dia = dias_pt.get(prox["dayofweek"].lower(), prox["dayofweek"])
                    return f"❌ FECHADA (JSON: próxima abertura {abertura_dia})"
                return "❌ FECHADA (JSON: closed = true)"

            # JSON indica aberto?
            if is_closed is False:
                shifts = restaurante.get("shifts", [])
                if not shifts:
                    return "❌ FECHADA (JSON: closed=false, mas sem shifts definidos)"

                for turno in shifts:
                    if turno.get("dayOfWeek", "").upper() == hoje_str:
                        start_str = turno.get("start", None)
                        dur = turno.get("duration", None)
                        if not start_str or not isinstance(dur, int):
                            continue
                        h, m, s = map(int, start_str.split(":"))
                        inicio = agora.replace(hour=h, minute=m, second=s, microsecond=0)
                        fim = inicio + timedelta(minutes=dur)
                        if inicio <= agora < fim:
                            return f"✅ ABERTA (JSON: dentro do horário {start_str}→{fim.strftime('%H:%M:%S')})"
                        else:
                            return f"❌ FECHADA (JSON: turno hoje {start_str}→{fim.strftime('%H:%M:%S')}, mas fora do horário)"

                return "❌ FECHADA (JSON: closed=false, mas sem turno hoje)"

            # Caso inesperado no JSON:
            raise ValueError(f"JSON: chave 'closed' inesperada: {is_closed!r}")

        except Exception as e_json:
            # Se falha no processamento do JSON, grava HTML pra debug
            os.makedirs("debug_html", exist_ok=True)
            ts = datetime.now(pytz.timezone("America/Belem")).strftime("%Y%m%d_%H%M%S")
            safe = re.sub(r'[^0-9A-Za-z_-]', '_', loja_nome)
            fname = f"debug_html/{safe}_{ts}.html"
            with open(fname, "w", encoding="utf-8") as f_debug:
                f_debug.write(html)
            print(f"⚠️ Erro ao processar JSON em '{loja_nome}': {e_json}\n   HTML salvo em {fname}")

        # 6) Fallback textual simples
        chave = html.lower()
        if "fechado" in chave and "adicionar ao carrinho" not in chave:
            return "❌ FECHADA (Fallback textual: encontrou ‘fechado’)"
        if "adicionar ao carrinho" in chave:
            return "✅ ABERTA (Fallback textual: encontrou ‘Adicionar ao carrinho’)"
        if "aberto" in chave:
            return "✅ ABERTA (Fallback textual: encontrou ‘aberto’)"
        return "✅ ABERTA (Fallback final)"

    except Exception as e_geral:
        tipo = type(e_geral).__name__
        return f"❌ ERRO GERAL ({tipo})"


# ========== FUNÇÃO QUE GERA O RELATÓRIO COMPLETO ==========
def gerar_relatorio_completo(driver) -> str:
    fuso = pytz.timezone("America/Belem")
    agora = datetime.now(fuso)
    data_fmt = agora.strftime("%d/%m/%Y %H:%M:%S")
    cabecalho = (
        f"*Relatório de Status das Lojas*\n"
        f"_Atualizado em: {data_fmt} (Fuso: America/Belem)_\n\n"
    )

    linhas = []
    for idx, loja in enumerate(lojas, start=1):
        nome = loja["nome"]
        url  = loja["url"]
        print(f"({idx}/{len(lojas)}) Checando \"{nome}\" …")
        status = checar_status_loja(driver, url, nome)
        linhas.append(f"*{nome}*: {status}")

    corpo = "\n".join(linhas)
    return cabecalho + corpo


# ========== LOOP PRINCIPAL (envia a cada 30 minutos para o Telegram) ==========
if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/98.0.4758.102 Safari/537.36"
    )

    # Se precisar especificar o caminho absoluto pro ChromeDriver, faça assim:
    # driver = webdriver.Chrome(executable_path="/caminho/para/chromedriver", options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        while True:
            try:
                texto = gerar_relatorio_completo(driver)
                send_to_telegram(texto)
            except Exception as e_loop:
                print(f"❌ Erro no laço principal: {e_loop}")

            print("⏱️ Aguardando 30 minutos até a próxima atualização...\n")
            time.sleep(30 * 60)

    finally:
        driver.quit()
