from flask import Flask, render_template,url_for,request, flash, session, redirect, logging
from flask_mysqldb import MySQL
import hashlib
import yaml
import smtplib
import os
from datetime import datetime
import json


app = Flask(__name__)
a = []


#Configure the DB
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
login_password = db['login_password']

mysql = MySQL(app)

@app.route('/')
def index():
	return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		login_details = request.form
		userName = login_details['userName']
		password = login_details['password']
		password = hashlib.md5(password.encode()).hexdigest()
		cur = mysql.connection.cursor()
		cur.execute('SELECT * FROM users WHERE username = %s AND password = %s', (userName, password))
		data = cur.fetchone()
		session['data'] = data
		if data and data[11] == "S":
			return redirect(url_for('home'))
		elif data and data[11] == 'B':
			return redirect(url_for('home_buyer'))
		elif data and data[11] == 'M':
			return redirect(url_for("home_miner"))
		else:
			return 'OOPS'
	return render_template("login.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		# Fetch the user details
		userDetails = request.form
		firstName = userDetails['firstName']
		lastName = userDetails['lastName']
		userName = userDetails['userName']
		password = userDetails['password']
		password = hashlib.md5(password.encode()).hexdigest()
		email = userDetails['email']
		confirmPassword = userDetails['confirmPassword']
		confirmPassword = hashlib.md5(confirmPassword.encode()).hexdigest()
		phone = userDetails['phone']
		ssn = userDetails['ssn']
		role = userDetails['role'][0]
		if role == 'S': 
			stocks = 100
		else:
			stocks = 0
		identity = hashlib.md5(userName.encode()).hexdigest()
		session['identity'] = identity
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO users(fname, lname, username, password, email, confirmpassword, phone, ssn, identity, role, stocks) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (firstName, lastName, userName, password, email, confirmPassword, phone, ssn, identity, role, stocks))
		mysql.connection.commit()
		cur.close()
		if password == confirmPassword:
			msg = "Welcome to your first BlockChain Application"
			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.starttls()
			server.login("ayushkalla2050@gmail.com", login_password)
			server.sendmail("ayushkalla2050@gmail.com", email, msg)
			server.quit()
			return render_template('congrats.html')
		else:
			return 'Password values do not match'
	return render_template("signup.html")

@app.route('/congrats')
def congrats():
	return render_template('congrats.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
	data = session.get('data', None)
	if request.method == 'POST':
		stock = request.form
		stockDeatils = stock['sell_stocks']
		session['stockDeatils'] = stockDeatils
		iden = data[10]
		date = datetime.now()
		date = date.strftime("%d/%m/%Y %H:%M:%S")
		if int(stockDeatils) > 0:
			transactions = {}
			transactions['date'] = date
			transactions['stockDeatils'] = int(stockDeatils)+1
			transactions['identity'] = iden
			transactions['info'] = "Sell"
			a.append(transactions)	
			return redirect(url_for('success'))
	return render_template("home.html", data = data)

@app.route('/home_buyer', methods=['GET', 'POST'])
def home_buyer():
	data = session.get('data', None)
	if request.method == 'POST':
		stock = request.form
		stockDeatils = stock['sell_stocks']
		session['stockDeatils'] = stockDeatils
		iden = data[10]
		date = datetime.now()
		date = date.strftime("%d/%m/%Y %H:%M:%S")
		if int(stockDeatils) > 0:
			transactions = {}
			transactions['date'] = date
			transactions['stockDeatils'] = int(stockDeatils)
			transactions['identity'] = iden
			transactions['info'] = "Buy"
			a.append(transactions)		
			return redirect(url_for('success'))
	return render_template("home_buyer.html", data = data)

@app.route('/home_miner', methods=['GET', 'POST'])
def home_miner():
	data = session.get('data', None)
	if request.method == 'POST':
		return redirect(url_for('success_miner'))
	return render_template("home_miner.html", data = data)

		
@app.route('/success')
def success():
	data = session.get('stockDeatils', None)
	return render_template("success.html", data = data)

@app.route('/success_miner')
def success_miner():
	global a
	data = session.get('data', None)
	cur = mysql.connection.cursor()
	iden = data[10]
	with open('transactions.txt', 'a') as f:
		for i in range(0, len(a)):
			if a[i]['info'] == "Sell":
				cur.execute("UPDATE users SET stocks = stocks - %s WHERE identity = %s", (a[i]['stockDeatils'], [a[i]['identity']]))
			else:
				cur.execute("UPDATE users SET stocks = stocks + %s WHERE identity = %s", (a[i]['stockDeatils'], [a[i]['identity']]))
			

			f.write("%s\n" % a[i])
		cur.execute("UPDATE users SET stocks = stocks + %s WHERE identity = %s", (-1, ["Sell"]))
		cur.execute("UPDATE users SET stocks = stocks + %s WHERE identity = %s", (1, [iden]))
		mysql.connection.commit()
		cur.close()
	a = []
	return render_template("success_miner.html", data = data)

@app.route('/chain')
def chain():
	data = session.get('data', None)
	with open('chain.txt', 'w') as f:
		for i in range(0, len(a)):
			f.write("%s\n" % a[i])
	return render_template("chain.html", data = [data, a])

@app.route('/transactions')
def transactions():
	b = open("transactions.txt").readlines()
	data = session.get('data', None)
	return render_template("transactions.html", data = [data, b])

if __name__ == '__main__':
	app.secret_key = os.urandom(24)
	app.run(debug=True)
