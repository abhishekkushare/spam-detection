import os
import warnings
warnings.filterwarnings("ignore")

from flask import redirect
from flask import Flask, render_template, make_response, request, flash,url_for
from flask_mysqldb import MySQL
#from flaskext.mysql import MySQL
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from dotenv import load_dotenv
from model import load_model,  process_sms

load_dotenv()

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'SMS_SPAM_DETECTION')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super secret key')

mysql = MySQL(app)

TWILIO_ACCOUNT_SID = None
TWILIO_AUTH_TOKEN = None
twilio_api = None


def fetch_user_from_db(authid, token):
    try:
        conn = mysql.connection
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            "select * from users where authid = %s and tno = %s",
            (authid, token),
        )
        account = cursor.fetchone()
        cursor.close()
        return account
    except Exception:
        return None


def insert_user(name, authid, tno):
    conn = mysql.connection
    if conn is None:
        raise RuntimeError("MySQL connection is not available")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users(name,authid,tno) VALUES(%s,%s,%s)",
        (name, authid, tno),
    )
    conn.commit()
    cursor.close()


@app.route("/", methods=['GET', 'POST'])
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
        account = fetch_user_from_db(authid, token)

        if account:
            TWILIO_ACCOUNT_SID = account[0]
            TWILIO_AUTH_TOKEN = account[3]
        else:
            TWILIO_ACCOUNT_SID = authid
            TWILIO_AUTH_TOKEN = token

        try:
            twilio_api = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            twilio_api.api.accounts(TWILIO_ACCOUNT_SID).fetch()
            return redirect(url_for('inbox'))
        except Exception:
            flash("ID and Token is not valid")
            return render_template('index.html')
        

@app.route("/inbox")
def inbox():
    if twilio_api is None:
        flash("Please log in with valid Twilio credentials first.")
        return redirect(url_for('index'))
    spam_msg, not_spam_msg = get_sms_and_predict(0, 10)
    template = render_template('inbox.html', spam_msg=spam_msg, not_spam_msg=not_spam_msg)
    response = make_response(template)
    return response
    return render_template('inbox.html')
    

@app.route("/contact")
def contactpage():
    print(f'Before')
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
        except Exception:
            flash("Registration failed: check MySQL is running and MYSQL_* settings in .env")
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

