import os
import json
import pytz
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== CONFIG TELEGRAM ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
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
            print("✅ Mensagem enviada ao Telegram.")
    except Exception as e:
        print(f"❌ Exceção ao enviar ao Telegram: {e}")

# ========== LISTA DE LOJAS ==========
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

# ========== VERIFICAÇÃO DE STATUS ==========
def checar_status_loja(driver, url, nome_loja):
    try:
        driver.get(url)

        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        chave = driver.page_source.lower()
        if "fechado" in chave and "adicionar ao carrinho" not in chave:
            return "❌ FECHADA"

        if "adicionar ao carrinho" in chave:
            return "✅ ABERTA"

        return "❓ INDEFINIDO"
    except Exception as e:
        return f"❌ ERRO ({type(e).__name__})"

# ========== RELATÓRIO ==========
def gerar_relatorio(driver):
    fuso = pytz.timezone("America/Belem")
    agora = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
    relatorio = f"*Relatório de Status das Lojas*\n_Atualizado em: {agora}_\n\n"

    for idx, loja in enumerate(lojas, 1):
        nome = loja["nome"]
        url = loja["url"]
        print(f"({idx}/{len(lojas)}) Checando {nome}...")
        status = checar_status_loja(driver, url, nome)
        relatorio += f"*{nome}*: {status}\n"

    return relatorio

# ========== EXECUÇÃO ==========
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

    # Caminhos fixos para ambiente do Render
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chromedriver_path = "/usr/bin/chromedriver"

    from selenium.webdriver.chrome.service import Service
service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        texto = gerar_relatorio(driver)
        send_to_telegram(texto)
    except Exception as e:
        print(f"❌ Erro geral: {e}")
    finally:
        driver.quit()
