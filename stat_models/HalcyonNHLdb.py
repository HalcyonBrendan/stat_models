import MySQLdb
from config import CONFIG as config

class HalcyonNHLdb(object):

	def __init__(self):
		self.db = MySQLdb.connect(passwd=config["mysql"]["pw"],host="localhost",user="root",db="halcyonnhl")
		self.cursor = self.db.cursor()

	def execute_command(self, command_string):
		self.cursor.execute(command_string)
		self.db.commit()

	def execute_query(self, query_string):
		self.cursor.execute(query_string)
		sql_out = self.cursor.fetchall()
		return sql_out

	def execute_num_query(self, query_string):
		self.cursor.execute(query_string)
		sql_out = self.cursor.fetchall()
		try:
			return float(self.strip_unwanted_num_text(str(sql_out)))
		except:
			return null

	def get_connection(self):
		return self.db

	def strip_unwanted_num_text(self,my_str):
		chars_to_strip = ["(", ")", ",", " ", "L"]
		for item in chars_to_strip:
		    # print "\'{0}\' in \'{1}\'? {2}".format(item, my_str, item in my_str)
		    my_str = my_str.replace(item,'')
		return my_str