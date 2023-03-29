#!/usr/bin/env python3
'''
OpenAI telegram bot for python-telegram-bot v20.x

Uses python requests to connect to OpenAI API.

Usage examples:
/chat Explain quantum computing
/pic draw a picture of Sahara desert

Voice transcription:
Forward any voice or audio message to Bot.

Evgeni Semenov, dev@safemail.sbs

'''
import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from functools import wraps
from pydub import AudioSegment
from io import BytesIO

telegram_api_token = "XXXXXX" # Your telegram bot API token here

openai_api_key = "XXXXXX" # Your OpenAI API token here
openai_chat_model = "gpt-3.5-turbo"
openai_image_model = "image-alpha-001"
openai_audio_model = "whisper-1"

allowed_users = [1111111, 1111111] # Add allowed users that can use the bot
allowed_groups = [-1111111] # Groups/channels where you want to use your bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await logger.warning('Update "%s" caused error "%s"', update, context.error)

def restricted(func): #this function restricts usage to specific users and on specific channels/groups
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        chat_type = update.effective_chat.type
        chat_id = update.effective_chat.id
        if chat_type == "private":
            if user_id not in allowed_users:
                print("User {} is not authorized.".format(user_id))
                return
        if chat_type in ["group", "supergroup", "channel"]:
            if chat_id not in allowed_groups:
                print("Group {} is not authorized.".format(chat_id))
                return
        return func(update, context, *args, **kwargs)
    return wrapped

def generate_image(query): 
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+openai_api_key
    }
    data = {
        "model": openai_image_model,
        "prompt": query,
        "num_images": 1,
        "size": "512x512",
        "response_format": "url"
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["data"][0]["url"]

def generate_text(query):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+openai_api_key
    } 
    data = {
        'model': openai_chat_model,
        'messages': [{'role': 'user', 'content': query}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

def download_file(url):
    response = requests.get(url)
    if response.status_code == 200:
        file = BytesIO(response.content)
    else:
        raise Exception(f"Error downloading audio from {url}: {response.status_code}")
    return file

def convert_audio(url):
    audio = download_file(url) 
    if audio:
        audio = AudioSegment.from_file(audio)
        audio.export("out.mp3", format="mp3")
        return True
    else:
        return False
    
def transcribe(file):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": "Bearer "+openai_api_key
    } 
    files = {
        "file": file,
    }
    data = {
        "model": openai_audio_model
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    return response.json()["text"]

@restricted
async def voice_to_text(update: Update, context:ContextTypes.DEFAULT_TYPE):
    
    openai_supported_extensions = ["mp3", "mp4", "mpeg", "m4a", "wav", "webm"]

    if update.message.voice:
        message = await context.bot.get_file(update.message.voice.file_id)
    if update.message.audio:
        message = await context.bot.get_file(update.message.audio.file_id)
    
    extension = str(message.file_path).split(".")[-1] # get file extension

    if extension not in openai_supported_extensions:
        if convert_audio(message.file_path):
            audio_file = open("out.mp3", "rb")
            text = transcribe(audio_file)
            os.unlink("out.mp3")
        else:
            text = "Conversion failed!"
    else:
        file = download_file(message.file_path)
        with open("out."+extension, "wb") as f:
            f.write(file.getbuffer())
        audio_file = open("out."+extension, "rb")
        text = transcribe(audio_file)
        os.unlink("out."+extension)
       
    await update.message.reply_text(text)


@restricted    
async def pic(update: Update, context:ContextTypes.DEFAULT_TYPE):
    message = update.message
    query = message.text.split("/pic")[1].strip()
    image_url = generate_image(query)
    image = requests.get(image_url).content
    await update.message.reply_photo(image)

@restricted
async def chat(update: Update, context:ContextTypes.DEFAULT_TYPE):
    message = update.message
    query = message.text.split("/chat")[1].strip()
    response = generate_text(query)
    await update.message.reply_text(response)

@restricted
async def start(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! You can /chat with me, or ask me to create a /pic. I can also transcribe the voice messages for you (just forward it to me in private chat)")

@restricted
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command.")


if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_api_token).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    
    pic_handler = CommandHandler("pic", pic)
    application.add_handler(pic_handler)

    chat_handler = CommandHandler("chat", chat)
    application.add_handler(chat_handler)

    voice_handler = MessageHandler(filters.VOICE | filters.AUDIO, voice_to_text)
    application.add_handler(voice_handler)

    application.add_error_handler(error)

    unknown_handler = MessageHandler(filters.COMMAND, unknown) #should be the last handler
    application.add_handler(unknown_handler)
    
    application.run_polling()
