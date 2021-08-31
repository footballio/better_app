import json
import requests
import better_config


class match_update:
    def __init__(self, key):
        self.m_id = None
        self.m_round = None
        self.m_status = None
        self.m_time = 0
        self.m_home_TID = 0
        self.m_away_TID = 0
        self.m_hscore = 0
        self.m_ascore = 0
        self.m_outcome = 0
        self.m_winner = None
        self.m_homewin = None
        self.m_awaywin = None
        self.m_id = key['fixture']['id']
        self.m_status = key['fixture']['status']['short']
        self.m_round = key['league']['round']
        self.m_time = better_config.intcheck(key['fixture']['timestamp'])
        self.m_home_TID = better_config.intcheck(key['teams']['home']['id'])
        self.m_away_TID = better_config.intcheck(key['teams']['away']['id'])
        self.m_hscore = better_config.intcheck(key['score']['fulltime']['home'])
        self.m_ascore = better_config.intcheck(key['score']['fulltime']['away'])
        self.m_homewin = key['teams']['home']['winner']
        self.m_awaywin = key['teams']['away']['winner']
        if self.m_hscore == self.m_ascore:
            if self.m_hscore is None:
                self.m_outcome = None
            else:
                self.m_outcome = 3
        elif self.m_hscore > self.m_ascore:
            self.m_outcome = 1
        elif self.m_hscore < self.m_ascore:
            self.m_outcome = 2
        else:
            pass
        if self.m_homewin is True:
            self.m_winner = 1
        elif self.m_awaywin is True:
            self.m_winner = 2
        else:
            pass


class teams_update:
    def __init__(self, key):
        self.t_id = None
        self.t_name = None
        self.t_image = None
        self.group_id = None
        self.t_rank = 0
        self.t_points = 0
        self.t_played = 0
        self.t_wins = 0
        self.t_draws = 0
        self.t_loses = 0
        self.t_gd = 0
        self.t_id = key['team']['id']
        self.t_name = key['team']['name']
        self.t_image = key['team']['logo']
        self.group_id = key['group']
        self.t_rank = better_config.intcheck(key['rank'])
        self.t_points = better_config.intcheck(key['points'])
        self.t_played = better_config.intcheck(key['all']['played'])
        self.t_wins = better_config.intcheck(key['all']['win'])
        self.t_draws = better_config.intcheck(key['all']['draw'])
        self.t_loses = better_config.intcheck(key['all']['lose'])
        self.t_gd = better_config.intcheck(key['goalsDiff'])


class players_update:
    def __init__(self, key):
        self.p_id = None
        self.p_name = None
        self.p_team = None
        self.p_image = None
        self.p_goals = 0
        self.p_id = key['player']['id']
        self.p_name = key['player']['name'].replace("'", "")
        self.p_team = key['statistics'][0]['team']['id']
        self.p_image = key['player']['photo']
        self.p_goals = better_config.intcheck(key['statistics'][0]['goals']['total'])


def sync_matches():
    url = "https://api-football-beta.p.rapidapi.com/fixtures"
    querystring = {"season": better_config.season_params.seasonId, "league": better_config.season_params.leagueId,
                   "from": better_config.season_params.date_from, "to": better_config.season_params.date_to}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    matches_json = json.loads(response)
    for key in matches_json['response']:
        params = match_update(key)
        if params.m_winner is None:
            query = "IF EXISTS (SELECT * FROM dbo.matches WHERE MID = ?) UPDATE matches SET m_round=?,m_status=?,m_time=?,m_hscore=?,m_ascore=?," \
                    "m_outcome=? WHERE MID = ? ELSE INSERT INTO matches (MID,m_round,m_status,m_time,m_home_TID,m_away_TID,m_hscore,m_ascore," \
                    "m_outcome) VALUES (?,?,?,?,?,?,?,?,?)"
            query_params = (params.m_id, params.m_round, params.m_status, params.m_time, params.m_hscore, params.m_ascore, params.m_outcome,
                            params.m_id, params.m_id, params.m_round, params.m_status, params.m_time, params.m_home_TID, params.m_away_TID,
                            params.m_hscore, params.m_ascore, params.m_outcome)
        else:
            query = "IF EXISTS (SELECT * FROM dbo.matches WHERE MID =?) UPDATE matches SET m_round=?,m_status=?,m_time=?,m_hscore=?,m_ascore=?" \
                    ",m_outcome=?,m_winner=? WHERE MID = ? ELSE INSERT INTO matches (MID,m_round,m_status,m_time,m_home_TID,m_away_TID,m_hscore," \
                    "m_ascore,m_outcome,m_winner) VALUES (?,?,?,?,?,?,?,?,?,?)"
            query_params = (params.m_id, params.m_round, params.m_status, params.m_time, params.m_hscore, params.m_ascore, params.m_outcome,
                            params.m_winner, params.m_id, params.m_id, params.m_round, params.m_status, params.m_time, params.m_home_TID,
                            params.m_away_TID, params.m_hscore, params.m_ascore, params.m_outcome, params.m_winner)
        better_config.db_put(query, query_params)


def sync_teams():
    url = "https://api-football-beta.p.rapidapi.com/standings"
    querystring = {"season": better_config.season_params.seasonId, "league": better_config.season_params.leagueId}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    standings_response = json.loads(response)
    standings_json = standings_response['response'][0]['league']['standings']
    for group in standings_json:
        for rank in group:
            params = teams_update(rank)
            query = "IF EXISTS (SELECT * FROM dbo.teams WHERE TID=?) UPDATE teams SET t_rank=?,t_points=?,t_played=?,t_wins=?,t_draws=?,t_loses=?," \
                    "t_goals_diff=? WHERE TID = ? ELSE INSERT INTO teams (TID,t_name,t_image,group_id,t_rank,t_points,t_played,t_wins,t_draws," \
                    "t_loses,t_goals_diff) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
            query_params = (params.t_id, params.t_rank, params.t_points, params.t_played, params.t_wins, params.t_draws, params.t_loses, params.t_gd,
                            params.t_id, params.t_id, params.t_name, params.t_image, params.group_id[-1], params.t_rank, params.t_points,
                            params.t_played, params.t_wins, params.t_draws, params.t_loses, params.t_gd)
            better_config.db_put(query, query_params)


def sync_players():
    url = "https://api-football-beta.p.rapidapi.com/players"
    page = 1
    querystring = {"season": better_config.season_params.seasonId, "league": better_config.season_params.leagueId, "page": page}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    players_json = json.loads(response)
    total_pages = players_json['paging']['total']
    print(total_pages)
    while page <= total_pages:
        for key in players_json['response']:
            params = players_update(key)
            query = "IF EXISTS (SELECT * FROM dbo.players WHERE PID = ?) UPDATE players SET p_goals=? WHERE PID = ? ELSE INSERT INTO players (PID," \
                    "p_name,TID,p_goals,p_image) VALUES (?,?,?,?,?)"
            query_params = (params.p_id, params.p_goals, params.p_id, params.p_id, params.p_name, params.p_team, params.p_goals, params.p_image)
            better_config.db_put(query, query_params)
        page += 1
        querystring = {"season": better_config.season_params.seasonId, "league": better_config.season_params.leagueId, "page": page}
        response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
        players_json = json.loads(response)
        print(page)


def sync_scorers():
    url = "https://api-football-beta.p.rapidapi.com/players/topscorers"
    querystring = {"season": better_config.season_params.seasonId, "league": better_config.season_params.leagueId}
    response = requests.request("GET", url, headers=better_config.headers, params=querystring).text
    players_json = json.loads(response)
    for key in players_json['response']:
        params = players_update(key)
        query = "IF EXISTS (SELECT * FROM dbo.players WHERE PID = ?) UPDATE players SET p_goals=? WHERE PID = ? ELSE INSERT INTO players (PID," \
                "p_name,TID,p_goals,p_image) VALUES (?,?,?,?,?)"
        query_params = (params.p_id, params.p_goals, params.p_id, params.p_id, params.p_name, params.p_team, params.p_goals, params.p_image)
        better_config.db_put(query, query_params)


sync_matches()
# sync_players()
# sync_scorers()
# sync_teams()
