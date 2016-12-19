import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta
import numpy as np
import pandas as pd
import HalcyonNHLdb



class GamesByNum(object):


	def __init__(self,season,curr_id,num_games):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = season
		self.curr_id = curr_id
		self.num_games = num_games
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
	season = 20152016
	curr_id = 2015020200
	num = 5
	gbd = GamesByNum(season,curr_id,num)