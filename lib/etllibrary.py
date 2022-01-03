#External Libraries
import json
import pymysql
import sys
import datetime

#Local Libraries
sys.path.insert(0, './lib')
from scraperlibrary import (
    cleanHeader,
    cleanData,
    get_type2
)

class ETL:
	host = ""
	user = ""
	pw = ""
	db = ""
	charset = ""
	logging = ""
	connection = ""
	cursor = ""
	jsonSchema = ""

	def __init__(self, host, user, pw, db, logging, schemaFile, charset='utf8'):
		self.host = host
		self.user = user
		self.pw = pw
		self.db = db
		self.charset = charset
		self.logging = logging

	## Initialize MySQL Cursor
		self.connection = pymysql.connect(host=self.host, user=user, password=pw, charset=self.charset)
		self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
		
		self.connectDatabase()
		DDLFields = list()
		
		self.jsonSchema = json.load(open(schemaFile))
		
	##initialize Logging
		self.logging = logging

	def connectDatabase(self):
		"""
		' connectDatabase: Checks if the database exists and if not it attempts to create it.  
		"""
		self.cursor.execute("SHOW DATABASES")
		dbExists = False
		for value in self.cursor:
			if value['Database'] == self.db:
				dbExists = True
				self.logging.info("etlLibrary: connectDatabase: Database "+self.db+" already exists.  Connecting to database.")
		if dbExists == False:
			self.cursor.execute("CREATE DATABASE "+self.db)
			self.logging.info("etlLibrary: connectDatabase: Database "+self.db+" doesn't yet exist.  Creating Database.")
		self.connection = pymysql.connect(host=self.host, user=self.user, password=self.pw, db=self.db, charset=self.charset)
		self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)

	def createSchema(self):
		'''
		'' createSchema - This function will retrieve a schema predefined in a json mapping
		'' and build the tables if it doesn't exist.  
		'''		
		for key, value in self.jsonSchema.items() :
				existingMYSQLTable = self.cursor.execute('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+key+'";')
				DDLFields = []
				if type(value) == type(dict()):
					for field, datatype in value.items():
						if field == "UNIQUE INDEX":
							DDLFieldDef =  field + " " +datatype+"_unique (" + datatype + " ASC), "
							DDLFields.append(DDLFieldDef)
						else:
							DDLFieldDef =  field + " " + datatype + ", "
							DDLFields.append(DDLFieldDef)

							columnExists = self.cursor.execute('SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+key+'" and COLUMN_NAME = "'+field+'";')
							if existingMYSQLTable > 0 and columnExists == 0:
								alterTable = "ALTER TABLE  "+self.db+"."+key+" ADD COLUMN "+field+" " +datatype+";"
								self.logging.info("now executing: "+ alterTable)
								self.cursor.execute(alterTable)

				if existingMYSQLTable == 0:
					mySQLDDL = """CREATE TABLE """+key+ """ 
									(id  INTEGER NOT NULL AUTO_INCREMENT, """+"""""".join(DDLFields)+""" 
									date_created TIMESTAMP NOT NULL ,
	  								date_updated TIMESTAMP NOT NULL, 
									PRIMARY KEY (id));"""
					self.logging.debug(mySQLDDL)
					self.cursor.execute(mySQLDDL)
				del DDLFields[:]

	def dataDump(self, table='dataDump'):
		'''
		'' dataDump - this method will create a table to store your json.
		'''
		existingMYSQLTable = self.cursor.execute('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+table+'";')
		if existingMYSQLTable == 0:
			ddl = """CREATE TABLE """+self.db+"""."""+table+""" (id INTEGER NOT NULL AUTO_INCREMENT,url varchar(150) NULL,record_id INT NULL,location varchar(100) NULL,source varchar(100) NULL, json text NULL, date_created TIMESTAMP NOT NULL, date_updated TIMESTAMP NOT NULL, parsed tinyint(1) default 0, PRIMARY KEY (id),  UNIQUE INDEX url_UNIQUE (url ASC));"""

			self.logging.debug(ddl)
			self.cursor.execute(ddl)


	def dumpData(self, url, record_id, source, location, json):
		'''
		'' dumpData - This function will dump the json objects into a table
		'''
		table = 'dataDump'
		existingMYSQLTable = self.cursor.execute('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+table+'";')
		if existingMYSQLTable == 0:
			ddl = """CREATE TABLE """+self.db+"""."""+table+""" (
	    				`id` INTEGER NOT NULL AUTO_INCREMENT,
	  					`url` varchar(150) NULL,
	  					`record_id` INT NULL,
	  					`location` varchar(100) NULL,
	  					`source` varchar(100) NULL,
	  					`json` json NULL,
	  					`date_created` TIMESTAMP NOT NULL,
	  					`date_updated` TIMESTAMP NOT NULL,
	  					parsed tinyint(1) default 0,
	  					PRIMARY KEY (`id`),
	  					UNIQUE INDEX `url_UNIQUE` (`url` ASC));
					"""
			self.logging.info('ETL:dumpData: Running the following DDL'+ddl)
			self.cursor.execute(ddl)
			
		theInsert = 'replace into '+self.db+'.'+table+' (url, record_id, source, location, json, parsed) values( "'+url+'", '+str(record_id)+', "'+source+'", "'+location+'", '+json+', 1 );'
		self.logging.info('ETL:dataDump: Running the following replace: '+theInsert)
		self.cursor.execute(theInsert)
		self.connection.commit()


	def analyzeArray(self, arrayName, location):
		'''
		'' analyzeArray - This function will grab all items parsed from your HTML, add them to an array_properties table for comparison.
		'' I use this to add similar properites to the same field as several towns use different names for things like bathrooms.
		'''
		self.logging.debug(arrayName)
		existingMYSQLTable = self.cursor.execute('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "array_properties";')
		if existingMYSQLTable == 0:

			mySQLDDL = """CREATE TABLE array_properties
			(id  INTEGER NOT NULL AUTO_INCREMENT, 
			location varchar(125), 
			array_name varchar(100), 
			key_name varchar(125), 
			data_type varchar(100), 
			PRIMARY KEY (id),
			unique index key_unique (key_name asc));"""
			self.logging.info(mySQLDDL)
			self.cursor.execute(mySQLDDL)

		for key, value in arrayName.items():
			if key is not None:
				doesRowExistSQL = 'select id from array_properties where key_name = "'+key+'";'
				doesRowExist = self.cursor.execute(doesRowExistSQL)

				if doesRowExist == 0:
					insertStatement = """replace into array_properties (key_name, location, data_type) values ( """"+key+"""", """"+location+"""", """"+get_type2(value)+"""" ) ;"""
					self.cursor.execute(insertStatement)
					self.connection.commit()
					self.logging.debug(insertStatement)


	def writeTable(self, tableName, object):
		'''
		'' writeTable: this function takes a table and an object and then writes the data into the table in question.
		'''
		table = tableName
		DDLFields = list()
		insertKeys = list()					#Used to hold the field names you will inser into
		insertValues = list()				#Used to hold the actual values you are inserting
		tableStructure = list()
		existingMYSQLTable = self.cursor.execute('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+tableName+'";')
		whereParentDataIs = list()

		for key, value in object.items():
			if key != "" and key[0].isdigit() is False : #Checkes if the key is a digit, if it is then we don't do anything.
				if value is None:
					datatype = "TEXT"
				else:
					datatype = get_type2(value)
				DDLFieldDef =  key + ' ' + datatype + ', '
				DDLFields.append(DDLFieldDef)
				insertKeys.append(key + ', ')

				columnExists = self.cursor.execute('SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+tableName+'" and COLUMN_NAME = "'+key+'";')
				if existingMYSQLTable > 0 and columnExists == 0:
					alterTable = 'ALTER TABLE  '+self.db+'.'+tableName+' ADD COLUMN '+key+' ' +datatype+';'
					self.logging.info('ETL: writeTable: Now executing: '+ alterTable)
					self.cursor.execute(alterTable)
				if value == "" or value is None:
					whereParentDataIs.append(key + """ is NULL and """)
					insertValues.append( """NULL , """)			
				elif value != "" and self.jsonSchema[tableName][key].upper().split('(')[0]  in ['VARCHAR', 'TEXT']:
					whereParentDataIs.append( key + """ = """ + '"' + value.replace('"',"'") + '"' + """ and """)
					insertValues.append('"' + value.replace('"',"'")  + '", ')
				elif value !="" and self.jsonSchema[tableName][key].upper()  == 'DATETIME':
					value = datetime.datetime.strptime(value, '%m/%d/%Y').strftime('%Y-%m-%d')
					whereParentDataIs.append( key + """ = """ + '"' +  value + '"' + """ and """)
					insertValues.append('"' + value + '", ')
				else:
					whereParentDataIs.append(key + """ = """  + str(value) + """ and """)
					insertValues.append(  str(value)+', ')	

		if existingMYSQLTable == 0:
			mySQLDDL = """CREATE TABLE """+tableName+ """ 
			(id  INTEGER NOT NULL AUTO_INCREMENT,"""+"""""".join(DDLFields)+""" PRIMARY KEY (id));"""
			self.logging.info(mySQLDDL)
			self.cursor.execute(mySQLDDL)

		doesRowExistSQL = """select * from """+ tableName + """ where """+"""""".join(whereParentDataIs)[:-4]+""";"""
		self.logging.info('ETL: writeTable: Running the following SQL: '+doesRowExistSQL) 

		doesRowExist = self.cursor.execute(doesRowExistSQL)
		if doesRowExist == 0:
			insertStatement = """replace into """+tableName+""" ("""+ """""".join(insertKeys)[:-2] +""",date_created,date_updated) values ("""+ """""".join(insertValues)[:-2] + """,now(),now()) ;"""
			self.logging.info(insertStatement)
			self.cursor.execute(insertStatement)
			self.connection.commit()
		else:
			self.logging.info('already exists')

		self.cursor.execute(doesRowExistSQL)
		addresses = self.cursor.fetchone()
		for key, value in addresses.items():
			if type(value) == type(datetime.datetime.now()):
				addresses.update({key : value.strftime('%Y-%m-%d') })
		return addresses

	def parseTable(self, dataArray, tableName, primaryTable=''):
		'''
		''	ParseTable - This method is used to parse 
		''  our tables and add the respective relationships.
		''  It's currently custom to my script and will need 
		''  to refactor it.
		'''
		foreignKey = primaryTable + '_id' #Used to link relationship to all tables. 
		DDLFields = list()
		insertKeys = list()					#Used to hold the field names you will inser into
		insertValues = list()				#Used to hold the actual values you are inserting
		subTableFields = list()
		table = dataArray[tableName]
		subTable = None
		tableStructure = list()
		whereParentDataIs = list()


		#Loop through the main tables.
		if type(table) != type(list()):
			for key, value in table.items():

				value = cleanData(value, self.jsonSchema[tableName][key])
				if type(value) != type(dict()) and type(value) != type(list()):
					insertKeys.append(key + ', ')
					if key in self.jsonSchema[tableName]: #Checkes if the key is a digit, if it is then we don't do anything.
						if value == "" or value is None:
							whereParentDataIs.append(key + """ is NULL and """)
							insertValues.append( """NULL , """)			
						elif value != "" and self.jsonSchema[tableName][key].upper().split('(')[0] in ['VARCHAR', 'TEXT']:
							whereParentDataIs.append( key + """ = """ + value + """ and """)
							insertValues.append( value + """, """)
						elif value != "" and self.jsonSchema[tableName][key] == "DATETIME":
							self.logging.debug( value)
							value = datetime.datetime.strptime(value, """%m/%d/%Y""").strftime("""%Y-%m-%d""")
							whereParentDataIs.append( key + """ = """ +  value + """ and """)
							insertValues.append( value + """, """)

						else:
							whereParentDataIs.append(key + """ = """ + str(value) + """ and """)
							insertValues.append( str(value) + """, """)			
				else:
					subTable = key
					DDLFieldDef =  key + '_id INTEGER, '
					DDLFields.append(DDLFieldDef)
					insertSubValues = list()
					insertSubKeys = list()
					whereDataIs = list()
					existingSubTable = self.cursor.execute('SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+subTable+'";')
					

					for subKey, subValue in value.items():
						if subKey[0].isdigit() is False:
							subDataType = get_type2(subValue)
							subTableFieldDef = subKey + ' ' + subDataType + ', '
							subTableFields.append( subTableFieldDef)
							insertSubKeys.append(subKey + ', ')

							if subValue == "":
								whereDataIs.append(subKey + ' is NULL and ')
							elif subValue != "" and self.jsonSchema[subTable][subKey].upper().split('(')[0] in ['VARCHAR', 'TEXT']:
								whereDataIs.append(subKey + ' = ' +  '"' + subValue.replace('"', '') + '"' + ' and ')
								insertSubValues.append('"' + subValue.replace('"', '') + '"' + ', ')
							elif subValue != "" and self.jsonSchema[subTable][subKey] == "DATETIME":
								self.logging.debug( str(subValue+ datetime.datetime.strptime(subValue, '%m/%d/%Y').strftime('%Y-%m-%d')))
								subValue = datetime.datetime.strptime(subValue, '%m/%d/%Y').strftime('%Y-%m-%d')
								whereDataIs.append(subKey + ' = ' +  '"' + subValue.replace('"', '') + '"' + ' and ')
								insertSubValues.append('"' + subValue.replace('"', '') + '"' + ', ')
							else:
								insertSubValues.append( str(subValue) + ', ')			
								whereDataIs.append(subKey + '=' +  '"' + str(subValue) + 'and ')
							columnExists = self.cursor.execute('SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+subTable+'" and COLUMN_NAME = "'+subKey+'";')
							if existingSubTable > 0 and columnExists == 0:
								alterTable = 'ALTER TABLE  '+self.db+'.'+subTable+' ADD COLUMN '+subKey+' ' +subDataType+';'
								self.logging.debug('now executing: '+ alterTable)
								self.cursor.execute(alterTable)

					if existingSubTable == 0:
						subTableDDL = """CREATE TABLE """+subTable+ """ 
						(id  INTEGER NOT NULL AUTO_INCREMENT,"""+"""""".join(subTableFields)+""" 
									date_created TIMESTAMP NOT NULL,
	  								date_updated TIMESTAMP NOT NULL, 
	  								PRIMARY KEY (id));"""
						self.logging.debug(subTableDDL)
						self.cursor.execute(subTableDDL)

					insertSubStatement = """replace into """+subTable+""" ("""+ """""".join(insertSubKeys)[:-2] +""") values ("""+ """""".join(insertSubValues).replace('""','NULL')[:-2] + """) ;"""
					self.logging.debug(insertSubStatement)
					self.cursor.execute(insertSubStatement)
					self.connection.commit()

			
					insertKeys.append(subTable+'_id, ')
					self.logging.debug(doesRowExistSQL) 
					self.cursor.execute(doesRowExistSQL)
					for key, value in self.cursor.fetchone().items():
						insertValues.append(str(value)+', ')
					
					
					del subTableFields[:], insertSubValues[:]


			doesRowExistSQL = """select id from """+ tableName + """ where """+"""""".join(whereParentDataIs)[:-4]+""";"""
			self.logging.debug(doesRowExistSQL) 
			
			doesRowExist = self.cursor.execute(doesRowExistSQL)
			insertStatement = """replace into """+tableName+""" ("""+ """""".join(insertKeys)[:-2] +""") values ("""+ """""".join(insertValues).replace('""','NULL')[:-2] + """) ;"""
			self.logging.debug(insertStatement)

			if tableName == primaryTable:
				if doesRowExist == 0:
					self.cursor.execute(insertStatement)
					self.connection.commit()
					self.logging.debug(insertStatement)
					self.logging.debug(doesRowExistSQL)
				self.cursor.execute(doesRowExistSQL)
				fkey = self.cursor.fetchone()
				for key, value in fkey.items():
					global fKeyValue, fKeyName
					fKeyName = primaryTable+'_id, '
					fKeyValue = str(value)+', '
			else:
				insertKeys.append(fKeyName)
				insertValues.append(fKeyValue)
				insertStatement = """replace into """+tableName+""" ("""+ """""".join(insertKeys)[:-2] +""") values ("""+ """""".join(insertValues).replace('""','NULL')[:-2] + """) ;"""
				self.logging.debug(insertStatement)
				self.cursor.execute(insertStatement)
				self.connection.commit()
			
				
				self.logging.debug(tableName, DDLFields, subTable, subTableFields)
			del DDLFields[:], insertValues
			return tableStructure
		else:
			subTable = tableName
			insertSubValues = list()
			insertSubKeys = list()
			whereDataIs = list()

			for items in table:
				for subKey, subValue in items.items():
					if subKey in self.jsonSchema[tableName]: #Checkes if the key is a digit, if it is then we don't do anything.
						subDataType = get_type2(subValue)
						subTableFieldDef = subKey + ' ' + subDataType + ', '
						subTableFields.append( subTableFieldDef)
						insertSubKeys.append(subKey + ', ')

						if subValue == "" or subValue is None:
							whereDataIs.append(subKey + ' is NULL and ')
							insertSubValues.append(' NULL, ')
						elif subValue != "" and self.jsonSchema[subTable][subKey].upper().split('(')[0] in ['VARCHAR', 'TEXT']:
							whereDataIs.append(subKey + ' = ' +  '"' + subValue.replace('"', '') + '"' + ' and ')
							insertSubValues.append('"' + subValue.replace('"', '') + '"' + ', ')
						elif subValue != "" and self.jsonSchema[subTable][subKey].upper() == "DATETIME":
							subValue = datetime.datetime.strptime(subValue, '%m/%d/%Y').strftime('%Y-%m-%d')
							whereDataIs.append(subKey + ' = ' +  '"' + subValue.replace('"', '') + '"' + ' and ')
							insertSubValues.append('"' + subValue.replace('"', '') + '"' + ', ')

						else:
							insertSubValues.append( str(subValue) + ', ')			
							whereDataIs.append(subKey + ' = ' + str(subValue) + ' and ')
						columnExists = self.cursor.execute('SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = "'+self.db+'" and TABLE_NAME = "'+subTable+'" and COLUMN_NAME = "'+subKey+'";')
						if columnExists == 0:
							alterTable = 'ALTER TABLE  '+self.db+'.'+subTable+' ADD COLUMN '+subKey+' ' +subDataType+';'
							self.logging.debug('now executing: '+ alterTable)
							self.cursor.execute(alterTable)

				doesRowExistSQL = """select id from """+ subTable + """ where """+"""""".join(whereDataIs)[:-4]+""";"""
				self.logging.debug(doesRowExistSQL) 
				doesRowExist = self.cursor.execute(doesRowExistSQL)

				if doesRowExist == 0:
					insertSubKeys.append(fKeyName)
					insertSubValues.append(fKeyValue)
					insertSubStatement = """replace into """+subTable+""" ("""+ """""".join(insertSubKeys)[:-2] +""") values ("""+ """""".join(insertSubValues).replace('""','NULL')[:-2] + """) ;"""
					self.logging.debug(insertSubStatement)
					self.cursor.execute(insertSubStatement)
					self.connection.commit()


				insertKeys.append(subTable+'_id, ')
				self.logging.debug(doesRowExistSQL) 
				self.cursor.execute(doesRowExistSQL)
				if self.cursor.execute(doesRowExistSQL) > 0:
					for key, value in self.cursor.fetchone().items():
						insertValues.append(str(value)+', ')
				
				del insertSubKeys[:], subTableFields[:], insertSubValues[:]
