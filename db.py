from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import config

#Session factory to create sessions to speak with our database
Session = sessionmaker();
#Reassignment of declarative base to base
Base = declarative_base()

#Command history table
class CommandHistory(Base):
	__tablename__ = 'command_history'

	command_id = Column(Integer, primary_key=True)
	command = Column(String(50))
	params = Column(String(50))
	user = Column(String(50))

#User command entered count table
class UserCommandCount(Base):
	__tablename__ = 'user_command_count'

	user_id = Column(Integer, primary_key=True)
	command_name = Column(String(50))
	count = Column(Integer)

#Create the database connection and configure the session to be
#binded to the database
def create_db_connection():
	database = create_engine(config.MYSQL_URL)
	Session.configure(bind=database)
	Base.metadata.create_all(bind=database)

#Add commands to our history
def add_command_to_history(command_name, parameters, author):
	session = Session()
	command = CommandHistory(command=command_name, params=" ".join(parameters), user=author)
	session.add(command)
	session.commit()