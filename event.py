#std && imported libs
import asyncio
import queue
import datetime
import os
from aiofile import AIOFile, Writer

#Custom libs
import config

#Event emitter
class Emitter:

	events = queue.Queue()
	current_date = datetime.date.today()
	file_name = "logs/{}-{}-{}.txt".format(current_date.month, current_date.day, current_date.year)
	command_count = 0
	event_counter = 0
	running = True
	aio_file = None

	#Initial DEV_MODE message to be printed upon the first time runnning the bot in a dev environment
	init_dev_mode_b = False
	init_dev_mode_m = '\nIF YOU\'RE SEEING THIS, THAT MEANS YOU HAVE DEV MODE ON WHICH SHOULD BE TURNED OFF FOR PRODUCTION USE\n'

	if os.path.isfile(file_name):
		aio_file = AIOFile(file_name, 'a+')
	else:
		aio_file = AIOFile(file_name, 'w+')

	writer = Writer(aio_file)

	@staticmethod
	async def emit(event, event_data):
		time = datetime.datetime.now()
		time_str = "{}:{}:{}".format(time.hour, time.minute, time.second)
		log_string = "[{}]-[{}]-:{}\n".format(time_str, event, event_data)

		await Emitter.writer(bytes(log_string, 'utf-8'))

		if Emitter.event_counter == 99:
			Emitter.event_counter = 0
			await Emitter.aio_file.fsync()
		else:
			Emitter.event_counter += 1

		if config.DEV_MODE:
			if not Emitter.init_dev_mode_b:
				Emitter.init_dev_mode_b = True
				print(Emitter.init_dev_mode_m)
			
			print('---[EVENT]---')
			print(log_string + ' was written to file')
			print('--------------\n')


	@staticmethod
	async def shutdown():
		await Emitter.aio_file.fsync()
		Emitter.aio_file.close()