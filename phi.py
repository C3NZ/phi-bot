import discord
import asyncio
import config
import db


client = discord.Client();

@client.event
async def on_ready():
	print('logged in as')
	print(client.user.name)
	print(client.user.id)
	print('-----')

@client.event
async def on_message(message):
	valid_command = True

	if message.content.startswith('$phi'):
		await client.send_message(message.channel, 'Hey, that\'s me!')
	elif message.content.startswith('$cultured'):
		await client.send_message(message.channel, 'Ah, yes, our lord and savior, @cenz#4867')
	elif message.content.startswith('$goodboy'):
		await client.send_message(message.channel, 'Woof!')
	else:
		valid_command = False
		
	if valid_command:
		user_input = message.content.split()
		db.add_command_to_history(user_input[0], user_input[1:], message.author.name)

if __name__ == '__main__':
	db.create_db_connection()
	client.run(config.DISCORD_TOKEN)
