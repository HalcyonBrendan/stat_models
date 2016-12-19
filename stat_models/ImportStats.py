import MySQLdb, re, time, sys, math, signal
from datetime import date, timedelta
import numpy as np
import pandas as pd
import HalcyonNHLdb


class TeamStats(object):

	def __init__(self,season):
		self.db = HalcyonNHLdb.HalcyonNHLdb()
		self.season = int(season)

		# Retrieve stats
		self.goals = self.retrieve_goals()



	def retrieve_goals(self):
		query = """SELECT team, COUNT(*) AS GF FROM Goals{0} WHERE period<5 AND zone=\'Off\' GROUP BY team""".format(self.season)
		query = """SELECT gameID,eventID,shooter,period,time FROM Goals{0} WHERE period<5 ORDER BY gameID ASC, eventID ASC""";