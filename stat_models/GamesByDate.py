import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta
import numpy as np
import pandas as pd
import HalcyonNHLdb



class GamesByDate(object):


	def __init__(self,season):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = season
		self.game_dates, self.gbd = self.retrieve_games_by_date()

	def retrieve_games_by_date(self):
		# retrieve dates from db
		query = """SELECT DISTINCT date FROM Games{0} ORDER BY date;""".format(self.season)
		game_dates = list(pd.read_sql(query,con=self.db.get_connection()).values.flatten())
		
		# create dictionary where key is date and value is array of game ids
		gbd = {}
		for gd in game_dates:
			query = """SELECT DISTINCT gameID FROM Games{0} WHERE date={1} ORDER BY gameID;""".format(self.season,int(gd))
			gbd[gd] = list(pd.read_sql(query,con=self.db.get_connection()).values.flatten())

		return game_dates, gbd


if __name__ == "__main__":
	gbd = GamesByDate(20152016)
