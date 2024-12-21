import time
import asyncio
import requests
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import tempfile
from pyrogram.types import InputMediaPhoto


TOKEN = "7417349320:AAETj2PU3KwnQJOQARAQWNwoKdRQWoMjIWA"
API_ID = "23542447"
API_HASH = "f88794e105fa8fb1900f2b933f8a5494"
GATEWAY_API_KEY = "0cdad91d-6f09-4c30-b894-bfa664e6de7b"


async def gerar_pix(valor: float, descricao: str) -> dict:
    url = "https://pix.evopay.cash/v1/pix"
    payload = {
        "amount": valor,
    }
    headers = {
        "API-Key": GATEWAY_API_KEY,
        "Content-Type": "application/json"
    }
    retries = 5
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(response.json())
                return response.json()
        
            else:
                raise Exception(f"Erro na API de Pix: {response.status_code} - {response.text}")
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                raise Exception("Erro ao gerar Pix: O servidor demorou muito para responder. Tente novamente mais tarde.")


async def verificacao(id):
    headers = {'API-Key': GATEWAY_API_KEY}
    response = requests.get(f"https://pix.evopay.cash/v1/pix?id={id}", headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        status = response_data.get("status")
        if status == "COMPLETED":
            return "pago"
        else:
            return False
    else:
        return False

async def start(client, message):
    message_text = (
        "Seja bem-vindo! Este bot foi feito pelo @Fenomeno33 e oferece serviços de atestados médicos "
        "e receitas médicas válidos em todo o Brasil.\n\n"
        "⏳ Compre com antecedência, pois nossa demanda é alta e podem ocorrer atrasos.\n\n"
        "🚨 Após finalizar o pagamento, envie o comprovante para o Suporte: @Fenomeno33."
    )
    keyboard = [
        [InlineKeyboardButton("🏥 Atestado Médico", callback_data="atestado")],
        [InlineKeyboardButton("💊 Receita Branca C1", callback_data="receita_branca")],
        [InlineKeyboardButton("🎧 Suporte", url="https://t.me/Fenomeno33")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(message_text, reply_markup=reply_markup)

async def selecionar_valor(client, message):
    query = message
    if query.data == "atestado":
        keyboard = [
            [InlineKeyboardButton("R$45,00 - São Paulo", callback_data="pagar_45_sp")],
            [InlineKeyboardButton("R$50,00 - Outros Estados", callback_data="pagar_50_outros")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Atestados Médicos\n\n"
            "✅ Originais, emitidos por médicos ativos.\n"
            "✅ Exclusivo para UPA, AMA e UBS (segurança garantida).\n\n"
            "Preços:\n"
            "🔸 R$45,00 para SP\n"
            "🔸 R$50,00 para outros estados",
            reply_markup=reply_markup,
        )
    elif query.data == "receita_branca":
        keyboard = [
            [InlineKeyboardButton("Confirmar Pagamento - R$50,00", callback_data="pagar_50")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Receitas Médicas\n\n"
            "✅ Receitas brancas (C1) para medicamentos controlados.\n"
            "✅ Exemplo: Codeína, Ozempic, Zolpidem, Sertralina, etc.\n\n"
            "Preço:\n"
            "🔸 R$50,00",
            reply_markup=reply_markup,
        )



async def gerar_pagamento(client, message):
    query = message
    if query.data == "pagar_45_sp":
        valor = 45
        descricao = "Atestado Médico - São Paulo"
    elif query.data == "pagar_50_outros":
        valor = 50
        descricao = "Atestado Médico - Outros Estados"
    elif query.data == "pagar_50":
        valor = 1
        descricao = "Receita Branca C1"
    else:
        await query.edit_message_text("Erro ao processar a solicitação.")
        return

    await query.edit_message_text("🔄 Gerando Pix... Aguarde alguns segundos.")
    try:
        pix_data = await gerar_pix(valor, descricao)
        
        qr_code_url = pix_data["qrCodeUrl"]
        qr_code_text = pix_data["qrCodeText"]

    
        response = requests.get(qr_code_url)
        response.raise_for_status() 

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name 
    
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=qr_code_url, 
                caption=(
                    f"🔸 Pagamento Gerado\n\n"
                    f"🎯 Serviço: {descricao}\n"
                    f"💰 Valor: R${valor}\n\n"
                    f"⏳ Prazo de expiração: 30 minutos\n\n"
                    f"PIX copia e cola:\n\n"
                    f"<code>{qr_code_text}</code>\n\n"
                    "1. Copie o código acima clicando nele.\n"
                    "2. Acesse seu aplicativo bancário favorito e use a opção PIX (copia e cola).\n"
                    "3. Efetue o pagamento e envie o comprovante para o suporte."
                ),
            )
        )
        
    
        await asyncio.sleep(10)

    
        for _ in range(50):
            try:
                id = pix_data.get("id") 

                verificar = await verificacao(id)
                if verificar == "pago":
                    await query.edit_message_text("✅ Pagamento realizado com sucesso!")
                    break
            except Exception as e:
                print(f"Erro ao verificar ou atualizar pagamento: {e}")
                await query.edit_message_text(
                    "❌ Ocorreu um erro ao processar seu depósito. Entre em contato com o suporte imediatamente."
                )
                break
            await asyncio.sleep(10) 

    except Exception as e:
        await query.edit_message_text(f"❌ Ocorreu um erro ao gerar o pagamento: {e}")



async def voltar_menu(client, message):
    query = message
    await start(client, query)

app = Client("bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


@app.on_message()
async def handle_start(client, message):
    if message.text.lower() == "/start":
        await start(client, message)

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    data = callback_query.data
    if data in ["atestado", "receita_branca"]:
        await selecionar_valor(client, callback_query)
    elif data in ["pagar_45_sp", "pagar_50_outros", "pagar_50"]:
        await gerar_pagamento(client, callback_query)
    elif data == "voltar_menu":
        await voltar_menu(client, callback_query)

print("Bot iniciado. Aguardando mensagens...")
app.run()