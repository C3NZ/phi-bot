
import discord
import asyncio
import config
import db

#Discord client PhiBot
class PhiBot(discord.Client):

	def __init__(self, lock):
		super().__init__()
		self.lock = lock 

	#when the bot has readied up
	async def on_ready(self):
		print('logged in as')
		print(self.user.name)
		print(self.user.id)
		print('-----')

		await self.change_presence(game=discord.Game(name='culturology'))
	
	#Helper functions for processing commands
	async def thats_me(self, message):
		await self.send_message(message.channel, 'Hey, that\'s me!')

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
			receiving_user = command_input[3].lstrip('<@!').rstrip('>')
			
			if amount < 0:
				await self.send_message(message.channel, '<@{}> you can\'t transfer a negative amount of money!'.format(discord_id))
				return
			
			if discord_id == receiving_user:
				await self.send_message(message.channel, '<@{}> you can\'t transfer a funds to yourself!'.format(discord_id))
				return
			
			with await self.lock:
				funds_subtracted = db.subtract_funds(discord_id, amount)

				if not funds_subtracted:
					await self.send_message(message.channel, '<@{}> You either tried transferring more than you have or do not have a bank account, this is embarrasing!'.format(discord_id))
					return

			with await self.lock:
				funds_added = db.add_funds(receiving_user, amount)

				if not funds_added:
					await self.send_message(message.channel, '<@{}> You either didn\'t provide a valid user or the user simply doesn\'t have a bank account. I am transferring the money back now.'.format(discord_id))
					db.add_funds(discord_id, amount)
					return

			with await self.lock:
				new_balance = db.get_funds(discord_id)
				await self.send_message(message.channel, '<@{}> Successfully transferred funds, Your account balance is now: {} beans'.format(discord_id, new_balance))

		else:
			await self.send_message(message.channel, '```Sorry, this is an invalid use transfer, please try $help bank for more information```')
	
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
				

	async def gamble(self, message):
		discord_id = message.author.id
		command_input = message.content.split()
		await self.send_message(message.channel, '<@{}> Although you didn\'t really gamble, heres some money!'.format(discord_id))

		funds = 0
		with await self.lock:
			db.add_funds(discord_id, 200)
			funds = db.get_funds(discord_id)

		await self.send_message(message.channel, '<@{}> You now have ${} in your bank account!'.format(discord_id, funds))


	#Commmand processor
	async def process_command(self, message):
		if message.content.startswith('$phi'):
			await self.thats_me(message)
		elif message.content.startswith('$cultured'):
			await self.send_message(message.channel, 'Ah, yes, our lord and savior, @cenz#4867')
		elif message.content.startswith('$goodboy'):
			await self.send_message(message.channel, 'Woof!')
		elif message.content.startswith('$bank'):
			await self.process_bank_account(message)
		elif message.content.startswith('$gamble'):
			await self.gamble(message)
		else:
			return False

		return True

	#Discord Event handlers
	async def on_message(self, message):
		valid_command = await self.process_command(message)

		#Log command to database
		if valid_command:
			user_input = message.content.split()
			with await self.lock:
				db.add_command_to_history(user_input[0], user_input[1:], message.author.name)


def shutdown():
	print('Shutting down...')
	db.close_database()

def main(loop):
	#Shared lock for keeping database information safe
	lock = asyncio.Lock()

	phi = PhiBot(lock)

	#Start and login to the bot
	try:
		loop.run_until_complete(phi.start(config.DISCORD_TOKEN))
	except KeyboardInterrupt:
		loop.run_until_complete(phi.logout())
	finally:
		loop.close()


if __name__ == '__main__':
	#Create database connection and then start all asynchronous actions
	db.create_db_connection()
	event_loop = asyncio.get_event_loop()
	main(event_loop)
