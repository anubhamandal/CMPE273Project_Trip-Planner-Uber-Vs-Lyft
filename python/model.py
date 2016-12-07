from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from datetime import datetime




# Database Configurations
app = Flask(__name__)
DATABASE = ''
PASSWORD = ''
USER = ''
HOSTNAME = ''


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s/%s'%(USER, PASSWORD, HOSTNAME, DATABASE)
db = SQLAlchemy(app)

# Database migration command line


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

class Location(db.Model):

	##Data Model Table
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), unique=False)
        address = db.Column(db.String(120), unique=False)
        city = db.Column(db.String(120) , unique=False)
        state = db.Column(db.String(120) , unique=False)
        zip = db.Column(db.Integer, unique=False)
        lat = db.Column(db.Float , unique=False)
        lng = db.Column(db.Float , unique=False)

	def __init__(self,name,address,city,state,zip,lat,lng):
		
		self.name = name
		self.address = address
		self.city = city
		self.state = state
		self.zip = zip
		self.lat = lat
		self.lng = lng
		
	def __repr__(self):
		return '<location %r>' % self.name

## db.execute executes sql query like CREATE DATABASE IF NOT EXISTS etc.


class CreateDB():
	def __init__(self, hostname=None):
		if hostname != None:	
			HOSTNAME = hostname
		import sqlalchemy
		engine = sqlalchemy.create_engine('mysql://%s:%s@%s'%(USER, PASSWORD, HOSTNAME)) # connect to server
		#engine.execute("DROP DATABASE IF EXISTS %s "%(DATABASE)) #delete db if an existing db is present. to get a new database for every time test is run.
		engine.execute("CREATE DATABASE IF NOT EXISTS %s "%(DATABASE)) #create db

if __name__ == '__main__':
	manager.run()
