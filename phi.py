
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
		#await self.send_message(message.channel, 'Hey, that\'s me!')

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
				
	#Gambling scaffolding, inactive and was just used for inserting funds
	#into the users account
	async def gamble(self, message):
		discord_id = message.author.id
		command_input = message.content.split()
		await self.send_message(message.channel, '<@{}> Although you didn\'t really gamble, heres some money!'.format(discord_id))

		funds = 0
		with await self.lock:
			db.add_funds(discord_id, 200)
			funds = db.get_funds(discord_id)

		await self.send_message(message.channel, '<@{}> You now have ${} in your bank account!'.format(discord_id, funds))

	#
	async def guess_game(self, message):
		discord_id = message.author.id
		command_input = message.content.split()
		user_challenged =  self.make_user_object(message.server.members, command_input[2])
		wagered_amount = 0
		game_in_session = False

		try:
			wagered_amount = int(command_input[1])
		except:
			await self.send_message(message.channel, '<@{}> You have to wager an integer amount!'.format(discord_id))
			return

		if wagered_amount < 0:
			await self.send_message(message.channel, '<@{}> You have to wager an amount greater than 0!'.format(discord_id))
			return

		if user_challenged and user_challenged.id != discord_id:
			game_in_session = True
		else:
			await self.send_message(message.channel, '<@{}> You either didn\'t give me a valid user or this user doesn\'t have a bank account, sorry!'.format(discord_id))
			return

		await self.send_message(message.channel, '<@{}> you have been challenged by <@{}> to guess a number between 1 and 100 for {} beans! Do you accept? (y/n)'.format(user_challenged.id, discord_id, wagered_amount))

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
			pass
			#await self.gamble(message)
		elif message.content.startswith('$guessgame'):
			await self.guess_game(message)
		else:
			return False

		return True

	#on message event handler. Sends command through custom command
	#handler
	async def on_message(self, message):
		valid_command = await self.process_command(message)

		#Log command to database
		if valid_command:
			user_input = message.content.split()
			with await self.lock:
				db.add_command_to_history(user_input[0], " ".join(user_input[1:]), message.author.name)


#Shutdown bp
def shutdown():
	print('Shutting down...')

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
