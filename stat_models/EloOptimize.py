import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta, datetime
from config import CONFIG as config
import numpy as np
import Elo
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)


class EloOptimize(object):

	def __init__(self,league,season,opt_season,param_grid):
		self.league = league
		self.season = season
		self.opt_season = opt_season
		self.param_grid = param_grid
		self.optimal_params = self.optimize()

	def compute_rmse(self,expected,actual):
		err = [x-y for x,y in zip(expected,actual)]
		sq_err = [x*x for x in err]
		rmse = np.sqrt(np.mean(sq_err))
		return rmse

	def optimize(self):
		print "Optimizing ", self.league, " ", self.season, " season using ", self.opt_season, " season."
		start_date = config["season_dates"][self.league][str(self.opt_season)]["start"]
		end_date = config["season_dates"][self.league][str(self.opt_season)]["end"]
		prev_elo_path = "outfiles/final_reg_elo_{0}.csv".format(prev_season(self.league,self.opt_season))
		min_rmse = 1
		for k in self.param_grid["K"]:
			for hb in self.param_grid["home_bias"]:
				for n in self.param_grid["norm"]:
					elo = Elo.Elo(self.opt_season,start_date,end_date,prev_elo_path,K=k,home_bias=hb,norm=n,opt_mode=True)
					elo.execute()
					rmse = self.compute_rmse(elo.expected_result,elo.actual_result)
					print k, " ", hb, " ", n, ": ", rmse
					if rmse < min_rmse:
						min_rmse = rmse
						opt_params = (k,hb,n)

		print "\nOptimal parameters: ", opt_params, " RMSE: ", min_rmse

		print "\nRunning target season ", self.season
		print "with parameters K=", opt_params[0], " home_bias=", opt_params[1], " norm=", opt_params[2]
		start_date = config["season_dates"][self.league][str(self.season)]["start"]
		end_date = config["season_dates"][self.league][str(self.season)]["end"]
		prev_elo_path = "outfiles/final_reg_elo_{0}.csv".format(prev_season(self.league,self.season))
		
		elo = Elo.Elo(self.season,start_date,end_date,prev_elo_path,K=opt_params[0],home_bias=opt_params[1],norm=opt_params[2],opt_mode=False)
		end_elo = elo.execute()
		elo.save_elo(end_elo)

def prev_season(league,curr_season):
	curr_season = str(curr_season)
	if league == "MLB":
		prev_season = str(int(curr_season)-1)
	else:
		prev_season = str(int(curr_season[0:4])-1) + curr_season[0:4]
	return int(prev_season)


if __name__ == "__main__":
	# TO SET
	league = "NHL"
	season = 20142015
	opt_season = 20132014
	param_grid = {"K": np.arange(6,26,2), "home_bias": np.arange(5,65,5), "norm": np.arange(275,475,25)}
	#param_grid = {"K": [12], "home_bias": [20], "norm": [350]}

	EloOptimize(league,season,opt_season,param_grid)

