from flask import Flask, render_template,request, redirect, session, flash, Response
from datetime import datetime, date
from mysqlconnection import connectToMySQL 
from pytz import timezone
app = Flask(__name__)
app.secret_key = 'keep it secret, keep it safe'

@app.route("/")
def index():
	
	return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
	errors = {}
	if request.method == "POST":
		try:
			if  len(request.form['first_name']) < 3:
				flash("First Name should be at least 3 characters")
			if  len(request.form['last_name']) < 3:
				flash("Last Name should be at least 3 characters")
			if  request.form["email"] == "":
				flash("Email Address is required")
			if len(request.form['password']) < 8:
				flash("Password should be at least 8 characters")
			if request.form['password'] != request.form['c_password']:
				flash("Passwords do not match")
		except Exception as e:
				flash("Unknown error")
		if '_flashes' in session.keys():
			return redirect('/')
		else:
			mysql = connectToMySQL()
			query = "INSERT INTO users (first_name, last_name, email, password, created_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s,NOW());"
			data = {
				"first_name": request.form['first_name'],
				"last_name": request.form['last_name'],
				"email": request.form['email'],
				"password": request.form['password'],
			}
			mysql.query_db(query, data)
			return redirect("/dashboard")


@app.route("/login", methods = ["POST"])
def login():
	errors = {}
	if request.method == "POST":
		try:
			if  request.form["email"] == "":
				flash("Email Address is required")
			if len(request.form['password']) < 8:
				flash("Password should be at least 8 characters")
		except Exception as e:
				flash("Unknown error")
		if '_flashes' in session.keys():
			return redirect('/')
		else:
			mysql = connectToMySQL()
			query = "SELECT * FROM users WHERE email = %(email)s LIMIT 1;"
			data = {
				"email": request.form['email'],
			}
			user = mysql.query_db(query, data)
			if user:
				try:
					mysql = connectToMySQL()
					query = "SELECT * FROM users WHERE email = %(email)s AND password = %(password)s LIMIT 1;"
					data = {
						"email": request.form['email'],
						"password": request.form['password'],
					}
					user = mysql.query_db(query, data)
					session['is_logged_in'] = True
					session['first_name'] = user[0]['first_name']
					session['user_id'] = user[0]['id']
					session['email'] = user[0]['email']
					return redirect("/dashboard")
				except Exception as e:
					flash("Invalid email and password combination")
					return redirect("/")
			else:
				flash( "Email does not exist in the database")
				return redirect("/")

@app.route("/dashboard", methods = ["GET"])
def dashboard():
	if 'is_logged_in' in session:
		if session['is_logged_in'] == True:
			try:
				mysql = connectToMySQL()
				query = "SELECT * FROM users WHERE id = %(id)s LIMIT 1;"
				data = {
					"id": session['user_id']
				}

				user = mysql.query_db(query, data)
			except Exception as e:
				flash("Invalid session")
				return redirect("/")

			mysql = connectToMySQL()
			query = "SELECT users.id as user_id, jobs.id as job_id, jobs.title as title FROM joins LEFT JOIN jobs ON jobs.id = joins.job_id LEFT JOIN users ON users.id = jobs.user_id;"
			all_jobs = mysql.query_db(query,data)

			all_job_added = []
			upcoming_joined_added = []
			if all_jobs:
				for lists in all_jobs:
					all_job_added.append(lists['job_id'])
					upcoming_joined_added.append(lists['job_id'])
			
				mysql = connectToMySQL()
				query = "SELECT jobs.location as location, users.id as user_id, jobs.id as job_id, jobs.title as title FROM jobs LEFT JOIN users ON users.id = jobs.user_id WHERE jobs.id NOT IN  %(all_job_added)s;"
				data = {
					"all_job_added": all_job_added,
				}
				not_joined = mysql.query_db(query,data)
				mysql = connectToMySQL()
				query = "SELECT  users.id as user_id, jobs.id as job_id, jobs.title as title FROM jobs LEFT JOIN users ON users.id = jobs.user_id WHERE jobs.id IN  %(upcoming_joined_added)s;"
				data = {
					"upcoming_joined_added": upcoming_joined_added,
				}
				all_job = mysql.query_db(query,data)

				return render_template("dashboard.html", user = user,not_joined = not_joined, all_job = all_job)
			else:
				mysql = connectToMySQL()
				query = "SELECT *, users.id as user_id, jobs.id as job_id, jobs.title as title FROM jobs LEFT JOIN users ON users.id = jobs.user_id;"
				not_joined = mysql.query_db(query,data)
				all_job = []
				return render_template("dashboard.html", user = user,not_joined = not_joined, all_job = all_job)

		else:
			flash("User is not logged in")
			return redirect("/")
	else:
		flash("User is not logged in")
		return redirect("/")

@app.route('/job_list/<id>', methods=['GET'])
def joblist(id):
	mysql = connectToMySQL()
	query = "SELECT *, users.id as user_id, jobs.created_at as created,jobs.id as job_id FROM jobs left join users on users.id = jobs.user_id  WHERE jobs.id =  %(id)s;"
	data = {
		"id":{id}
	}
	job = mysql.query_db(query, data)
	return render_template("jobs_list.html", job = job)

@app.route('/delete', methods=['POST'])
def delete():
	mysql = connectToMySQL()
	query = "DELETE FROM jobs WHERE id = %(job_id)s;" 
	data = {
			"job_id": request.form['job_id'],
		}
	mysql.query_db(query, data)
	mysql = connectToMySQL()
	query = "DELETE FROM joins WHERE job_id = %(job_id)s;" 
	data = {
			"job_id": request.form['job_id'],
		}
	mysql.query_db(query, data)
	return redirect('/dashboard')

@app.route('/edits/<id>', methods=['GET'])
def edits(id):
	mysql = connectToMySQL()
	query = "SELECT * FROM jobs WHERE id = %(id)s LIMIT 1;;" 
	data = {
			"id":{id}
		}
	edit_job = mysql.query_db(query, data)
	return render_template("jobs_edit.html", edit_job = edit_job)

@app.route('/update', methods=['POST'])
def update():
	try:
		if  len(request.form['title']) < 3:
			flash("Title should be at least 3 characters.")
		if  len(request.form['description']) < 10:
			flash("Description should be at least 10 characters.")
		if  request.form["location"] == "":
			flash("Location must not blank or empty.")
	except Exception as e:
		flash("Unknown error")
	if '_flashes' in session.keys():
		return redirect('/addjob')
	else:
		mysql = connectToMySQL()
		query = "UPDATE jobs SET  title = %(title)s, description = %(description)s, location = %(location)s WHERE id = %(id)s;"
		data = {
				"id": request.form['id'],
				"title": request.form['title'],
				"description": request.form['description'],
				"location": request.form['location'],
		}
		mysql.query_db(query, data)
		flash("Successful Edit!")
		return redirect('/dashboard')

@app.route('/addjob', methods=['GET'])
def add_job():
	return render_template("add_job.html")

@app.route('/add', methods=['POST'])
def add():
	if request.method == "POST":
		try:
			if  len(request.form['title']) < 3:
				flash("Title should be at least 3 characters.")
			if  len(request.form['description']) < 10:
				flash("Description should be at least 10 characters.")
			if  request.form["location"] == "":
				flash("Location must not blank or empty.")
		except Exception as e:
			flash("Unknown error")
		if '_flashes' in session.keys():
			return redirect('/addjob')
		else:
			mysql = connectToMySQL()
			query = "INSERT INTO jobs (user_id, title, description, location, created_at) VALUES (%(user_id)s,%(title)s,%(description)s,%(location)s, NOW());"
			data = {
				"user_id": session['user_id'],
				"title": request.form['title'],
				"description": request.form['description'],
				"location": request.form['location'],
			}
			mysql.query_db(query, data)
			flash("You just successful added a job!")
			return redirect('/dashboard')

@app.route('/logout', methods=['GET'])
def logout():
	session.clear()
	return redirect("/")

@app.route('/join', methods=['POST'])
def join():
	mysql = connectToMySQL()
	query = "INSERT INTO joins (user_id, job_id, created_at) VALUES (%(user_id)s, %(job_id)s, NOW());"
	data = {
		"user_id": request.form['user_id'],
		"job_id":request.form['job_id'],
	}
	join = mysql.query_db(query,data)
	flash("Successful added in your job!")
	return redirect('/dashboard')


if __name__ == "__main__":
	app.run(port=8000, debug=True)
