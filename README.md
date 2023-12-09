# sailor-bot

### Sailor discord bot based on discordpy lib allows your users create their own voice rooms with needed sizes depends on type of 'boat'.

Create discord bot, invite on your server and put it's token to .env file in the same folder with

DISCORD_TOKEN=your_bot_top_secret_token

> pip install -r requirements.txt
>
> python ./bot.py

For testing purposes you can pull prepared docker image from docker hub

> docker pull blfmnt/sailor-bot

Run

> docker run -e DISCORD_TOKEN='your_bot_secret_token' sailor-bot
