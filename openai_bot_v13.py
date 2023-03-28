#!/usr/bin/env python3

'''
Telegram bot that uses OpenAI API.
For python-telegram-bot library v13.x

Uses both python requests and openai libraries

Evgeni Semenov, dev@safemail.sbs
'''

import os
import tempfile
import logging
import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from pydub import AudioSegment
import openai
from functools import wraps
import requests

telegram_token = "YOUR TELEGRAM TOKEN HERE" # Add your telegram bot token here
openai.api_key = "YOUR OPEN AI TOKEN HERE" # Add your OpenAI key here
gpt3_engine_id = "gpt-3.5-turbo"  # Change this to the ID of the GPT engine you want to use
allowed_users = [11111111, 11111111] # Add allowed users that can use the bot
allowed_groups = [-1111111111] # Groups/channels where you want to use your bot

bot = telegram.Bot(telegram_token)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#Restricted function
def restricted(func):
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

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def generate_text(prompt):
    response = openai.ChatCompletion.create(
        model = gpt3_engine_id,
        messages=[{"role" : "user", "content" : prompt}]
    )
    return response.choices[0].message.content

def generate_image(query):
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    data = {
        "model": "image-alpha-001",
        "prompt": f"draw a picture of {query}",
        "num_images": 1,
        "size": "512x512",
        "response_format": "url"
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["data"][0]["url"]

@restricted
def pic(update: telegram.Update, context: CallbackContext):
    message = update.message
    query = message.text.split('/pic')[1].strip()
    image_url = generate_image(query)
    image = requests.get(image_url).content
    bot = telegram.Bot(token=telegram_token)
    bot.send_photo(chat_id=message.chat_id, photo=image)

@restricted
def chat(update: telegram.Update, context: CallbackContext):
    message = update.message
    prompt = message.text.split('/chat')[1].strip()

    generated_text = generate_text(prompt)
    message.reply_text(generated_text)

@restricted
def voice_to_text(update, context): # works only with ogg or Telegram voice messages atm
    if update.message.voice:
        voice_message = context.bot.get_file(update.message.voice.file_id)
        voice_url = voice_message.file_path
        voice_response = requests.get(voice_url)

        # Create temporary files and convert
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
            f.write(voice_response.content)
            audio = AudioSegment.from_file(f.name, format='ogg')

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            audio.export(f.name, format='mp3')
            voice_file = open(f.name, 'rb')

        # Transcribe
        transcript = openai.Audio.transcribe("whisper-1", voice_file)

        # Send out
        context.bot.send_message(chat_id=update.effective_chat.id, text=transcript["text"])

        # Delete the temporary files
        os.unlink(f.name)
        os.unlink(voice_file.name)

if __name__ == "__main__":    
    updater = Updater(telegram_token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('chat', chat))
    updater.dispatcher.add_handler(CommandHandler('pic', pic))
    updater.dispatcher.add_handler(MessageHandler(Filters.voice, voice_to_text))

    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()
