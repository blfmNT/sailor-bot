#!/usr/bin/python3

import os
import discord
from discord.ext import tasks
import logging
import asyncio
import CONFIG
import NAMES
import sailordb
import random

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class SailorBot(discord.Client):
   created_channels = []

   #list of tuples each contains: user id, channel id, invite id, invite message id
   created_invites = []
   #in minutes
   garbage_collector_interval = 5
   invites_channel = None
   sailor_category = None

   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s]: %(message)s',
                          handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()])

      self.sailordb = sailordb.SailorDB('sailor.db')

   @tasks.loop(minutes=garbage_collector_interval)
   async def garbage_collector(self):
      #remove empty voice channels
      for guild in self.guilds:
         for category in guild.categories:
            if category.name in CONFIG.CATEGORIES:
               for channel in category.channels:
                  if len(channel.members) == 0:
                     logging.info(f'Found empty boat channel {channel.name}({channel.id})')
                     await channel.delete()

      for created_invite in self.created_invites:
         channel_id = created_invite[1]
         message_id = created_invite[3]
         channel_exists = discord.utils.get(self.sailor_category.voice_channels, id=channel_id)
         if channel_exists is None:
            invite_message = await self.invites_channel.fetch_message(message_id)
            await invite_message.delete()



   async def on_ready(self):
      logging.info(f'{self.user} logged in')

      #init channels and categories
      for guild in self.guilds:
         #init voice channels in configs order
         self.sailor_category = discord.utils.get(guild.categories, name=CONFIG.SAILOR_CHANNELS_CATEGORY)
         if self.sailor_category is None:
            self.sailor_category = await guild.create_category(CONFIG.SAILOR_CHANNELS_CATEGORY)

         #all text channels in discord are in lowercase
         self.invites_channel = discord.utils.get(self.sailor_category.text_channels, name=CONFIG.INVITES_CHANNEL)
         if self.invites_channel is None:
            self.invites_channel = await self.sailor_category.create_text_channel(CONFIG.INVITES_CHANNEL)
         else:
            #better than remove all old messages
            await self.invites_channel.delete()
            self.invites_channel = await self.invites_channel.clone()


         for init_set_sail_channel in CONFIG.SET_SAIL_CHANNELS:
            channel = discord.utils.get(self.sailor_category.voice_channels, name=init_set_sail_channel)
            if channel is None:
               await self.sailor_category.create_voice_channel(init_set_sail_channel)


         for init_category in CONFIG.CATEGORIES:
            category = discord.utils.get(guild.categories, name=init_category)
            if category is None:
               await guild.create_category(init_category)

      #init garbage collector
      self.garbage_collector.start()


   async def create_boat(self, owner, max_size):
      guild = owner.guild

      target_category = CONFIG.CATEGORIES[0]

      match max_size:
         case 4:
            target_category = CONFIG.CATEGORIES[1]
         case 10:
            target_category = CONFIG.CATEGORIES[2]
         case 24:
            target_category = CONFIG.CATEGORIES[3]

      boats_category = discord.utils.get(guild.categories, name=target_category)

      if boats_category is None:
         boats_category = await guild.create_category(target_category)

      channel_name = NAMES.BOAT_NAMES[random.randint(0, len(NAMES.BOAT_NAMES))]
      new_channel = await boats_category.create_voice_channel(channel_name, user_limit=max_size)
      self.created_channels.append(new_channel.id)
      await owner.move_to(new_channel)

      logging.info(f'User {owner}({owner.id}) started a channel {new_channel.name}({new_channel.id})')


   async def on_message(self, message):
      logging.info(f'Received a new message from {message.author}({message.author.id})')

      user = message.author

      self.sailordb.add_user_message(user.name, user.id, message.content)

      if message.content == '!h' or message.content == '!help':
         await message.channel.send(content='''Join any Create X (Create Sloop) voice channel to set up your own voice channel\n~-- invites commands --~\nUse !invite (!i) [message] to create invite on your boat channel\n!delete (!d) to delete your invite''', delete_after=600)


      if message.channel.id != self.invites_channel.id:
         return

      #better use bot.commands for real
      if message.content.startswith('!i') or message.content.startswith('!invite'):
         logging.info(f'{user} creates invite')
         invite_message = message.content[8:]

         if user.voice is None or user.voice.channel is None or user.voice.channel.members == user.voice.channel.user_limit:
            return

         for created_invite in self.created_invites:
            if user.id in created_invite and user.voice.channel.id in created_invite:
               bot_invite_message = await self.invites_channel.fetch_message(created_invite[3])
               await bot_invite_message.delete()
               self.created_invites.remove(created_invite)

         invite = await user.voice.channel.create_invite()
         result = await self.invites_channel.send(content=f"{invite_message} \n" + str(invite), delete_after=600)
         if result:
            self.created_invites.append((user.id, user.voice.channel.id, invite.id, result.id))

         await message.delete()

      elif message.content == '!d' or message.content == '!delete':
         for created_invite in self.created_invites:
            if user.id in created_invite:
               bot_invite_message = await self.invites_channel.fetch_message(created_invite[3])
               self.created_invites.remove(created_invite)
               await bot_invite_message.delete()
               await message.delete()


   async def on_voice_state_update(self, member, before, after):
      #better store created channels in db
      if before.channel and before.channel.id in self.created_channels and len(before.channel.members) == 0:
         logging.info(f'All left boat channel {before.channel.name}({before.channel.id})')
         await before.channel.delete()

      if after.channel:
         if after.channel.name == CONFIG.SET_SAIL_ON_SLOOP:
            await self.create_boat(member, 2)

         if after.channel.name == CONFIG.SET_SAIL_ON_4MANS_BOAT:
            await self.create_boat(member, 4)

         if after.channel.name == CONFIG.SET_SAIL_ON_GALLEON:
            await self.create_boat(member, 10)

         if after.channel.name == CONFIG.SET_SAIL_ON_ISLAND:
            await self.create_boat(member, 24)

   async def on_command_error(self, context, exception):
      logging.error(f'{context} thrown an command error: {exception}')


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = SailorBot(intents=intents)
client.run(TOKEN)
