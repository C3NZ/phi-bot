import discord
import asyncio
import config

client = discord.Client();

@client.event
async def on_ready():
	print('logged in as')
	print(client.user.name)
	print(client.user.id)
	print('-----')

@client.event
async def on_message(message):
	if message.content.startswith('$phi'):
		await client.send_message(message.channel, 'Hey, that\'s me!')


client.run(config.DISCORD_TOKEN)