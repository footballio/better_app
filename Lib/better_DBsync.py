import json
import requests
import better_config


class match_update():
    def __init__(self,match_json,key):
        self.match_id = None
        self.match_type = None
        self.match_status = None
        self.match_start = None
        self.match_hteam = None
        self.match_ateam = None
        self.match_hscore = None
        self.match_ascore = None
        self.match_hscore = None
        self.match_winner = None
        self.match_id = key['id']
        self.match_type = key['roundInfo']['round']
        self.match_status = key['status']['type']
        self.match_start = key['startTimestamp']
        self.match_hteam = key['homeTeam']['name']
        self.match_ateam = key['awayTeam']['name']
        self.match_hscore = key['homeScore']['current']
        self.match_ascore = key['awayScore']['current']
        if self.match_hscore == self.match_ascore:
            self.match_outcome = 3
        elif self.match_hscore > self.match_ascore:
            self.match_outcome = 1
        elif self.match_hscore < self.match_ascore:
            self.match_outcome = 2
        else:
            pass
        self.match_winner = key['winnerCode']

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

def sync_mastches():
    url = "https://sofascore.p.rapidapi.com/tournaments/get-matches"

    querystring = {"tournamentId": "34","seasonId": "37167","pageIndex": "0"}

    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    matches_json = json.loads(response)
    for key in matches_json['events']:
        params = match_update(matches_json,key)
        query = """IF EXISTS (SELECT * FROM dbo.matches WHERE MID = '{}')
                         UPDATE matches
                         SET match_type='{}',match_status='{}',match_start='{}',match_hteam='{}',match_ateam='{}',match_hscore='{}',match_ascore='{}',match_outcome='{}',match_winner='{}'
                         WHERE MID = '{}'
                     ELSE
                         INSERT INTO matches (MID,match_type,match_status,match_start,match_hteam,match_ateam,match_hscore,match_ascore,match_outcome,match_winner)
                         VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(params.match_id,params.match_type,params.match_status,
                                                                                              params.match_start,params.match_hteam,
                                                                                              params.match_ateam,params.match_hscore,
                                                                                              params.match_ascore,params.match_outcome,
                                                                                              params.match_winner,params.match_id,params.match_id,
                                                                                              params.match_type,params.match_status,
                                                                                              params.match_start,params.match_hteam,
                                                                                              params.match_ateam,params.match_hscore,
                                                                                              params.match_ascore,params.match_outcome,
                                                                                              params.match_winner)
        better_config.db_put(query)


def sync_standings():
    url = "https://api-football-beta.p.rapidapi.com/standings"
    querystring = {"season": "2020","league": "2"}

    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    standings_response = json.loads(response)
    standings_json = standings_response['response'][0]['league']['standings']
    # print(standings_json)
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
    key = 0
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
