import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import HalcyonNHLdb
import GamesByDate


class Bank(object):
	def __init__(self, league='NHL', bankroll=1000, relative=.02, absolute=25, book="Pinnacle", use_relative_bet=True):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.league = league
		self.book = book
		self.bankroll = bankroll
		self.rel_bet_size = relative
		self.abs_bet_size = absolute
		self.use_relative_bet = use_relative_bet		

	def _bet_size(self):
		if self.use_relative_bet:
			return self.bankroll * self.rel_bet_size
		else:
			return self.abs_bet_size

	# In case of two outcome bets, team and choice should be the same
	def place_bet(self, season, game_id, team, choice, line, thresh):
		bet_size = self._bet_size()
		self.bankroll -= bet_size
		outcome = self.check_bet_outcome(season, game_id, team, choice)
		if outcome == 1:
			#self.bankroll += bet_size * thresh
			self.bankroll += bet_size * line
			print "After betting ${0} on \'{1}\' and winning at {2}, your new bankroll is: ${3}".format(bet_size, choice, line, self.bankroll)
		elif outcome == -1:
			self.bankroll += bet_size
		else:
			print "After betting ${0} on \'{1}\' and losing, your new bankroll is: ${2}".format(bet_size, choice, self.bankroll)

	def check_bet_outcome(self, season, game_id, team, choice):
		#  Query DB to check bet outcome
		query = "SELECT winner FROM Moneylines{0} WHERE gameID={1} AND team=\'{2}\';".format(season,game_id,team)
		try:
			winner = self.db.execute_query(query)[0][0]
		except:
			print "Had problem finding winner. Returning bet amount to bankroll."
			time.sleep(2)
			return -1
		print "WINNER v CHOICE: ", winner, " ", choice
		if winner == choice: return 1
		return 0