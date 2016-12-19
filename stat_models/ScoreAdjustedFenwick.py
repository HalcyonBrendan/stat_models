''' For each game in a specified season, compute the relative score-adjusted fenwick values.
	For now, formula computed according to http://puckon.net/articles/improving-our-score-adjustment.php	
'''

import time, datetime, math, random
import numpy
import HalcyonNHLdb, Game
from config import CONFIG as config


class SAF():

	def __init__(self, season_string):
		self.stats_db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = season_string
		self.build_date = datetime.datetime.now()
		self.teams = config["teams"]
		self.num_teams = len(self.teams)
		self.saf_mat = []
		self.win_mat = []
		self.game_id_mat = []
		self.is_home_mat = []

	def run_season(self):

		self.saf_mat = numpy.zeros(shape=(self.num_teams,82))
		self.win_mat = numpy.zeros(shape=(self.num_teams,82))
		self.game_id_mat = numpy.zeros(shape=(self.num_teams,82))
		self.is_home_mat = numpy.zeros(shape=(self.num_teams,82))
		team_counter = 0
		for team in self.teams:
			print "Computing SAF for ", team
			query_string = "SELECT gameID,location FROM Games{0} WHERE team=\'{1}\' ORDER BY gameID".format(self.season,team)
			game_tuples = self.stats_db.execute_query(query_string)

			game_counter = 0
			for game_tuple in game_tuples:

				#print game_id[0], " game ", game_counter+1, " for ", team
				gid = int(game_tuple[0])
				location = game_tuple[1]

				game = Game.Game(self.season, gid, team)

				self.win_mat[team_counter,game_counter] = game.get_game_result()
				self.saf_mat[team_counter,game_counter] = compute_SAF(game)
				self.game_id_mat[team_counter,game_counter] = int(gid)
				self.is_home_mat[team_counter,game_counter] = int(location=="home")

				game_counter +=1

			team_counter +=1

	def get_saf_matrix(self):
		return self.saf_mat

	def get_win_matrix(self):
		return self.win_mat

	def get_is_home_matrix(self):
		return self.is_home_mat

	def get_game_id_matrix(self):
		return self.game_id_mat

# Includes pp, pk, and EN events for now
def compute_SAF(game):

	fen_u2_avg = .44
	fen_u1_avg = .461
	fen_tied_avg = .50
	fen_d1_avg = .539
	fen_d2_avg = .56

	state_times = game.get_state_times()
	time_u2 = state_times[5]/60.
	time_u1 = state_times[4]/60.
	time_tied = state_times[3]/60.
	time_d1 = state_times[2]/60.
	time_d2 = state_times[1]/60.

	fen_events_by_state = game.get_rel_fen_by_state()
	fen_u2 = fen_events_by_state[5]
	fen_u1 = fen_events_by_state[4]
	fen_tied = fen_events_by_state[3]
	fen_d1 = fen_events_by_state[2]
	fen_d2 = fen_events_by_state[1]

	#print "times: ", time_u2, " ", time_u1, " ", time_tied, " ", time_d1, " ", time_d2
	#print "fens: ", fen_u2, " ", fen_u1, " ", fen_tied, " ", fen_d1, " ", fen_d2

	SAF = (time_u2*(fen_u2-fen_u2_avg)+time_u1*(fen_u1-fen_u1_avg)+time_tied*(fen_tied-fen_tied_avg)+time_d1*(fen_d1-fen_d1_avg)+time_d2*(fen_d2-fen_d2_avg))/(time_u2+time_u1+time_tied+time_d1+time_d2) + .5

	return SAF


if __name__ == "__main__":

	# Initialize class with year on which you want to build SAPS
	saf = SAF("20152016")
	saf.run_season()		


