######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
#for image uploading
from werkzeug import secure_filename
import os, base64
import time
import datetime


mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'EASDFGHTYJ^%$WESRGWEWGESD'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = ''#CHANGE THIS TO YOUR MYSQL USERNAME
app.config['MYSQL_DATABASE_PASSWORD'] = '' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'#CHANGE THIS TO YOUR MYSQL DATABASE NAME
app.config['MYSQL_DATABASE_HOST'] = 'localhost'#CHANGE THIS TO YOUR MYSQLDATABASE HOST
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
	return render_template('improved_register.html', supress='True')

@app.route("/register/", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname=request.form.get('first_name')
		lname=request.form.get('last_name')
		username=request.form.get('username')
		bio=request.form.get('bio')
		dob=request.form.get('dob')
		home=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (email, password, gender, bio, first_name, last_name, hometown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, gender, bio, fname, lname, home ))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def numFriends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT num_friends FROM Users where Users.user_id='{0}'".format(uid))
	return cursor.fetchone()[0]

def getUserFirstName(email):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()

def getUserFriends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, user_id FROM Users AS friend \
	JOIN Relationships AS connection \
	ON friend.user_id <> '{0}' AND friend.user_id = connection.user_1_id OR friend.user_id = connection.user_2_id AND friend.user_id != '{0}' AND\
	connection.connected = 1 AND connection.user_1_id = '{0}' OR connection.user_2_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUserFeed():
	#User see's most recent photos of entire platform
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id FROM Photos ORDER BY date_of_creation desc")
	return cursor.fetchall()

def getUsersPhotos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT data, caption FROM Photos JOIN Albums WHERE Photos.album_id = Albums.album_id AND Albums.owner_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(data, pid), ...]

def getPhotoLikes():
	cursor = conn.cursor()
	cursor.execute("SELECT  num_likes FROM Photos ORDER BY date_of_creation")
	return cursor.fetchall()

def getPhotoComments():
	cursor = conn.cursor()
	cursor.execute("SELECT text FROM Comments WHERE photo_id = Comments.photo_id ORDER BY date_of_creation")
	return cursor.fetchall()

def postComment(text, uid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	text = request.form.get('text')
	photo_id = getPhotoIdFromPhoto()
	timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments (text, photo_id, date_of_creation, author_id) = '{0}', '{1}', '{2}', '{3}'".format(text, photo_id, timestamp, uid))

def deleteComment(comment_id, uid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Comments WHERE(author_id = '{0}' and photo_id='{1}')".format(uid, photo_id))


def topUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT first_name FROM Users LIMIT 6")
	print( cursor.fetchall())
	return cursor.fetchall()

def topTags():
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT type FROM Tags LIMIT 6")
	print( cursor.fetchall())
	return cursor.fetchall()

def topAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT album_name FROM Albums LIMIT 6")
	print( cursor.fetchall())
	return cursor.fetchall()

#bio
def getUserBio():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT bio FROM Users WHERE Users.user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

#block
def blockUser():
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Relationships (user_1_id, user_2_id, blocked) VALUES ('{0}', '{1}', '{2}')".format(uid, other_uid, 1 ))

# loads photos for profile based on album id(ie, loads only your photos)
def getAlbumPhotos(albumID):
	cursor = conn.cursor()
	cursor.execute("SELECT data from Photos WHERE author_id = '{0}' ORDER BY date_of_creation".format(uid))
	cursor.fetchall()[0]

#load albums
def getUserAlbums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums = cursor.execute("SELECT DISTINCT album_name FROM Albums, Users WHERE Albums.owner_id='{0} ORDER BY date_of_creation'".format(uid))
	return cursor.fetchall()

def getTagId():
	type = request.form.get('tag_type')
	cursor = conn.cursor()
	cursor.execute("SELECT id FROM Tags WHERE type = '{0}'".format(type))
	cursor.fetchone()

def like():
	return 5

# TODO:
def recommandTags():
	return ""

def showTop10User():
	return ''

@app.route('/likes/<pid>', methods=['GET'])
@flask_login.login_required
def likePhoto(photos_id):
	pid = 0
	plusOneLike = 1
	cursor = conn.cursor()
	userliked_list=cursor.fetchall()
	cursor.execute("INSERT INTO Likes VALUES(user_id, photo_id, likes) '{0}', '{1}', ".format(uid, pid, plusOneLike))
	cursor.execute("SET Photos WHERE (photo_id = 0) num_likes + 1")
	return

def getContribution():
	return ''


def findAllPhotoIdFromTag(tags_text):
	return ''

def findAlbumnNamefromId(albums_id):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_name FROM Albums WHERE albums_id = '{0}'".format(albums_id))
	return cursor.fetchone()[0]

def findPhotoOwnerId(photos_id):
	cursor = conn.cursor()
	cursor.execute("SELECT photos_owner_id FROM Photos WHERE photos_id = '{0}'".format(photos_id))
	return cursor.fetchone()[0]

def isTagUnique(tagType):
	cursor = conn.cursor()
	if cursor.execute("SELECT type FROM Tags WHERE Tags.text = '{0}'".format(tagType)):
		return False
	else:
		return True

def existingTag(tagType):
	return ''
# end stuff to do

#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	first_name = getUserFirstName(flask_login.current_user.id)
	friends = getUserFriends()
	albums = getUserAlbums()
	photos = getUsersPhotos()
	bio = getUserBio()
	num_friends = numFriends()
	return render_template('profile.html', name=flask_login.current_user.id, first_name=first_name[0], photos=photos, friends=friends, albums=albums, bio=bio, num_friends=num_friends)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		num_likes = 0
		tags = request.files.get('tags')
		album_name = request.form.get('album')
		photo_data = base64.standard_b64encode(imgfile.read())
		ts = time.time()
		timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (owner_id, album_name, date_of_creation) VALUES ('{0}', '{1}', '{2}')".format(uid, album_name, timestamp ))
		cursor.execute("INSERT INTO Photos (data, caption, date_of_creation, num_likes, tags) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(photo_data, caption, timestamp, num_likes, tags))
		conn.commit()
		return render_template('index.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos() )
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html')


@app.route("/rec", methods=['POST'])
# recommendations
def getReccomendations():
	tag_id = getTagId(type)
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id from Photos AS photo JOIN Tags AS tag \
	WHERE photo.photo_id = tag.photo_id  VALUES ({0}) = (tag_id))")
	cursor.fetchall()

@app.route("/search", methods=['POST'])
# search functionality
def search():
	# Search by user_names
	# Made up for the ease of searching for people with the same name
	first_name = request.form.get('input')
	cursor = conn.cursor()
	cursor.execute("SELECT FROM Friends WHERE first_name = '{0}'".format(first_name))
	cursor.fetchall()

	# Search by tags
	if request.method == 'POST':
		users = request.form.get('users')
		tags = request.form.get('tags')
		tag_list = [(tag) for tag in tags.split(',')]
		cursor = conn.cursor()
		cursor.execute("SELECT photo_id FROM Tags WHERE photo_id IN (%s)" % format_strings, tuple(tag_list))
		photo_ids = cursor.fetchall()
		photo_ids = [id[0] for id in photo_ids]
		format_strings = ','.join(['%s'] * len(photo_ids))
		cursor.execute("SELECT photo_ids, data, caption, user_id, likes FROM Photos WHERE photo_id IN (%s)" % format_strings, tuple(photo_ids))
		data = cursor.fetchall()
		return redirect(url_for('get_albums'))

@app.route("/index", methods=['GET', 'POST'])
def index():
	feed = getUserFeed()
	top5Tags = topTags()
	first_name = getUserFirstName(flask_login.current_user.id)
	top5Albums = topAlbums()
	comment=request.form.get('comments')
	print(comment)
	cursor = conn.cursor()
	ts = time.time()
	timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	cursor.execute("INSERT INTO Comments (text, author_id, photo_id, date_of_creation) VALUES('{0}', '{1}', '{2}', '{3}')".format(comment, 3, 0,  ts ))
	print('comment', comment)
	top5Users = topUsers()
	likes = like()
	photo_likes = getPhotoLikes()
	comments = getPhotoComments()
	search = request.form.get('tags')
	return render_template('index.html', feed=feed, likes=likes, comments=comments, topUsers=top5Users, topTags=top5Tags, topAlbums=top5Albums, first_name = first_name[0])

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)


@app.route("/like", methods=['GET', 'POST'])
def like():
	num = likes()
	num += 1
	return likes(num)
