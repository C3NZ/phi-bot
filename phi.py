import discord
import asyncio
import config
import db

#Discord client for interacting with users
client = discord.Client();

#Very simple print wrapper for not having to write if statements all throughout the code
def log_to_console(string):
	if config.DEBUG_MODE:
		print(string)

#------Helper functions------

#Hey, that's me!
async def thats_me(message):
	await client.send_message(message.channel, 'Hey, that\'s me!')

#Process a users bank account
async def process_bank_account(command_input, message):
	
	if len(command_input) == 1:
			print(command_input)
			await client.send_message(message.channel, 'This is where your bank info will be!')
	else:
		if command_input[1] == 'start':
			await client.send_message(message.channel, 'Starting your bank account!')


#-----Handling client events-----
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
		await thats_me(message)
	elif message.content.startswith('$cultured'):
		await client.send_message(message.channel, 'Ah, yes, our lord and savior, @cenz#4867')
	elif message.content.startswith('$goodboy'):
		await client.send_message(message.channel, 'Woof!')
	elif message.content.startswith('$bank'):
		command_input = message.content.split()
		await process_bank_account(command_input, message)
	elif message.content.startswith('$yt'):
		await client.send_message(message.channel, '?play https://www.youtube.com/watch?v=4yym5Og_Oeg')
	else:
		valid_command = False

	#Log command to database
	if valid_command:
		user_input = message.content.split()
		db.add_command_to_history(user_input[0], user_input[1:], message.author.name)


def shutdown():
	log_to_console('shutting down now')

if __name__ == '__main__':
	db.create_db_connection()
	client.run(config.DISCORD_TOKEN)
	shutdown()
