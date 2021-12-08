from flask import Flask, render_template, request, redirect, url_for, Markup, session, flash, send_file, send_from_directory
from flask_login import logout_user
import psycopg2
import json
from io import BytesIO
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'studyspotz'
app.config['UPLOAD_FOLDER'] = os.getcwd() + '/static'

def getConnection():
    conn = psycopg2.connect(database='postgres', user='postgres', password='postgres', host='study-spotz.cyeatfrrbwcm.us-east-1.rds.amazonaws.com' , port='5432')
    return conn

def getCursor(conn):
    return conn.cursor()

def passwordStrength(password):
    uppercase = 0
    lowercase = 0
    number = 0
    for char in password:
        if char.isupper():
            uppercase += 1
        elif char.islower():
            lowercase +=1 
        elif char.isdigit():
            number += 1
    if uppercase >= 1 and lowercase >= 1 and number >= 1 and len(password) >= 8:
        return True
    return False

@app.route('/')
@app.route("/signup")
def signup():
    email = request.args.get('email')
    password = request.args.get('password')
    username = request.args.get('username')
    name = request.args.get('name')
    security = request.args.get('question')
    try:
        errorMessage = Markup(json.loads(session['messages'])['main'])
        session['messages'] = json.dumps({"main":''})
    except:
        errorMessage = ''
    if email != None and password != None and username != None and name != None and security != None:
        return register(name, username, email, password, security)
    return render_template('CreateAccount.html', errorMessage = errorMessage)

def register(name, username, email, password, security):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute("""SELECT * FROM users WHERE email = %s""", (email,))
    errorMessage = ''
    if email == '':
        errorMessage += '*Please enter an email address.<br>'
    elif cur.fetchone() != None:
        errorMessage += '*The email you entered already exits. Please sign in using that email. <br>'
    cur.execute("""SELECT * FROM users WHERE username = %s""", (username,))
    if username == '':
        errorMessage += '*Please enter an username. <br>'
    elif cur.fetchone() != None:
        errorMessage += '*The username you have entered already exists. Please enter a different username<br>'
    if password == '':
        errorMessage += '*Please enter a password.<br>'
    elif passwordStrength(password) == False:
        errorMessage += '*The password you have entered is weak. Please make sure you have at least 8 characters, an uppercase letter, a lowercase letter, and a number.<br>'
    if name == '':
        errorMessage += '*Please enter a name. <br>'
    if security == '':
        errorMessage += '*Please answer the security question. <br>'
    if errorMessage != '':
        cur.close()
        conn.close()
        session['messages'] = json.dumps({"main":errorMessage})
        return redirect(url_for('signup'))

    cur.execute("""INSERT INTO users (username, name, email, password, securityquestion) VALUES (%s, %s, %s, %s, %s)""", (username, name, email, password, security))
    conn.commit()
    cur.close()
    conn.close()
    # flash('Account successfully created!','success')
    return redirect(url_for('profile', username = username, user=username))


def loggedIn(email, password):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute("""SELECT * FROM users  WHERE email = %s""", (email,))
    allData = cur.fetchall()
    cur.execute("""SELECT password FROM users WHERE email = %s""", (email,))
    correctPassword = cur.fetchone()[0]
    errorMessage= ''
    if email == '':
        errorMessage += "*Please enter an email<br>"
    elif len(allData) == 0:
        errorMessage += "*Incorrect email <br>"
    if password == '':
        errorMessage += "*Please enter a password <br>"
    elif len(allData) != 0 and correctPassword != password:
        errorMessage += "*Incorrect password\n"
    if errorMessage != '':
        cur.close()
        conn.close()
        session['messages'] = json.dumps({"main":errorMessage})
        return redirect(url_for('login'))
    elif len(allData) == 1 and correctPassword == password:
        cur.close()
        conn.close()
        session['logged_in'] = True
        # flash('Successfully logged in!','success')
        return redirect(url_for('home', username=allData[0][0]))

@app.route('/login/')
def login():
    email = request.args.get('email')
    password = request.args.get('password')
    try:
        errorMessage = Markup(json.loads(session['messages'])['main'])
        session['messages'] = json.dumps({"main":''})
    except:
        errorMessage = ''
    if password != None and email != None:
        return loggedIn(email, password)
    return render_template('Login.html', errorMessage = errorMessage)

def reset(email, password, confirmPassword, security):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute("SELECT * FROM users WHERE email=%s", (email, ))
    errorMessage = ''

    errorMessage = ''
    if email == '':
        errorMessage += '*Please enter an email address.<br>'
    elif cur.fetchone() == None:
        errorMessage += '*The email you entered does not exist. <br>'
    if security == '':
        errorMessage += '*Please answer the security question. <br>'
    if password == '':
        errorMessage += '*Please enter a password.<br>'
    elif passwordStrength(password) == False:
        errorMessage += '*The password you have entered is weak. Please make sure you have at least 8 characters, an uppercase letter, a lowercase letter, and a number.<br>'
    if confirmPassword == '':
        errorMessage += '*Please enter confirm password.<br>'
    if password != confirmPassword:
        errorMessage += '*Confirm password not the same as password <br>'
    cur.execute("SELECT securityquestion FROM users WHERE email=%s", (email, ))
    val = cur.fetchone()[0]
    if val != security:
        errorMessage += '*Incorrect answer to the security question <br>'
    if errorMessage != '':
        cur.close()
        conn.close()
        session['messages'] = json.dumps({"main":errorMessage})
        return redirect(url_for('resetPassword'))
    cur.execute("""UPDATE users SET password = %s WHERE email = %s""", (password, email))
    conn.commit()
    cur.execute("SELECT * FROM users WHERE email=%s", (email, ))
    print(cur.fetchone())
    cur.close()
    conn.close()
    return redirect(url_for('login'))

@app.route('/resetPassword', methods=['GET', 'POST'])
def resetPassword():
    email = request.args.get('email')
    password = request.args.get('password')
    confirmPassword = request.args.get('confirmPassword')
    security = request.args.get('question')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        security = request.form['question']
    print(email)
    try:
        errorMessage = Markup(json.loads(session['messages'])['main'])
        session['messages'] = json.dumps({"main":''})
    except:
        errorMessage = ''
    if email != None and password != None and confirmPassword != None and security != None:
        return reset(email, password, confirmPassword, security)

    return render_template('resetPass.html', error = errorMessage)

@app.route('/home/<username>')
def home(username):
    if True:
        conn = getConnection()
        cur = getCursor(conn)
        cur.execute('SELECT name FROM users WHERE username=%s', (username,))
        name = cur.fetchone()[0]
        cur.execute('SELECT groups FROM users WHERE username=%s', (username,))
        groups = cur.fetchone()[0]
        try:
            groups = [(f'/groups/{group}/{username}', group) for group in groups]
        except:
            groups = []
        cur.execute('SELECT avatar FROM users WHERE username=%s', (username,))
        try:
            avatar = cur.fetchone()[0]
            cur.execute('SELECT * FROM documents WHERE id=%s', (avatar,))
            val = cur.fetchone()
            filename = val[1].split('.')
            filename[-1] = 'png'
            filename = '.'.join(filename)
            print(filename)
        except:
            avatar = None
            filename = 'profileimage.png'
        cur.close()
        conn.close()
        print(name)
        return render_template('home.html', name=name, groups=groups, picture=filename)
    # except:
    #     cur.close()
    #     conn.close()
    #     return render_template('home.html')

@app.route('/groups/<username>')
def groups (username):
    groupName = request.args.get('groupName')
    members = request.args.get('members')
    if groupName != None and groupName != '' and members != None and members != '':
        members = members.replace(' ', '').split(',')
        print(members)
        conn = getConnection()
        cur = getCursor(conn)
        members.append(username)
        cur.execute('INSERT INTO groups (name, members) VALUES (%s, %s)', (groupName, members))
        conn.commit()
        for member in members:
            try:
                cur.execute('SELECT groups FROM users where username  = %s', (member,))
                user_groups = cur.fetchone()[0]
                if user_groups == None:
                    user_groups = []
                user_groups.append(groupName)
                cur.execute("""UPDATE users SET groups = %s WHERE username = %s""", (user_groups, member))
                conn.commit()
            except:
                pass
        cur.close()
        conn.close()
        return redirect(url_for('group', groupName=groupName, username=username))
    return render_template('findGroups.html')

@app.route('/groups/<groupName>/<username>', methods=["GET", "POST"])
def group(groupName, username):
    try:
        conn = getConnection()
        cur = getCursor(conn)
        cur.execute('SELECT * FROM groups WHERE name=%s', (groupName,))
        group = cur.fetchone()
        print(group)
        name = group[1]
        members = group[2]
        documents = []
        if group[3] == None or len(group[3]) == 0:
            documents = [] 
        else: 
            for id in group[3]:
                cur.execute('SELECT * FROM documents WHERE id=%s', (id,))
                val = cur.fetchone()
                documents.append(val)
        calander = []
        if group[4] == None or len(group[4]) == 0:
            ['no events']
        else:
            for eventID in group[4]:
                cur.execute('SELECT * FROM events WHERE id=%s', (eventID,))
                val = cur.fetchone()
                calander.append(val)
        todos = []
        if group[5] == None or len(group[5]) == 0:
            todos = [] 
        else:
            for eventID in group[5]:
                cur.execute('SELECT * FROM tasks WHERE id=%s', (eventID,))
                val = cur.fetchone()
                todos.append(val)
        cur.close()
        conn.close()
        print(todos)
        return render_template('groups.html', name=name, members=members, files=documents, events=calander, tasks=todos)
    except:
        cur.close()
        conn.close()
        return render_template('groups.html', name='No name', members=['no members'], files=['no documents'], calander=['no events'], todos=['no todos'])

@app.route('/upload/<group>/<user>', methods=["GET","POST"])
def upload(group, user):
    print("UPLOAD")
    if request.method=='POST':
        file = request.files['inputFile']
        print(file)
        fileDetails = (file.filename, file.read())
        conn = getConnection()
        cur = getCursor(conn)
        cur.execute('INSERT INTO documents (name, content) VALUES (%s, %s) RETURNING id;', (fileDetails[0], fileDetails[1]))
        fileID = cur.fetchone()[0]
        conn.commit()
        cur.execute('SELECT documents FROM groups WHERE name = %s', (group, ))
        documents = cur.fetchone()[0]
        if documents == None:
            documents = []
        documents.append(fileID)
        cur.execute("""UPDATE groups SET documents = %s WHERE name = %s""", (documents, group))
        conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/addEvent/<group>/<user>', methods=['POST'])
def add_event(group, user):
    description = request.form['description']
    date = request.form['date']
    time = request.form['time']
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('INSERT INTO events (description, date, time, done) VALUES (%s, %s, %s, %s) RETURNING id;', (description, date, time, False))
    eventID = cur.fetchone()[0]
    conn.commit()
    cur.execute('SELECT calendar FROM groups WHERE name = %s', (group, ))
    events = cur.fetchone()[0]
    if events == None:
        events = []
    events.append(eventID)
    cur.execute("""UPDATE groups SET calendar = %s WHERE name = %s""", (events, group))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/doneEvent/<group>/<user>/<int:event_id>')
def resolve_event(group, user, event_id):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('SELECT done FROM events WHERE id = %s', (event_id,))
    status = cur.fetchone()[0]
    if status == False:
        status = True
    elif status == True:
        status = False
    cur.execute('UPDATE events SET done = %s WHERE id = %s', (status, event_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/deleteEvent/<group>/<user>/<int:event_id>')
def delete_event(group, user, event_id):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('DELETE FROM events WHERE id=%s', (event_id,))
    conn.commit()
    cur.execute('SELECT calendar FROM groups WHERE name = %s', (group, ))
    val = cur.fetchone()[0]
    print(val)
    print(event_id)
    val.remove(str(event_id))
    cur.execute('UPDATE groups SET calendar = %s WHERE name = %s', (val, group))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/task/<group>/<user>', methods=['POST'])
def add_task(group, user):
    content = request.form['content']
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('INSERT INTO tasks (content, done) VALUES (%s, %s) RETURNING id;', (content, False))
    eventID = cur.fetchone()[0]
    conn.commit()
    cur.execute('SELECT todos FROM groups WHERE name = %s', (group, ))
    events = cur.fetchone()[0]
    if events == None:
        events = []
    events.append(eventID)
    cur.execute("""UPDATE groups SET todos = %s WHERE name = %s""", (events, group))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/deleteTask/<group>/<user>/<int:task_id>')
def delete_task(group, user, task_id):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('DELETE FROM tasks WHERE id=%s', (task_id,))
    conn.commit()
    cur.execute('SELECT todos FROM groups WHERE name = %s', (group, ))
    val = cur.fetchone()[0]
    print(val)
    print(task_id)
    val.remove(str(task_id))
    cur.execute('UPDATE groups SET todos = %s WHERE name = %s', (val, group))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/doneTask/<group>/<user>/<int:task_id>')
def resolve_task(group, user, task_id):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('SELECT done FROM tasks WHERE id = %s', (task_id,))
    status = cur.fetchone()[0]
    if status == False:
        status = True
    elif status == True:
        status = False
    cur.execute('UPDATE tasks SET done = %s WHERE id = %s', (status, task_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/download/<group>/<user>/<id>', methods=['GET', 'POST'])
def download(group, user, id):
    print("DOWNLOAD")
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('SELECT * FROM documents WHERE id=%s', (id,))
    val = cur.fetchone()
    cur.close()
    conn.close()
    return send_file(BytesIO(val[2]), attachment_filename=val[1], as_attachment=True)

@app.route('/delete/<group>/<user>/<file_id>', methods=["GET", "POST"])
def delete_file(group, user, file_id):
    print("DELETE")
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('DELETE FROM documents WHERE id=%s', (file_id,))
    conn.commit()
    cur.execute('SELECT documents FROM groups WHERE name = %s', (group, ))
    val = cur.fetchone()[0]
    val.remove(file_id)
    cur.execute('UPDATE groups SET documents = %s WHERE name = %s', (val, group))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('group', groupName=group, username=user))

@app.route('/profile/<username>/<user>')
def profile (username, user):
    conn = getConnection()
    cur = getCursor(conn)
    cur.execute('SELECT * FROM users WHERE username=%s', (username,))
    userValues = cur.fetchone()
    try:
        userValues = ['' if val == None else val for val in userValues]
        cur.execute('SELECT avatar FROM users WHERE username=%s', (username,))
        try:
            avatar = cur.fetchone()[0]
            cur.execute('SELECT * FROM documents WHERE id=%s', (avatar,))
            val = cur.fetchone()
            filename = val[1].split('.')
            filename[-1] = 'png'
            filename = '.'.join(filename)
        except:
            avatar = None
            filename = 'profileimage.png'
        cur.close()
        conn.close()
        return render_template('profile.html', picture=filename, username=username, name=userValues[1], nickname=userValues[7], school=userValues[8], major=userValues[15], bio=userValues[9], \
        email=userValues[2], phone=userValues[3], twitter=userValues[10], instagram=userValues[11], facebook=userValues[12], snapchat=userValues[13], \
        linkedin=userValues[14], ZOOMMeetingID=userValues[18], show= userValues[18] != None and userValues[18] !='', orginalUser = username==user)
    except:
        cur.close()
        conn.close()
        return render_template('profile.html', orginalUser = username==user)


@app.route('/logout')
def logout ():
	session.pop('username', None)
	return redirect(url_for('login'))
    # return render_template('Login.html')

@app.route('/profile_update/<username>', methods=['GET','POST'])
def profile_update(username):
    variables = ['name', 'nickname', 'school', 'major', 'bio', 'phone', 'twitterID', 'instagramID', 'facebookID', 'snapchatID', 'linkedinID', 'ZOOMMeetingID']
    changed = [field for field in variables if request.args.get(field) != None and request.args.get(field) != '']
    print(changed)
    conn = getConnection()
    cur = getCursor(conn)
    for var in changed:
        cur.execute("UPDATE users SET {} = %s WHERE username = %s".format(var), (request.args.get(var), username))
        conn.commit()
    try:
        if request.files['inputFile']:
            changed.append('avatar')
            print('AVATAR')
            file = request.files['inputFile']
            print(file)
            fileDetails = (file.filename, file.read())
            filename = secure_filename(fileDetails[0])
            filename = filename.split('.')
            filename[-1] = 'png'
            filename = '.'.join(filename)
            file.stream.seek(0)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute('INSERT INTO documents (name, content) VALUES (%s, %s) RETURNING id;', (fileDetails[0], fileDetails[1]))
            fileID = cur.fetchone()[0]
            conn.commit()
            cur.execute("""UPDATE users SET avatar = %s WHERE username = %s""", (fileID, username))
            conn.commit()
    except:
        pass
    cur.close()
    conn.close()
    if changed == []:
        return render_template('profile_update.html')
    return redirect(url_for('profile', username = username, user=username))
@app.route('/uploadAvatar/<user>')
def avatar(user):
    file = request.files['inputFile']
    # print(file)
    return render_template('profile_update.html')
@app.route('/zoom/<user>/<zoomid>')
def zoom(user, zoomid):
    src="https://us04web.zoom.us/j/meetingID?pwd=MDhKL1hGeHcvZ3RaejVhWW54WDBRUT09".replace('meetingID', zoomid)
    return render_template('zoom.html', src=src)

if __name__=='__main__':
	app.run(debug=True)
