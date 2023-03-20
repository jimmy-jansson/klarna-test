from flask import Flask, render_template, request, session
import requests
import base64
import time
import json
import plotly.express as px
import plotly.io as pio
import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'bajsmannen123'

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/kp", methods=["GET", "POST"])
def klarna_payments():
    response_data = None
    if request.method == "POST":
        session.clear()
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username
        session["password"] = password
        usrPass = username + ':' + password
        b64Val = base64.b64encode(usrPass.encode()).decode()
        headers = {"Authorization": "Basic %s" % b64Val,
            "Content-Type": "application/json",
        }
        data = json.loads(request.form["data"])
        if request.form.get("check") == "true":
            data["intent"] = "buy_and_tokenize"
            data["subscription"] =    {
                    "name": "jimmys prenumeration",
                    "interval": "MONTH",
                    "interval_count": "30",
                }
        else:
            data["intent"] = "buy"
        response = requests.post("https://api.playground.klarna.com/payments/v1/sessions", headers=headers, json=data)

        if response.ok == True:
            response_data = response.json()
            session["session_id"] = response_data['session_id']
            return render_template("kp_template.html", response_data=response_data)
        else:
            error_data = response.text
            return render_template("kp_template.html", error_data=error_data)
    else:
        return render_template("kp_template.html", response_data=response_data)

@app.route("/create_order", methods=["GET","POST"])
def create_order():
    username = session["username"]
    password = session["password"]
    usrPass = username + ':' + password
    b64Val = base64.b64encode(usrPass.encode()).decode()
    headers = {"Authorization": "Basic %s" % b64Val,
        "Content-Type": "application/json",
    }

    response = requests.get("https://api.playground.klarna.com/payments/v1/sessions/" + session["session_id"], headers=headers)
    response_data = response.json()
    token_response = None
    token_response_data = None
    while 'authorization_token' not in response_data:
        response = requests.get("https://api.playground.klarna.com/payments/v1/sessions/" + session["session_id"], headers=headers)
        response_data = response.json()
        time.sleep(1)
    else:
        authorization_token = response_data["authorization_token"]
        if response_data["intent"] == "buy_and_tokenize":
                    response_data["subscription"] =    {
                    "name": "jimmys prenumeration",
                    "interval": "MONTH",
                    "interval_count": "30",
                    }
                    response_data["intended_use"] = "subscription"
                    response_data["description"] = "tjäna pengar"
        order_line_data= {key: response_data[key] for key in ("order_lines", "order_amount", "purchase_country", "purchase_currency", "intent")}
        response = requests.post("https://api.playground.klarna.com/payments/v1/authorizations/" + authorization_token + "/order", headers=headers, json=order_line_data)
        if response_data["intent"] == "buy_and_tokenize":
            token_data= {key: response_data[key] for key in ("locale", "purchase_country", "purchase_currency", "subscription", "intent", "intended_use", "description")}
            token_response = requests.post("https://api.playground.klarna.com/payments/v1/authorizations/" + authorization_token + "/customer-token", headers=headers, json=token_data)
            token_response_data = token_response.json()
        response_data = response.json()
        if response.ok == True:
            session.clear()
            return render_template("grattis.html", response_data=response_data, token_response_data=token_response_data)
        else:
            session.clear()
            return "Order creation failed", 500

@app.route("/kco", methods=["GET", "POST"])
def klarna_checkout():
    response_data = None
    session.clear()
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username
        session["password"] = password
        usrPass = username + ':' + password
        b64Val = base64.b64encode(usrPass.encode()).decode()
        headers = {"Authorization": "Basic %s" % b64Val,
            "Content-Type": "application/json",
        }
        data = json.loads(request.form["data"])
        if request.form.get("check") == "true":
            data["intent"] = "buy_and_tokenize"
            data["subscription"] =    {
                    "name": "jimmys prenumeration",
                    "interval": "MONTH",
                    "interval_count": "30",
                }
        response = requests.post("https://api.playground.klarna.com/checkout/v3/orders", headers=headers, json=data)
        if response.ok == True:
            response_data = response.json()
            session["order_id"] = response_data['order_id']
            return render_template("kco_template.html", response_data=response_data)
        else:
            error_data = response.text
            return render_template("kco_template.html", error_data=error_data)
    else:
        return render_template("kco_template.html", response_data=response_data)

@app.route("/tacktack=<order_id>", methods=["GET", "POST"])
def thanks(order_id):
    username = session["username"]
    password =  session["password"]
    usrPass = username + ':' + password
    b64Val = base64.b64encode(usrPass.encode()).decode()
    headers = {"Authorization": "Basic %s" % b64Val,
        "Content-Type": "application/json",
    }
    order_id = session["order_id"]
    response = requests.get("https://api.playground.klarna.com/checkout/v3/orders/" + order_id, headers=headers)
    response_data = response.json()
    session.clear()
    return render_template("grattis_kco.html", response_data=response_data)

@app.route("/recurring", methods=["GET", "POST"])
def klarna_recurring():
    session.clear()
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usrPass = username + ':' + password
        b64Val = base64.b64encode(usrPass.encode()).decode()
        headers = {"Authorization": "Basic %s" % b64Val,
            "Content-Type": "application/json",
        }
        data = json.loads(request.form["data"])
        token_id = request.form["token_id"]
        response = requests.post("https://api.playground.klarna.com/customer-token/v1/tokens/" + token_id + "/order", headers=headers, json=data)
        if response.ok == True:
            response_data = response.json()
            return render_template("recurring_template.html", response_data = response_data)
        else:
            error_data = response.text
            return render_template("recurring_template.html", error_data=error_data)
    else:
        return render_template("recurring_template.html")


lap_data_cache = {}

@app.route('/drivers', methods=['GET', 'POST'])
def drivers_lap_times():
    global lap_data_cache
    
    if not lap_data_cache:
        # If cache is empty, fetch data from API
        lap_data_cache['leclerc'] = requests.get('https://ergast.com/api/f1/2023/1/drivers/leclerc/laps.json').json()['MRData']['RaceTable']['Races'][0]['Laps']
        lap_data_cache['hamilton'] = requests.get('https://ergast.com/api/f1/2023/1/drivers/hamilton/laps.json').json()['MRData']['RaceTable']['Races'][0]['Laps']
        lap_data_cache['norris'] = requests.get('https://ergast.com/api/f1/2023/1/drivers/norris/laps.json').json()['MRData']['RaceTable']['Races'][0]['Laps']
        lap_data_cache['perez'] = requests.get('https://ergast.com/api/f1/2023/1/drivers/perez/laps.json').json()['MRData']['RaceTable']['Races'][0]['Laps']
        lap_data_cache['russell'] = requests.get('https://ergast.com/api/f1/2023/1/drivers/russell/laps.json').json()['MRData']['RaceTable']['Races'][0]['Laps']

    if request.method == 'POST':
        driver = request.form['driver']
    else:
        driver = 'leclerc'

    lap_data = lap_data_cache[driver]

    timing_data = []
    lap_counter = []
    i = 0
    for lap in lap_data:
        lap_time_str = lap['Timings'][0]['time']
        lap_time = datetime.datetime.strptime(lap_time_str, '%M:%S.%f').time()
        lap_time_secs = lap_time.minute * 60 + lap_time.second + lap_time.microsecond / 1000000
        timing_data.append(lap_time_secs)
        lap_counter.append(lap['number'])

    race_df = pd.DataFrame({'lap': lap_counter, 'lap_time': timing_data})
    fig = px.line(race_df, x='lap', y='lap_time')
    graph_html = pio.to_html(fig, full_html=False)

    return render_template('lap_times.html', driver=driver, graph_html=graph_html)


if __name__ == '__main__':
    app.run(debug=True)
