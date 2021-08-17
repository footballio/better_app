import pyodbc
from flask import Flask, request
import json
import better_DBsync as db_syncer
import time
import better_config

app = Flask(__name__)

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
    query_put = """INSERT INTO dbo.users(u_mail, u_name, u_pass) VALUES ('{}','{}','{}');""".format(newusermail,newusername,newpassword)
    better_config.db_put(query_put)
    query_userid = """SELECT UID from dbo.users WHERE u_mail='{}'""".format(newusermail)
    user_id = better_config.db_pull_val(query_userid)
    print(user_id)
    return 'userID = {}'.format(user_id)

@app.route('/form-login',methods=['POST'])
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
            return ('Wrong username / password')

@app.route('/pull-bets', methods=['GET'])
def pullbets():
    UID = request.args['UID']
    LID = request.args['LID']
    query = """SELECT UID,n_type, m_status, m_hteam, m_ateam, m_hscore, m_ascore, m_outcome, m_winner
            FROM dbo.betlog
            WHERE UID='{}', LID='{}'""".format(UID, LID)
    response = better_config.db_pull_list(query)
    return response

@app.route('/submit-bet',methods=['POST'])
def submitbets():


    return 'Form Data Example'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    db_syncer.sync_scorers()
    #db_syncer.sync_mastches()
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