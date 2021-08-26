from flask import Flask, request
import better_DBsync as dbSyncer
import datetime
import better_config

app = Flask(__name__)


class bets_update:
    def __init__(self, key):
        self.mid = None
        self.m_round = None
        self.home = None
        self.away = None
        self.outcome = None
        self.winner = None
        self.mid = key['match']['id']
        self.m_round = key['match']['type']
        self.home = key['match']['home']
        self.away = key['match']['away']
        self.outcome = key['match']['outcome']
        if "winner" in key:
            self.winner = key['match']['winner']


@app.route('/form_register', methods=['POST'])
def form_register():
    newusermail = request.args['email']
    newusername = request.args['username']
    newpassword = request.args['password']
    existing_mail = better_config.db_pull_list("""SELECT Uname FROM dbo.users""")
    print(existing_mail)
    if newusername in existing_mail:
        return "Error. Username already exists"
    else:
        pass
    query_put = """INSERT INTO dbo.users(u_mail, u_name, u_pass) VALUES ('{}','{}','{}');""".format(newusermail, newusername, newpassword)
    better_config.db_put(query_put)
    query_userid = """SELECT UID from dbo.users WHERE u_mail='{}'""".format(newusermail)
    user_id = better_config.db_pull_val(query_userid)
    print(user_id)
    return 'userID = {}'.format(user_id)


@app.route('/form-login', methods=['POST'])
def form_login():
    if request.method == 'POST':
        mail = request.args['email']
        password = request.args['password']
        query_validate = """SELECT [u_pass] FROM dbo.users WHERE u_mail='{}'""".format(mail)
        identity = better_config.db_pull_val(query_validate)
        if identity == password:
            query_userid = """SELECT UID from dbo.users WHERE u_mail='{}'""".format(mail)
            user_id = better_config.db_pull_val(query_userid)
            return 'userID = {}'.format(user_id)
        else:
            return 'Wrong username / password'


@app.route('/pull-bets', methods=['GET'])
def pullbets():
    uid = request.args['UID']
    lid = request.args['LID']
    b_query = """SELECT UID, LID, b_winner_TID, b_goaler_PID
                 FROM dbo.b_betlog
                 WHERE UID='{}', LID='{}'""".format(uid, lid)
    m_query = """SELECT UID, m_round, m_status, m_hteam, m_ateam, m_hscore, m_ascore, m_outcome, m_winner
                 FROM dbo.m_betlog
                 WHERE UID='{}', LID='{}'""".format(uid, lid)
    m_response = better_config.db_pull_list(m_query)
    b_resonse = better_config.db_pull_list(b_query)
    return "{} \n{}".format(m_response, b_resonse)


@app.route('/submit-bet', methods=['POST'])
def submitbets():
    bets_json = request.get_json()
    uid = bets_json['parameters']['UID']
    lid = bets_json['parameters']['LID']
    if "bets" in bets_json:
        u_winner = bets_json['bets']['winner']
        u_goaler = bets_json['bets']['goaler']
        query_bets = """IF EXISTS (SELECT u_winner FROM dbo.b_betlog WHERE (UID='{}' AND LID='{}'))
                              UPDATE b_betlog
                              SET log_time,b_winner_TID='{}',b_goaler_PID='{}'
                              WHERE (UID='{}' AND LID='{}')
                        ELSE
                              INSERT INTO b_betlog (UID,LID,log_time,u_winner,u_goaler)
                              VALUES ('{}','{}','{}','{}','{}')""".format(uid, lid, datetime.datetime.now(), u_winner, u_goaler, uid, lid,
                                                                          uid, lid, datetime.datetime.now(), u_winner, u_goaler)
        better_config.db_put(query_bets)
    if "matches" in bets_json:
        for match in bets_json['matches']:
            params = bets_update(match)
            query_matches = """IF EXISTS (SELECT * FROM dbo.m_betlog WHERE (UID='{}' AND LID='{}' AND MID='{}'))
                                    UPDATE m_betlog
                                    SET m_round='{}',log_time='{}',b_hscore='{}',b_ascore='{}',b_outcome='{}',b_winner='{}'
                                    WHERE (UID='{}' AND LID='{}' AND MID='{}')
                               ELSE
                                   INSERT INTO m_betlog (UID,LID,MID,m_round,log_time,b_hscore,b_ascore,b_outcome,b_winner)
                                   VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(uid, lid, params.mid, params.m_round,
                                                                                                   datetime.datetime.now(), params.home,
                                                                                                   params.away, params.outcome, params.winner, uid,
                                                                                                   lid, params.mid, uid, lid, params.mid,
                                                                                                   params.m_round, datetime.datetime.now(),
                                                                                                   params.home, params.away, params.outcome,
                                                                                                   params.winner)
            better_config.db_put(query_matches)
    return "Success"


if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    dbSyncer.sync_matches()
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
