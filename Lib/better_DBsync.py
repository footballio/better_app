import json
import requests
import better_config


class match_update:
    def __init__(self, key):
        self.m_id = None
        self.m_round = None
        self.m_status = None
        self.m_time = None
        self.m_hscore = None
        self.m_ascore = None
        self.m_outcome = None
        self.m_winner = None
        self.m_id = key['fixture']['id']
        self.m_round = key['league']['round']
        self.m_status = key['fixture']['status']['short']
        self.m_time = key['fixture']['timestamp']
        self.m_hscore = key['score']['fulltime']['home']
        self.m_ascore = key['score']['fulltime']['away']
        if self.m_hscore == self.m_ascore:
            self.m_outcome = 3
        elif self.m_hscore > self.m_ascore:
            self.m_outcome = 1
        elif self.m_hscore < self.m_ascore:
            self.m_outcome = 2
        else:
            pass
        if key['teams']['home']['winner']:
            self.m_winner = 1
        elif key['teams']['away']['winner']:
            self.m_winner = 2
        else:
            self.m_winner = None


class teams_update:
    def __init__(self, key):
        self.t_id = None
        self.t_name = None
        self.t_image = None
        self.group_id = None
        self.t_rank = None
        self.t_points = None
        self.t_played = None
        self.t_wins = None
        self.t_draws = None
        self.t_loses = None
        self.t_gd = None
        self.t_id = key['team']['id']
        self.t_name = key['team']['name']
        self.t_image = key['team']['logo']
        self.group_id = key['group']
        self.t_rank = key['rank']
        self.t_points = key['points']
        self.t_played = key['all']['played']
        self.t_wins = key['all']['win']
        self.t_draws = key['all']['draw']
        self.t_loses = key['all']['lose']
        self.t_gd = key['goalsDiff']


class players_update:
    def __init__(self, key):
        self.p_id = None
        self.p_name = None
        self.p_team = None
        self.p_image = None
        self.p_goals = None
        self.p_id = key['player']['id']
        self.p_name = key['player']['name']
        self.p_team = key['statistics'][0]['team']['id']
        self.p_image = key['player']['photo']
        self.p_goals = key['statistics'][0]['goals']['total']


def sync_matches():
    url = "https://api-football-beta.p.rapidapi.com/fixtures"
    querystring = {"season": "2015", "league": "2"}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    matches_json = json.loads(response)
    for key in matches_json['response']:
        params = match_update(key)
        if params.m_winner is None:
            query = """IF EXISTS (SELECT * FROM dbo.matches WHERE MID = '{}')
                             UPDATE matches
                             SET m_round='{}',m_status='{}',m_time='{}',m_hscore='{}',m_ascore='{}',m_outcome='{}'
                             WHERE MID = '{}'
                         ELSE
                             INSERT INTO matches (MID,m_round,m_status,m_time,m_hscore,m_ascore,m_outcome)
                             VALUES ('{}','{}','{}','{}','{}','{}','{}')""".format(params.m_id, params.m_round, params.m_status, params.m_time,
                                                                                   params.m_hscore, params.m_ascore, params.m_outcome,
                                                                                   params.m_id, params.m_id, params.m_round, params.m_status,
                                                                                   params.m_time, params.m_hscore, params.m_ascore, params.m_outcome)
        else:
            query = """IF EXISTS (SELECT * FROM dbo.matches WHERE MID = '{}')
                                        UPDATE matches
                                        SET m_round='{}',m_status='{}',m_time='{}',m_hscore='{}',m_ascore='{}',m_outcome='{}',m_winner='{}'
                                        WHERE MID = '{}'
                        ELSE
                            INSERT INTO matches (MID,m_round,m_status,m_time,m_hscore,m_ascore,m_outcome,m_winner)
                            VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')""".format(params.m_id, params.m_round, params.m_status, params.m_time,
                                                                                       params.m_hscore, params.m_ascore, params.m_outcome,
                                                                                       params.m_winner, params.m_id, params.m_id, params.m_round,
                                                                                       params.m_status, params.m_time, params.m_hscore,
                                                                                       params.m_ascore, params.m_outcome, params.m_winner)
        better_config.db_put(query)


def sync_teams():
    url = "https://api-football-beta.p.rapidapi.com/standings"
    querystring = {"season": "2020", "league": "2"}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    standings_response = json.loads(response)
    standings_json = standings_response['response'][0]['league']['standings']
    for group in standings_json:
        for rank in group:
            params = teams_update(rank)
            query = """IF EXISTS (SELECT * FROM dbo.standings WHERE TID='{}')
                              UPDATE teams
                              SET t_rank='{}',t_points='{}',t_played='{}',t_wins='{}',t_draws='{}',t_loses='{}',t_goals_diff='{}'
                              WHERE TID = '{}'
                          ELSE
                              INSERT INTO teams (TID,t_name,group_id,t_rank,t_points,t_played,t_wins,t_draws,t_loses,t_goals_diff)
                              VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(params.t_id, params.t_rank, params.t_points,
                                                                                                   params.t_played, params.t_wins, params.t_draws,
                                                                                                   params.t_loses, params.t_gd, params.t_id,
                                                                                                   params.t_id, params.t_name, params.group_id[-1],
                                                                                                   params.t_rank, params.t_points, params.t_played,
                                                                                                   params.t_wins, params.t_draws, params.t_loses,
                                                                                                   params.t_gd)
            better_config.db_put(query)


def sync_players():
    url = "https://api-football-beta.p.rapidapi.com/players/topscorers"
    querystring = {"season": "2021", "league": "2"}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    scorers_json = json.loads(response)
    for key in scorers_json['response']:
        params = players_update(key)
        query = """IF EXISTS (SELECT * FROM dbo.scorers WHERE PID = '{}')
                        UPDATE players
                        SET p_goals='{}'
                        WHERE PID = '{}'
                    ELSE
                        INSERT INTO players (PID,p_name,TID,p_goals,p_image)
                        VALUES ('{}','{}','{}','{}','{}')""".format(params.p_id, params.p_goals, params.p_id, params.p_id, params.p_name,
                                                                    params.p_team, params.p_goals, params.p_image)
        better_config.db_put(query)
