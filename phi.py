import discord
import asyncio
import config
import db

#Discord client for interacting with users
client = discord.Client();

#------Helper functions------
async def thats_me(message):
	await client.send_message(message.channel, 'Hey, that\'s me!')

#Process a users bank account
async def process_bank_account(command_input, message):
	if len(chopped_input) <= 1:
			print(chopped_input)
			await client.send_message(message.channel, 'This is where your bank info will be!')
	else:
		print(chopped_input)
		
		if chopped_input[1] == 'start':
			await client.send_message(message.channel, 'Starting your bank account!')

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
		thats_me(message)
	elif message.content.startswith('$cultured'):
		await client.send_message(message.channel, 'Ah, yes, our lord and savior, @cenz#4867')
	elif message.content.startswith('$goodboy'):
		await client.send_message(message.channel, 'Woof!')
	elif message.content.startswith('$bank'):
		chopped_input = message.content.split()
		process_bank_account(chopped_input, message)
	elif message.content.startswith('$yt'):
		await client.send_message(message.channel, '?play https://www.youtube.com/watch?v=4yym5Og_Oeg')
	else:
		valid_command = False

	if valid_command:
		user_input = message.content.split()
		db.add_command_to_history(user_input[0], user_input[1:], message.author.name)

def shutdown():
	print('Shutting down the bot now')

if __name__ == '__main__':
	db.create_db_connection()
	client.run(config.DISCORD_TOKEN)
	shutdown()
