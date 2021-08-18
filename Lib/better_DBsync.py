import json
import requests
import better_config
import datetime


class match_update():
    def __init__(self,match_json,key):
        self.match_id = None
        self.match_type = None
        self.match_status = None
        self.match_start = None
        self.match_homeTID = None
        self.match_home = None
        self.match_awayTID = None
        self.match_away = None
        self.match_hscore = None
        self.match_ascore = None
        self.match_outcome = None
        self.match_winner = None
        self.match_id = key['fixture']['id']
        self.match_type = key['league']['round']
        self.match_status = key['fixture']['status']['short']
        self.match_start = key['fixture']['timestamp']
        self.match_homeTID = key['teams']['home']['id']
        self.match_home = key['teams']['home']['name']
        self.match_awayTID = key['teams']['away']['id']
        self.match_away = key['teams']['away']['name']
        self.match_hscore = key['score']['fulltime']['home']
        self.match_ascore = key['score']['fulltime']['away']
        if self.match_hscore == self.match_ascore:
            self.match_outcome = 3
        elif self.match_hscore > self.match_ascore:
            self.match_outcome = 1
        elif self.match_hscore < self.match_ascore:
            self.match_outcome = 2
        else:
            pass
        if key['teams']['home']['winner']:
            self.match_winner = 1
        elif key['teams']['away']['winner']:
            self.match_winner = 2
        else:
            self.match_winner = None

class standings_update():
    def __init__(self,standings_json,key):
        self.group_id = None
        self.group_name = None
        self.team_rank = None
        self.team_id = None
        self.team_points= None
        self.team_played = None
        self.team_wins = None
        self.team_draws = None
        self.team_loses = None
        self.team_gf = None
        self.group_id = key['group']
        self.team_rank = key['rank']
        self.team_id = key['team']['id']
        self.team_name = key['team']['name']
        self.team_points= key['points']
        self.team_played = key['all']['played']
        self.team_wins = key['all']['win']
        self.team_draws = key['all']['draw']
        self.team_loses = key['all']['lose']
        self.team_gf = key['goalsDiff']

class scorers_update():
    def __init__(self,scorers_json,key):
        self.player_id = None
        self.player_name = None
        self.player_team = None
        self.player_image = None
        self.player_goals= None
        self.player_id = key['player']['id']
        self.player_name = key['player']['name']
        self.player_team = key['statistics'][0]['team']['id']
        self.player_image = key['player']['photo']
        self.player_goals = key['statistics'][0]['goals']['total']

def sync_matches():
    url = "https://api-football-beta.p.rapidapi.com/fixtures"
    querystring = {"season": "2015","league": "2"}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    matches_json = json.loads(response)
    for key in matches_json['response']:
        params = match_update(matches_json,key)
        if params.match_winner is None:
            query = """IF EXISTS (SELECT * FROM dbo.matches WHERE MID = '{}')
                             UPDATE matches
                             SET m_type='{}',m_status='{}',m_time='{}',m_home_TID='{}',m_home='{}',m_away_TID='{}',m_away='{}',m_hscore='{}',
                             m_ascore='{}',m_outcome='{}',m_winner='{}'
                             WHERE MID = '{}'
                         ELSE
                             INSERT INTO matches (MID,m_type,m_status,m_time,m_home_TID,m_home,m_away_TID,m_away,m_hscore,m_ascore,m_outcome)
                             VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(params.match_id,params.match_type,params.match_status,
                                                                                                params.match_start,params.match_homeTID,params.match_home,
                                                                                                params.match_awayTID,params.match_away,params.match_hscore,
                                                                                                params.match_ascore,params.match_outcome,params.match_winner,
                                                                                                params.match_id,params.match_id,params.match_type,
                                                                                                params.match_status,params.match_start,params.match_homeTID,
                                                                                                params.match_home, params.match_awayTID,params.match_away,
                                                                                                params.match_hscore,params.match_ascore,params.match_outcome)
        else:
            query = """IF EXISTS (SELECT * FROM dbo.matches WHERE MID = '{}')
                                        UPDATE matches
                                        SET m_type='{}',m_status='{}',m_time='{}',m_home_TID='{}',m_home='{}',m_away_TID='{}',m_away='{}',m_hscore='{}',
                                        m_ascore='{}',m_outcome='{}',m_winner='{}'
                                        WHERE MID = '{}'
                        ELSE
                            INSERT INTO matches (MID,m_type,m_status,m_time,m_home_TID,m_home,m_away_TID,m_away,m_hscore,m_ascore,m_outcome,m_winner)
                            VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(params.match_id,params.match_type,params.match_status,
                                                                                                    params.match_start,params.match_homeTID,params.match_home,
                                                                                                    params.match_awayTID,params.match_away,params.match_hscore,
                                                                                                    params.match_ascore,params.match_outcome,params.match_winner,
                                                                                                    params.match_id,params.match_id,params.match_type,
                                                                                                    params.match_status,params.match_start,params.match_homeTID,
                                                                                                    params.match_home, params.match_awayTID,params.match_away,
                                                                                                    params.match_hscore,params.match_ascore,params.match_outcome,
                                                                                                    params.match_winner)
        better_config.db_put(query)


def sync_standings():
    url = "https://api-football-beta.p.rapidapi.com/standings"
    querystring = {"season": "2020","league": "2"}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    standings_response = json.loads(response)
    standings_json = standings_response['response'][0]['league']['standings']
    for group in standings_json:
        for rank in group:
            params = standings_update(group,rank)
            query = """IF EXISTS (SELECT * FROM dbo.standings WHERE TID = '{}')
                              UPDATE standings
                              SET t_rank='{}',t_points='{}',t_played='{}',t_wins='{}',t_draws='{}',t_loses='{}',t_goals_diff='{}'
                              WHERE TID = '{}'
                          ELSE
                              INSERT INTO standings (group_id,t_rank,TID,t_name,t_points,t_played,t_wins,t_draws,t_loses,t_goals_diff)
                              VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(params.team_id,params.team_rank,params.team_points,
                                                                                              params.team_played,params.team_wins,params.team_draws,
                                                                                              params.team_loses,params.team_gf,params.team_id,
                                                                                              params.group_id[-1],params.team_rank,params.team_id,
                                                                                              params.team_name,params.team_points,params.team_played,
                                                                                              params.team_wins,params.team_draws,params.team_loses,
                                                                                              params.team_gf)
            better_config.db_put(query)

def sync_scorers():
    url = "https://api-football-beta.p.rapidapi.com/players/topscorers"
    querystring = {"season":"2021","league":"2"}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    scorers_json = json.loads(response)
    for key in scorers_json['response']:
        params = scorers_update(scorers_json,key)
        query = """IF EXISTS (SELECT * FROM dbo.scorers WHERE PID = '{}')
                        UPDATE scorers
                        SET Pgoals='{}',Pimage='{}'
                        WHERE PID = '{}'
                    ELSE
                        INSERT INTO scorers (PID,Pname,Pgoals,Pimage,TID)
                        VALUES ('{}','{}','{}','{}','{}')""".format(params.player_id,params.player_goals,params.player_image,params.player_id,
                                                                    params.player_id,params.player_name,params.player_goals,params.player_image,
                                                                    params.player_team)
        better_config.db_put(query)
