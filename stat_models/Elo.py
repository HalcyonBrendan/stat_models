import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta, datetime
import numpy as np
import GamesByDate
import HalcyonNHLdb
import pandas as pd
pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 60)
pd.set_option('display.width', 1000)

from config import CONFIG as config



class Elo(object):

	def __init__(self,season,start_date,end_date,prev_elo):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = season
		self.start_date = start_date
		self.end_date = end_date
		self.gbd = GamesByDate.GamesByDate(self.season).gbd
		self.season_df = self.retrieve_season_results()

		self.init_elo_df = self.retrieve_initial_elo(prev_elo)
		print "\nOriginal ELO ratings for ", self.season, "\n"
		print self.init_elo_df

		self.K = 20
		self.home_bias = 50

	def save_elo(self,elo_df):
		pass

	def retrieve_season_results(self):
		query = "SELECT gameID, team, opponent, winner, loser, result, points, gameType, date FROM Games{0} WHERE location=\"home\" ORDER BY gameID ASC;".format(self.season)
		season_df = pd.read_sql(query,con=self.db.get_connection())
		return season_df

	def retrieve_initial_elo(self,prev_elo):
		try:
			elo_df = pd.read_csv(prev_elo,columns=config["teams"])
		except:
			init_data = 1500*np.ones((1,len(config["teams"])))
			elo_df = pd.DataFrame(init_data,index=np.arange(len(init_data)),columns=config["teams"])
		return elo_df

	def get_result(self,gid):
		win_loss = str(self.season_df["result"].loc[self.season_df["gameID"]==gid].item())
		game_type = str(self.season_df["gameType"].loc[self.season_df["gameID"]==gid].item())
		if win_loss == "W" and game_type == "RE":
			result = 1
		elif win_loss == "W" and game_type == "OT":
			result = 2
		elif win_loss == "W" and game_type == "SO":
			result = 3
		elif win_loss == "L" and game_type == "RE":
			result = 4
		elif win_loss == "L" and game_type == "OT":
			result = 5
		elif win_loss == "L" and game_type == "SO":
			result = 6
		else:
			print "Error retrieving result for game ", gid, ". Exiting."
			exit()
		return result

	def get_teams(self,gid):
		home = self.season_df["team"].loc[self.season_df["gameID"]==gid].item()
		away = self.season_df["opponent"].loc[self.season_df["gameID"]==gid].item()
		return home, away

	def compute_home_expectation(self,elo_diff):
		home_expect = 1./(10**(-elo_diff/400)+1)
		#print "Expected home pct: ", home_expect
		return home_expect

	def update_elo(self,elo_df,home,away,result):
		home_elo = elo_df[home].iloc[-1]
		away_elo = elo_df[away].iloc[-1]

		home_expected = self.compute_home_expectation(self.home_bias+home_elo-away_elo)
		away_expected = 1-home_expected
		
		if result == 1:
			new_home_elo = home_elo + self.K * (1 - home_expected)
			new_away_elo = away_elo + self.K * (0 - away_expected)
		elif result == 2:
			new_home_elo = home_elo + self.K * (.8 - home_expected)
			new_away_elo = away_elo + self.K * (.2 - away_expected)
		elif result == 3:
			new_home_elo = home_elo + self.K * (.6 - home_expected)
			new_away_elo = away_elo + self.K * (.4 - away_expected)
		elif result == 4:
			new_home_elo = home_elo + self.K * (0 - home_expected)
			new_away_elo = away_elo + self.K * (1 - away_expected)
		elif result == 5:
			new_home_elo = home_elo + self.K * (.2 - home_expected)
			new_away_elo = away_elo + self.K * (.8 - away_expected)
		elif result == 6:
			new_home_elo = home_elo + self.K * (.4 - home_expected)
			new_away_elo = away_elo + self.K * (.6 - away_expected)

		elo_df[home].iloc[-1] = new_home_elo
		elo_df[away].iloc[-1] = new_away_elo
		return elo_df

	def execute(self):

		curr_date = self.start_date
		curr_elo_df = self.init_elo_df

		while curr_date <= self.end_date:
			# get gids for current date if they exist, else continue to next day
			try:
				gids = self.gbd[curr_date]
			except:
				curr_date = int((datetime.strptime(str(curr_date),'%Y%m%d') + timedelta(1)).strftime('%Y%m%d'))
				continue

			# since games exist on this day, add row to curr_elo_df for new ratings
			curr_elo_df = curr_elo_df.append(curr_elo_df.iloc[[-1]], ignore_index=True)

			for gid in gids:
				# get team names
				home_team, away_team = self.get_teams(gid)
				# get game result
				result = self.get_result(gid)
				# update Elo
				curr_elo_df = self.update_elo(curr_elo_df,home_team,away_team,result)

			curr_date = int((datetime.strptime(str(curr_date),'%Y%m%d') + timedelta(1)).strftime('%Y%m%d'))

		print ""
		ratings_df = curr_elo_df.iloc[-1]
		ratings_df.columns = ['Team', 'Rating']

		print ratings_df.sort('Rating',ascending=False)

		print "\nFinal Elo ratings for ", self.season, "\n"
		print curr_elo_df.iloc[-1]

if __name__ == "__main__":
	try:
		prev_elo_path = str(sys.argv[1])
	except:
		prev_elo_path = None

	#TO SET
	season = 20132014
	start_date = 20131001
	end_date = 20140501

	elo = Elo(season,start_date,end_date,prev_elo_path)
	end_elo = elo.execute()
	elo.save_elo(end_elo)

