# openai-telegram

This is a Telegram bot that utilizes OpenAI API.
At the moment you can use it for ChatGPT, image generation (dall-e) and voice message transcription (whisper).

# Setup

Add your API keys for Telegram bot and OpenAI.  
Install requirements.  
You want to limit the users that are allowed to use the bot, add the desired userID's in the list. There are several ways how you can find out your userID, but the easiest one is to use https://t.me/getidsbot on Telegram.  
The same goes with allowed channels/groups. Add group IDs where you want to allow the usage of your bot.  

# Usage

To use ChatGPT, just enter a command /chat followed by a text in private chat with bot or on the channel where your bot is present. For example:  
/chat explain quantum computing  

For image generation, use /pic:  
/pic black cat  

For audio message transcription just forward the audio message to the bot (in a private chat)
