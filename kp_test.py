from flask import Flask, render_template, request, session, redirect, url_for
import requests
import base64
import time
import json

app = Flask(__name__)
app.secret_key = 'bajsmannen123'

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/kp", methods=["GET", "POST"])
def klarna_payments():
    response_data = None
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
        data = {
            "purchase_country": "SE",
            "purchase_currency": "SEK",
            "locale": "sv-SE",
            "order_amount": 10000,
            "order_tax_amount": 2000,
            "order_lines": [
                {
                    "type": "physical",
                    "reference": "123050",
                    "name": "Tomatoes",
                    "quantity": 10,
                    "unit_price": 500,
                    "tax_rate": 2500,
                    "total_tax_amount": 1000,
                    "total_amount": 5000
                },
                {
                    "type": "physical",
                    "reference": "543670",
                    "name": "Bananas",
                    "quantity": 20,
                    "unit_price": 250,
                    "tax_rate": 2500,
                    "total_tax_amount": 1000,
                    "total_amount": 5000
                }
            ]
        }

        response = requests.post("https://api.playground.klarna.com/payments/v1/sessions", headers=headers, json=data)

        if response.ok == True:
            response_data = response.json()
            session["session_id"] = response_data['session_id']
        return render_template("kp_template.html", response_data=response_data)
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

    while 'authorization_token' not in response_data:
        response = requests.get("https://api.playground.klarna.com/payments/v1/sessions/" + session["session_id"], headers=headers)
        response_data = response.json()
        time.sleep(1)
    else:
        authorization_token = response_data["authorization_token"]

        order_line_data= {key: response_data[key] for key in ("order_lines", "order_amount", "purchase_country", "purchase_currency")}
        
        response = requests.post("https://api.playground.klarna.com/payments/v1/authorizations/" + authorization_token + "/order", headers=headers, json=order_line_data)
        
        if response.ok == True:
            session.clear()
            return render_template("grattis.html", response_data=response_data)
        else:
            session.clear()
            return "Order creation failed", 500

@app.route("/kco", methods=["GET", "POST"])
def klarna_checkout():
    response_data = None
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
        data = {
            "purchase_country": "SE",
            "purchase_currency": "SEK",
            "locale": "sv-SE",
            "order_amount": 10000,
            "order_tax_amount": 2000,
            "order_lines": [
                {
                    "type": "physical",
                    "reference": "123050",
                    "name": "Tomatoes",
                    "quantity": 10,
                    "unit_price": 500,
                    "tax_rate": 2500,
                    "total_tax_amount": 1000,
                    "total_amount": 5000
                },
                {
                    "type": "physical",
                    "reference": "543670",
                    "name": "Bananas",
                    "quantity": 20,
                    "unit_price": 250,
                    "tax_rate": 2500,
                    "total_tax_amount": 1000,
                    "total_amount": 5000
                }
            ],
            "merchant_urls":{
            "terms": "https://www.example.com/terms.html",
            "checkout": "https://www.example.com/checkout.html?order_id={checkout.order.id}",
            "confirmation": "https://www.example.com/confirmation.html?order_id={checkout.order.id}",
            "push": "https://www.example.com/api/push?order_id={checkout.order.id}"
            },
        }
        response = requests.post("https://api.playground.klarna.com/checkout/v3/orders", headers=headers, json=data)

        if response.ok == True:
            response_data = response.json()
        return render_template("kco_template.html", response_data=response_data)
    else:
        return render_template("kco_template.html", response_data=response_data)

if __name__ == "__main__":
    app.run(debug=False)
