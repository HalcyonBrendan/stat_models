import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import HalcyonNHLdb
import GamesByDate
import Bank
import Game, ScoreAdjustedFenwick


class PythagGambit(object):
	def __init__(self,bank,season=20152016,start_date=20151201,end_date=20160410,num_games=5,pyth_exp=2.0,pyth_opt="goals",bet_timing="close"):
		self.bank = bank
		self.season = season
		self.start_date = start_date
		self.end_date = end_date
		self.gbd = GamesByDate.GamesByDate(self.season).gbd
		self.num_games = num_games
		self.pyth_exp = pyth_exp
		self.pyth_opt = pyth_opt
		self.diff_thresh = .45
		self.timing = bet_timing

	def retrieve_teams(self,gid):
		query = "SELECT team,opponent FROM Games{0} WHERE location=\"home\" AND gameID={1};".format(self.season,gid)
		teams = self.bank.db.execute_query(query)
		home_team = teams[0][0]
		away_team = teams[0][1]
		return home_team, away_team

	def retrieve_prev_ids(self,team,curr_date):
		query = "SELECT gameID FROM Games{0} WHERE team=\"{1}\" AND date<{2} ORDER BY date DESC LIMIT {3}".format(self.season,team,curr_date,self.num_games)
		prev_ids_temp = self.bank.db.execute_query(query)
		prev_ids = [int(x[0]) for x in prev_ids_temp]
		return prev_ids

	def count_wins(self,team,gids):
		query = "SELECT COUNT(*) FROM Games{0} WHERE team=\"{1}\" AND gameID IN {2} AND team=winner;".format(self.season,team,tuple(gids))
		win_count = float(self.bank.db.execute_query(query)[0][0])/len(gids)
		return win_count

	def count_goals(self,team,gids,way):
		if way == "for":
			query = "SELECT COUNT(*) FROM Goals{0} WHERE team=\"{1}\" AND gameID IN {2} AND period<5;".format(self.season,team,tuple(gids))
			goal_count = self.bank.db.execute_query(query)[0][0]
		elif way== "against":
			query = "SELECT COUNT(*) FROM Goals{0} WHERE opponent=\"{1}\" AND gameID IN {2} AND period<5;".format(self.season,team,tuple(gids))
			goal_count = self.bank.db.execute_query(query)[0][0]
		return goal_count

	def compute_safs(self,team,gids,way):
		safs = []
		safs_against = []
		for gid in gids:
			game = Game.Game(str(self.season),gid,team)
			saf = ScoreAdjustedFenwick.compute_SAF(game)
			safs.append(saf)
			if way == "against":
				safs_against.append(1-saf)
		if way == "for": return sum(safs)
		elif way == "against": return sum(safs_against)


	def compute_xWins(self,team,gids,exp,opt):
		if opt == "goals":
			gf = float(self.count_goals(team,gids,"for"))
			ga = float(self.count_goals(team,gids,"against"))
			# compute expected wins (pct)
			xWins = gf**exp / (gf**exp + ga**exp)
		elif opt == "saf":
			safs_for = float(self.compute_safs(team,gids,"for"))
			safs_against = float(self.compute_safs(team,gids,"against"))
			# compute expected wins (pct)
			xWins = safs_for**exp / (safs_for**exp + safs_against**exp)
		return xWins

	def prepare_bet(self,gid,team,excess):
		# get moneylines
		query = "SELECT odds FROM Moneylines{0} WHERE gameID={1} AND team=\'{2}\' AND bookName=\'{3}\' ORDER BY pollTime;".format(self.season,gid,team,self.bank.book)
		team_odds_temp = self.bank.db.execute_query(query)
		team_odds = [float(x[0]) for x in team_odds_temp]
		# choose odds based on self.timing option, then place bet
		try:
			flag = 0
			open_odds = team_odds[0]
			close_odds = team_odds[-1]
			if self.timing == "open": 
				odds = team_odds[0]
			elif self.timing == "close>open":
				odds = close_odds
				if open_odds>close_odds: flag = 1
			else: odds = close_odds

			if flag == 0: 
				print gid
				self.bank.place_bet(self.season,gid,team,team,odds,0)
			
		except:
			print "Couldn't select odds from list of moneylines:"
			print team_odds
			print "Continuing to next game."


	def execute(self):
		
		curr_date = self.start_date

		while curr_date <= self.end_date:
			try:
				gids = self.gbd[curr_date]
			except:
				curr_date = int((datetime.strptime(str(curr_date),'%Y%m%d') + timedelta(1)).strftime('%Y%m%d'))
				continue

			for gid in gids:
				# get team names
				home_team, away_team = self.retrieve_teams(gid)
				# get ids for previous self.num_games involving each team
				home_ids = self.retrieve_prev_ids(home_team,curr_date)
				away_ids = self.retrieve_prev_ids(away_team,curr_date)
				# count number of wins in previous self.num_games for each team
				home_wins = self.count_wins(home_team,home_ids)
				away_wins = self.count_wins(away_team,away_ids)
				# compute number of expected wins according to pythag model
				home_xWins = self.compute_xWins(home_team,home_ids,self.pyth_exp,self.pyth_opt)
				away_xWins = self.compute_xWins(away_team,away_ids,self.pyth_exp,self.pyth_opt)
				# compute difference between teams, s.t. more positive favours home, more negative favours away
				xDiff = (home_xWins - home_wins) - (away_xWins - away_wins)
				print "For ", home_team, " hosting ", away_team, " we have xDiff = ", xDiff

				# if xDiff exceeds threshold, place bet
				if xDiff >= self.diff_thresh:
					self.prepare_bet(gid,home_team,xDiff-self.diff_thresh)
				elif xDiff <= -self.diff_thresh:
					self.prepare_bet(gid,away_team,-self.diff_thresh-xDiff)

			curr_date = int((datetime.strptime(str(curr_date),'%Y%m%d') + timedelta(1)).strftime('%Y%m%d'))



if __name__ == "__main__":

	# TO SET
	league = 'NHL'
	season = 20122013
	start_date = 20130205
	end_date = 20130430
	num_games = 4
	pyth_exp = 2.3
	# option can be "goals" or "xGoals", where the latter uses our expected goals model
	pyth_opt = "saf"
	bet_timing = "close"

	bank = Bank.Bank(league=league,use_relative_bet=False)
	gambit = PythagGambit(bank,season=season,start_date=start_date,end_date=end_date,num_games=num_games,pyth_exp=pyth_exp,pyth_opt=pyth_opt,bet_timing=bet_timing)
	gambit.execute()


