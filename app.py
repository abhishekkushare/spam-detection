import os
import warnings
from datetime import timezone
from zoneinfo import ZoneInfo

warnings.filterwarnings("ignore")

import MySQLdb
from flask import redirect, session
from flask import Flask, render_template, make_response, request, flash, url_for
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from dotenv import load_dotenv
from model import load_model, process_sms

load_dotenv()

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'abhishek')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'abhishek')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'SMS_SPAM_DETECTION')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super secret key')

IST = ZoneInfo("Asia/Kolkata")

TWILIO_ACCOUNT_SID = None
TWILIO_AUTH_TOKEN = None
twilio_api = None


def get_db_connection():
    return MySQLdb.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        passwd=app.config["MYSQL_PASSWORD"],
        db=app.config["MYSQL_DB"],
        charset="utf8mb4",
    )


def fetch_user_by_authid(authid):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM users WHERE authid = %s ORDER BY id DESC LIMIT 1",
            (authid,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
    finally:
        conn.close()


@app.template_filter("ist")
def format_ist(value):
    if not value:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST).strftime("%d %b %Y\n%I:%M %p IST")


@app.context_processor
def inject_user():
    return {
        'logged_in': session.get('logged_in', False),
        'user_label': session.get('user_name') or session.get('user_sid') or '',
    }


def insert_user(name, authid, tno):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users(name,authid,tno) VALUES(%s,%s,%s)",
            (name, authid, tno),
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def insert_feedback(name, suggestions):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback(name, suggestions) VALUES(%s, %s)",
            (name, suggestions),
        )
        conn.commit()
        cursor.close()
    finally:
        conn.close()

@app.route("/")
def root():
    return redirect(url_for('index'))
    
@app.route("/homepage", methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/login', methods = ['POST', 'GET'])
def login():
    global TWILIO_ACCOUNT_SID
    global TWILIO_AUTH_TOKEN
    global twilio_api
	
    if request.method == 'POST':
        authid = request.form['s_id'].strip()
        token = request.form['token'].strip()
        TWILIO_ACCOUNT_SID = authid
        TWILIO_AUTH_TOKEN = token
        try:
            user_name = fetch_user_by_authid(authid) or authid
        except Exception:
            user_name = authid

        try:
            twilio_api = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            twilio_api.api.accounts(TWILIO_ACCOUNT_SID).fetch()
            session['logged_in'] = True
            session['user_name'] = user_name
            session['user_sid'] = TWILIO_ACCOUNT_SID
            session['user_token'] = TWILIO_AUTH_TOKEN
            return redirect(url_for('inbox'))
        except Exception:
            flash("ID and Token is not valid")
            return render_template('index.html')


@app.route('/logout')
def logout():
    global TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, twilio_api
    TWILIO_ACCOUNT_SID = None
    TWILIO_AUTH_TOKEN = None
    twilio_api = None
    session.clear()
    return redirect(url_for('index'))
        
def get_twilio_client():
    global twilio_api

    if twilio_api is not None:
        return twilio_api

    sid = session.get('user_sid')
    token = session.get('user_token')

    if not sid or not token:
        return None

    try:
        twilio_api = Client(sid, token)
        twilio_api.api.accounts(sid).fetch()
        return twilio_api
    except Exception:
        twilio_api = None
        return None

@app.route("/inbox")
def inbox():
    if get_twilio_client() is None:
        session.clear()
        flash("Please log in with valid Twilio credentials first.")
        return redirect(url_for('index'))

    spam_msg, not_spam_msg = get_sms_and_predict(0, 10)
    return render_template(
        'inbox.html',
        spam_msg=spam_msg,
        not_spam_msg=not_spam_msg
    )
    

@app.route("/contact", methods=['GET', 'POST'])
def contactpage():
    if request.method == 'POST':
        name = request.form.get('uname', '').strip()
        suggestions = request.form.get('suggestions', '').strip()
        if not name or not suggestions:
            flash("Please enter your name and suggestions.", "error")
            return redirect(url_for('contactpage'))
        try:
            insert_feedback(name, suggestions)
            flash("Thanks for your feedback", "success")
        except Exception as exc:
            flash(f"Could not save feedback: {exc}", "error")
        return redirect(url_for('contactpage'))
    return render_template('contactus.html')



@app.route("/register",methods = ['POST', 'GET'])
def register():
    if request.method == 'POST':        
        name = request.form['name']
        authid = request.form['authid']
        tno = request.form['tno']
        # conn = mysql.connect()
        # cur = connection.cursor()
        try:
            insert_user(name, authid, tno)
            flash("You have registered successfully.")
        except Exception as exc:
            flash(f"Registration failed: {exc}")
        return render_template('register.html')
        
    if request.method == 'GET':
            return render_template('register.html')


def get_sms_and_predict(start, end):
    '''
    Return predictions for the sms between start and end.
    This is efficient for paginations
    '''
    model = load_model() ## load saved model
    sms = list(twilio_api.messages.stream())
    if (end > len(sms)):
        end = len(sms)

    sub_sms = sms[start:end]
    print(sub_sms)
    spam_msg = []
    not_spam_msg = []
    for msg in sub_sms:
        txt = msg.body
        txt = process_sms(txt)
        pred = (model.predict(txt) > 0.5).astype("int32").item()

        if pred == 1:
            spam_msg.append(msg)
        else:
            not_spam_msg.append(msg)
    return spam_msg, not_spam_msg

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001, debug=True)

