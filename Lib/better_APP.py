from flask import Flask, request
import better_DBsync as dbSyncer
import datetime
import better_config
import collections
import json

app = Flask(__name__)


class bets_update:
    def __init__(self, key):
        self.mid = None
        self.home = None
        self.away = None
        self.outcome = None
        self.winner = None
        self.mid = key['match']['id']
        self.home = key['match']['home']
        self.away = key['match']['away']
        self.outcome = key['match']['outcome']
        if "winner" in key:
            self.winner = key['match']['winner']


@app.route('/form-register', methods=['POST'])
def form_register():
    newusermail = request.args['email']
    newname = request.args['name']
    newpassword = request.args['password']
    existing_mail = better_config.db_pull_list("SELECT u_mail FROM dbo.users WHERE u_mail = ?", newusermail)
    if newusermail in existing_mail:
        return "Error. E-Mail already exists"
    else:
        pass
    query_put = "INSERT INTO dbo.users(u_mail, u_name, u_pass) VALUES (?,?,?)"
    query_params = (newusermail, newname, newpassword)
    better_config.db_put(query_put, query_params)
    query_userid = "SELECT UID from dbo.users WHERE u_mail=?"
    user_id = better_config.db_pull_val(query_userid, newusermail)
    return user_id


@app.route('/form-login', methods=['POST'])
def form_login():
    if request.method == 'POST':
        mail = request.args['email']
        password = request.args['password']
        query_validate = "SELECT u_pass FROM dbo.users WHERE u_mail=?"
        identity = better_config.db_pull_val(query_validate, mail)
        if identity == password:
            query_userid = "SELECT UID from dbo.users WHERE u_mail=?"
            user_id = better_config.db_pull_val(query_userid, mail)
            return user_id
        else:
            return 'Wrong username / password'


@app.route('leagues/leagueCreate', methods=['GET'])
def league_create():
    uid = request.args['UID']
    leaguename = request.args['league_name']
    pay_url = request.args['pay_url']
    query = "INSERT INTO dbo.leagues (league, admin_uid) VALUES (?,?)"
    query_params = (leaguename, uid)
    better_config.db_put(query, query_params)
    leagueID = better_config.db_pull_val("SELECT LID FROM dbo.leagues WHERE LID = (SELECT MAX(LID) FROM dbo.leagues WHERE admin_uid=?)", uid)
    better_config.db_put("INSERT INTO dbo.leagues (UID, LID) VALUES (?,?)", (uid, leagueID))
    if pay_url:
        query_pay = "UPDATE dbo.leagues SET pay_url=? WHERE (LID=?)"
        params_pay = (pay_url, leagueID)
        better_config.db_put(query_pay, params_pay)
    return leagueID


@app.route('leagues/leagueJoin', methods=['GET'])
def league_join():
    uid = request.args['UID']
    lid = request.args['LID']
    check = "SELECT COUNT(1) FROM dbo.leagues WHERE LID=?"
    lid_check = better_config.db_pull_val(check, lid)
    if lid_check == 0:
        return "Error: couldn't find league'"
    else:
        query = "INSERT INTO dbo.leagues (UID, LID) VALUES (?,?)"
        query_params = (uid, lid)
        better_config.db_put(query, query_params)
        return "Success"


@app.route('leagues/pullLeagueBets', methods=['GET'])
def pullbets_lid():
    table = []
    lid = request.args['LID']
    query = "SELECT UID, m_round, m_status, m_hteam, m_ateam, m_hscore, m_ascore, m_outcome, m_winner, goaler_PID, winner_TID FROM dbo.betlog " \
            "WHERE LID=?"
    rows = better_config.db_pull_list(query, lid)
    for row in rows:
        r = collections.OrderedDict()
        r["Match"] = row[0]
        r["m_round"] = row[1]
        r["m_status"] = row[2]
        r["m_time"] = row[3]
        r["m_hscore"] = row[4]
        r["m_ascore"] = row[5]
        r["m_outcome"] = row[6]
        r["m_winner"] = row[7]
        r["goaler"] = row[8]
        r["WINNER"] = row[9]
        table.append(r)
    response = json.dumps(table)
    return response


@app.route('users/pullUserBets', methods=['GET'])
def pullbets_uid():
    table = []
    uid = request.args['UID']
    lid = request.args['LID']
    query = "SELECT UID, m_round, m_status, m_hteam, m_ateam, m_hscore, m_ascore, m_outcome, m_winner, goaler_PID, winner_TID FROM dbo.betlog " \
            "WHERE UID=?, LID=?"
    query_params = (uid, lid)
    rows = better_config.db_pull_list(query, query_params)
    for row in rows:
        r = collections.OrderedDict()
        r["Match"] = row[0]
        r["m_round"] = row[1]
        r["m_status"] = row[2]
        r["m_time"] = row[3]
        r["m_hscore"] = row[4]
        r["m_ascore"] = row[5]
        r["m_outcome"] = row[6]
        r["m_winner"] = row[7]
        r["goaler"] = row[8]
        r["WINNER"] = row[9]
        table.append(r)
    response = json.dumps(table)
    return response


@app.route('users/submit-bet', methods=['POST'])
def submitbets():
    bets_json = request.get_json()
    uid = bets_json['parameters']['UID']
    lid = bets_json['parameters']['LID']
    if "bets" in bets_json:
        u_winner = bets_json['bets']['winner']
        u_goaler = bets_json['bets']['goaler']
        query_bets = "IF EXISTS (SELECT MID FROM dbo.betlog WHERE (UID=? AND LID=? AND MID=0)) UPDATE dbo.betlog SET log_time,winner_TID=?," \
                     "goaler_PID=? WHERE (UID=? AND LID=? AND MID=0) ELSE INSERT INTO dbo.betlog (UID,LID,MID,log_time,winner_TID,goaler_PID) " \
                     "VALUES (?,?,0,?,?,?)"
        querybets_params = (uid, lid, datetime.datetime.now(), u_winner, u_goaler, uid, lid, uid, lid, datetime.datetime.now(), u_winner, u_goaler)
        better_config.db_put(query_bets, querybets_params)
    if "matches" in bets_json:
        for match in bets_json['matches']:
            params = bets_update(match)
            query_matches = "IF EXISTS (SELECT * FROM dbo.betlog WHERE (UID=? AND LID=? AND MID=?)) UPDATE dbo.betlog SET log_time=?,b_hscore=?," \
                            "b_ascore=?,b_outcome=?,b_winner=? WHERE (UID=? AND LID=? AND MID=?) ELSE INSERT INTO dbo.betlog (UID,LID,MID,log_time," \
                            "b_hscore,b_ascore,b_outcome,b_winner) VALUES (?,?,?,?,?,?,?,?)"
            querymatch_params = (uid, lid, params.mid, datetime.datetime.now(), params.home, params.away, params.outcome, params.winner, uid, lid,
                                 params.mid, uid, lid, params.mid, datetime.datetime.now(), params.home, params.away, params.outcome, params.winner)
            better_config.db_put(query_matches, querymatch_params)
    return "Success"


@app.route('/matches', methods=['GET'])
def matches_result():
    table = []
    query = "SELECT * FROM dbo.matches"
    query_params = ()
    rows = better_config.db_pull_list(query, query_params)
    for row in rows:
        r = collections.OrderedDict()
        r["MID"] = row[0]
        r["m_round"] = row[1]
        r["m_status"] = row[2]
        r["m_time"] = row[3]
        r["m_home_TID"] = row[4]
        r["m_away_TID"] = row[5]
        r["m_hscore"] = row[6]
        r["m_ascore"] = row[7]
        r["m_outcome"] = row[8]
        r["m_winner"] = row[9]
        table.append(r)
    response = json.dumps(table)
    return response


@app.route('/players', methods=['GET'])
def players():
    table = []
    query = "SELECT * FROM dbo.players"
    query_params = ()
    rows = better_config.db_pull_list(query, query_params)
    for row in rows:
        r = collections.OrderedDict()
        r["PID"] = row[0]
        r["p_name"] = row[1]
        r["TID"] = row[2]
        r["p_goals"] = row[3]
        r["p_image"] = row[4]
        table.append(r)
    response = json.dumps(table)
    return response


@app.route('/players/scorers', methods=['GET'])
def scorers():
    table = []
    query = "SELECT * FROM dbo.players WHERE p_goals > 0 ORDER BY p_goals DESC"
    query_params = ()
    rows = better_config.db_pull_list(query, query_params)
    for row in rows:
        r = collections.OrderedDict()
        r["PID"] = row[0]
        r["p_name"] = row[1]
        r["TID"] = row[2]
        r["p_goals"] = row[3]
        r["p_image"] = row[4]
        table.append(r)
    response = json.dumps(table)
    return response


@app.route('/king_runner', methods=['GET'])
def runner():
    table = []
    run_scorers = request.args['scorers']
    run_teams = request.args['teams']
    run_matches = request.args['matches']
    run_players = request.args['players']
    if run_scorers:
        dbSyncer.sync_scorers()
        table.append("scorers synced")
    else:
        pass
    if run_teams:
        dbSyncer.sync_teams()
        table.append("teams synced")
    else:
        pass
    if run_matches:
        dbSyncer.sync_matches()
        table.append("matches synced")
    else:
        pass
    if run_players:
        dbSyncer.sync_players()
        table.append("players synced")
    else:
        pass
    response = json.dumps(table)
    return response


@app.route('/king_setting/pay', methods=['GET'])
def user_payment():
    uid = request.args['uid']
    lid = request.args['lid']
    query = "IF EXISTS (SELECT * FROM dbo.league_users WHERE (UID=? AND LID=?)) UPDATE dbo.league_users SET u_paid=? WHERE (UID=? AND LID=?)" \
            "ELSE INSERT INTO dbo.league_users (UID,LID,payment) VALUES (?,?,?)"
    query_params = (uid, lid, 1, uid, lid, uid, lid, 1)
    better_config.db_put(query, query_params)
    return "Success"


if __name__ == '__main__':
    app.run(debug=True, port=5000)
    # dbSyncer.sync_matches()
    # db_syncer.sync_mastches()
    # while True:
    #     # if x time passed since last timestamp, else pass
    #     this_run = datetime.datetime.now()
    #     if (this_run - sync_time.scorer_lastrun).seconds > 1800 :
    #         try:
    #             db_syncer.sync_scorers()
    #         except:
    #             print("Error - couldn't complete dbo.scorers update")
    #     if (this_run - sync_time.scorer_lastrun).seconds > 900 :
    #         try:
    #             db_syncer.sync_matches()
    #         except:
    #             print("Error - couldn't complete dbo.matches update")
    #     if (this_run - sync_time.scorer_lastrun).seconds > 60:
    #         try:
    #             db_syncer.sync_results()
    #         except:
    #             print("Error - couldn't complete dbo.results update")
    #
    #     time.sleep(60)
