#std lib && imported files
import discord
import asyncio
import aiohttp
import random

#custom libs
import config
import db
from event import Emitter

#Discord client PhiBot
class PhiBot(discord.Client):

	def __init__(self, lock):
		super().__init__()
		self.running = True
		self.lock = lock
		self.eb_quotes = [
		'It is certain',
		'It is decidedly so',
		'Without a doubt',
		'Yes, definitely',
		'You may rely on it',
		'As I see it, yes',
		'Most likely',
		'Outlook good',
		'Yes',
		'Signs point to yes',
		'Reply hazy, please try again',
		'Ask again later',
		'Better not tell you now',
		'Cannot predict now',
		'Concentrate and ask again',
		'Don\'t count on it',
		'My reply is no',
		'My sources say no',
		'Outlook not so good',
		'Very doubtful'
		]
		self.shortener_endpoint = 'https://www.googleapis.com/urlshortener/v1/url'
	
	def set_running(self, running):
		self.running = running


	#on startup
	async def on_ready(self):

		if config.DEV_MODE:
			await self.change_presence(game=discord.Game(name='phi-bot DEV_MODE'))
		else:
			await self.change_presence(game=discord.Game(name='with all of my fellow users'))

		await Emitter.emit('Successfully-logged-in', 'Logged in as:{} with a user ID of:{}'.format(self.user.name, self.user.id))

	#Parse the id from a string
	def parse_id_from_string(self, id_string):
		return id_string.lstrip('<@!').rstrip('>')

	#Generate a user object given the current server members and id
	def make_user_object(self, server_members, id_string):
		user_id = self.parse_id_from_string(id_string)
		return discord.utils.get(server_members, id=user_id)

	#Helper functions for processing commands
	async def thats_me(self, message):
		await self.send_message(message.channel, 'Hey, that\'s me!')	

	#The magical 8ball
	async def eight_ball(self, message):
		await self.send_message(message.channel, random.choice(self.eb_quotes))

	#link shortener
	async def shorten_url(self, message):
		params = {'key':config.SHORTENER_KEY}
		headers = {'Content-Type': 'application/json'}
		url = message.content.split(' ')[1]

		async with aiohttp.ClientSession() as session:
			async with session.post(self.shortener_endpoint, params=params, json={'longUrl':url}, headers=headers) as response:
				if response.status == 200:
					json = await response.json()
					reply = 'Your shortened url:{}'.format(json['id'])
					await self.send_message(message.channel, reply)
					await Emitter.emit('Shorten-Success', 'URL:{} shortened to URL:{}'.format(url, json['id']))
				else:
					await self.send_message(message.channel, 'You did not provide a correct URL')
					await Emitter.emit('Shorten-Failure', 'URL:{} was attempted'.format(url))

	#Start a users bank account if they don't already ahve one
	async def start_bank_account(self, message):
		user_not_in_bank = None
		discord_id = message.author.id

		#Makes a bank account for the user if they don't already have one
		with await self.lock:
			user_not_in_bank = db.create_new_bank_account(discord_id)

		if user_not_in_bank:
			message_to_send = '<@{}>, your bank account has just been created and you have been granted 200 credits! Yay!'.format(discord_id)
			await self.send_message(message.channel, message_to_send)
		else:
			message_to_send = '<@{}>, you already have an account within our bank!'.format(discord_id)
			await self.send_message(message.channel, message_to_send)
	
	#Retreive bank account funds for a specific user
	async def get_bank_funds(self, message):
		discord_id = message.author.id
		funds = 0
		
		with await self.lock:
			funds = db.get_funds(discord_id)

		if funds == -1:
			message_to_send = '<@{}>, you do not have a bank account, but you can make one with the `$bank start` command :)'.format(discord_id)
			await self.send_message(message.channel, message_to_send)
		else:
			message_to_send = '<@{}>, you have ${} in your bank account, have a nice day!'.format(discord_id, funds)
			await self.send_message(message.channel, message_to_send)

	#Transfer bank funds to the user, called from the bank account routing
	async def transfer_bank_funds(self, message):
		discord_id = message.author.id
		command_input = message.content.split()
		
		if len(command_input) == 4:
			amount = int(command_input[2])
			receiving_user = self.parse_id_from_string(command_input[3])
			
			#Prevent negative funds through
			if amount < 0:
				await self.send_message(message.channel, '<@{}> you can\'t transfer a negative amount of money!'.format(discord_id))
				return
			
			#Validate that the user isn't trying to transfer funds to themselves
			if discord_id == receiving_user:
				await self.send_message(message.channel, '<@{}> you can\'t transfer a funds to yourself!'.format(discord_id))
				return
			
			#attempt to subtract funds from the user who initiated the transfers
			#bank account
			with await self.lock:
				funds_subtracted = db.subtract_funds(discord_id, amount)

				if not funds_subtracted:
					await self.send_message(message.channel, '<@{}> You either tried transferring more than you have or do not have a bank account, this is embarrasing!'.format(discord_id))
					return

			#Attempt to add the new funds to the receiving users bank account,
			#refund the initial user if the transaction fails
			with await self.lock:
				funds_added = db.add_funds(receiving_user, amount)

				if not funds_added:
					await self.send_message(message.channel, '<@{}> You either didn\'t provide a valid user or the user simply doesn\'t have a bank account. I am transferring the money back now.'.format(discord_id))
					db.add_funds(discord_id, amount)
					return

			#Retrieve the balance of the user who just made the transfer
			with await self.lock:
				new_balance = db.get_funds(discord_id)
				await self.send_message(message.channel, '<@{}> Successfully transferred funds, Your account balance is now: {} beans'.format(discord_id, new_balance))

		else:
			await self.send_message(message.channel, '```Sorry, this is an invalid use of transfer, please try $help bank for more information```')
	
	#Route bank account transaction request and handle input processing
	async def process_bank_account(self, message):
		
		discord_id = message.author.id
		command_input = message.content.split()
		
		try:
			if command_input[1] == 'start':
				await self.start_bank_account(message)
			elif command_input[1] == 'funds':
				await self.get_bank_funds(message)
			elif command_input[1] == 'transfer':
				await self.transfer_bank_funds(message)
		except Exception as e:
			await self.send_message(message.channel, '```Sorry, this is an invalid use transfer, please try $help bank for more information```')
			print(e)
				
	#Commmand processor
	async def process_command(self, message):
		content = message.content

		if not content.startswith('$'):
			return False

		if content.startswith('$phi'):
			await self.thats_me(message)
		elif content.startswith('$goodboy'):
			await self.send_message(message.channel, 'Woof!')
		elif content.startswith('$bank'):
			await self.process_bank_account(message)
		elif content.startswith('$8ball'):
			await self.eight_ball(message)
		elif content.startswith('$shorten'):
			await self.shorten_url(message)
		else:
			await self.send_message(message.channel, '```Sorry, you didn\'t enter a valid command, please try $help for more information```')
			return False

		return True

	#on message event handler. Sends command through custom command
	#handler
	async def on_message(self, message):
		valid_command = await self.process_command(message)

		#Log command to database
		if valid_command:
			await Emitter.emit('Processed command', 'Just finished processing a valid command')
			user_input = message.content.split()
			with await self.lock:
				db.add_command_to_history(user_input[0], " ".join(user_input[1:]), message.author.name, message.author.id)
				



#Shutdown bp
async def shutdown():
	await Emitter.emit('Bot shutdown phase', 'Bot is now turning off')
	await Emitter.shutdown()

	

def main(loop):
	#Shared lock for keeping database information safe
	lock = asyncio.Lock()

	phi = PhiBot(lock)

	#Manage the asyncio event loop
	try:
		loop.run_until_complete(phi.start(config.DISCORD_TOKEN))
	except KeyboardInterrupt:
		phi.set_running(False)
		loop.run_until_complete(phi.logout())
		loop.run_until_complete(shutdown())
	finally:
		loop.close()


if __name__ == '__main__':
	#Create database connection and then start all asynchronous actions
	db.create_db_connection()
	event_loop = asyncio.get_event_loop()
	main(event_loop)
