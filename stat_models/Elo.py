import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta, datetime
from config import CONFIG as config
import numpy as np
import GamesByDate
import HalcyonNHLdb
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)

from config import CONFIG as config


class Elo(object):

	def __init__(self,season,start_date,end_date,prev_elo,opt_mode=False,K=15,home_bias=30,norm=400,reg_frac=1./3):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = int(season)
		self.start_date = int(start_date)
		self.end_date = int(end_date)
		self.last_date = 0
		self.gbd = GamesByDate.GamesByDate(self.season).gbd
		self.season_df = self.retrieve_season_results()

		# opt_mode =True => parameters being optimized on season prior to actual target season
		# opt_mode =False => Elo being computed with specified parameters on target games
		self.opt_mode = opt_mode
		if self.opt_mode:
			self.expected_result = []
			self.actual_result = []

		self.init_elo_df = self.retrieve_initial_elo(prev_elo)

		self.K = K
		self.home_bias = home_bias
		self.norm = norm

		self.reg_frac = reg_frac

	def regress_elo(self,elo_df,frac):
		reg_df = elo_df[[self.last_date]]-frac*(elo_df[[self.last_date]]-1505)
		return reg_df

	def save_elo(self,elo_df):
		# save entire elo_df in csv file
		#print elo_df
		full_outfile = "outfiles/daily_elo_{0}.csv".format(self.season)
		elo_df.to_csv(full_outfile)
		# regress final ratings 1/3 back towards 1505
		final_df = elo_df[[self.last_date]]
		reg_df = self.regress_elo(final_df,self.reg_frac)
		final_outfile = "outfiles/final_reg_elo_{0}.csv".format(self.season)
		reg_df.to_csv(final_outfile)

	def retrieve_season_results(self):
		query = "SELECT gameID, team, opponent, winner, loser, result, points, gameType, date FROM Games{0} WHERE location=\"home\" ORDER BY gameID ASC;".format(self.season)
		season_df = pd.read_sql(query,con=self.db.get_connection())
		return season_df

	def retrieve_initial_elo(self,prev_elo):
		try:
			elo_df = pd.read_csv(prev_elo)
			elo_df = elo_df.set_index(elo_df.columns[0])
		except:
			init_date = "{0}_i".format(self.start_date)
			init_data = 1500*np.ones((len(config["teams"]),1))
			elo_df = pd.DataFrame(init_data,index=config["teams"],columns=[init_date])
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
		if home == "PHX": home = "ARI"
		elif away == "PHX": away = "ARI"
		if home == "ATL": home = "WPG"
		elif away == "ATL": away = "WPG"
		return home, away

	def compute_home_expectation(self,elo_diff):
		home_expect = 1./(10**(-elo_diff/self.norm)+1)
		#print "Expected home pct: ", home_expect
		return home_expect

	def update_elo(self,elo_df,curr_date,home,away,gid,result):
		home_elo = elo_df[curr_date].ix[home]
		away_elo = elo_df[curr_date].ix[away]

		home_expected = self.compute_home_expectation(self.home_bias+home_elo-away_elo)
		away_expected = 1-home_expected
		if self.opt_mode: self.expected_result.append(home_expected)
		
		if result == 1:
			home_actual = 1
			new_home_elo = home_elo + self.K * (home_actual - home_expected)
			new_away_elo = away_elo + self.K * ((1-home_actual) - away_expected)
		elif result == 2:
			home_actual = .8
			new_home_elo = home_elo + self.K * (home_actual - home_expected)
			new_away_elo = away_elo + self.K * ((1-home_actual) - away_expected)
		elif result == 3:
			home_actual = .6
			new_home_elo = home_elo + self.K * (home_actual - home_expected)
			new_away_elo = away_elo + self.K * ((1-home_actual) - away_expected)
		elif result == 4:
			home_actual = 0
			new_home_elo = home_elo + self.K * (home_actual - home_expected)
			new_away_elo = away_elo + self.K * ((1-home_actual) - away_expected)
		elif result == 5:
			home_actual = .2
			new_home_elo = home_elo + self.K * (home_actual - home_expected)
			new_away_elo = away_elo + self.K * ((1-home_actual) - away_expected)
		elif result == 6:
			home_actual = .4
			new_home_elo = home_elo + self.K * (home_actual - home_expected)
			new_away_elo = away_elo + self.K * ((1-home_actual) - away_expected)

		if self.opt_mode: self.actual_result.append(home_actual)
		
		elo_df[curr_date].ix[home] = new_home_elo
		elo_df[curr_date].ix[away] = new_away_elo
		return elo_df

	def execute(self):

		curr_date = self.start_date
		prev_date = self.init_elo_df.columns[0]
		curr_elo_df = self.init_elo_df

		while curr_date <= self.end_date:
			# get gids for current date if they exist, else continue to next day

			try:
				gids = self.gbd[curr_date]
			except:
				curr_date = int((datetime.strptime(str(curr_date),'%Y%m%d') + timedelta(1)).strftime('%Y%m%d'))
				continue

			# since games exist on this day, add col to curr_elo_df for new ratings
			curr_elo_df[curr_date] = curr_elo_df[prev_date]

			for gid in gids:
				# get team names
				home_team, away_team = self.get_teams(gid)
				# get game result
				result = self.get_result(gid)
				# update Elo
				curr_elo_df = self.update_elo(curr_elo_df,curr_date,home_team,away_team,gid,result)

			prev_date = curr_date
			self.last_date = curr_date
			curr_date = int((datetime.strptime(str(curr_date),'%Y%m%d') + timedelta(1)).strftime('%Y%m%d'))

		curr_elo_df.index.names = ['Team']
		return curr_elo_df


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

