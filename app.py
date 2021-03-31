from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
# from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import urllib
import config
import re
import os
from flask_login import login_user, LoginManager, UserMixin, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt

app = Flask(__name__)
# Need to set secret key and session type for session variables to work
app.secret_key = b'\xdc\xa6\x9d\xb2\xf8\xa7\xc3\xaa5\\\x9b\xc6'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Trouble installing pyodbc on azure app service container.  Follow this: https://stackoverflow.com/questions/64640016/how-to-access-odbc-driver-on-azure-app-service
# Seems like pyodbc depends on unixodbc, which may not be installed on the container instance that Azure uses.




#Locally, reading from .env file
params = urllib.parse.quote_plus(config.params)
engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)

class User(UserMixin):
    def __init__(self, id, password, active=True):
        self.id = id
        self.password = password
        self.active = active
    def __repr__(self):
        return f"User('{self.id})"
    # def get(id):
    #     return self
    def get_id(self):
        return self.id



@login_manager.user_loader
def load_user(id):
    return User(id, '')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['useremail']
        # hashed_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        password = request.form['password']
        # print(username)
        # print(hashed_password)
        user_result = engine.execute("SELECT * from advising.USER_TBL WHERE email = \'%s\'" % username)
        db_password = engine.execute(text("SELECT user_password from advising.USER_TBL WHERE email = \'%s\';" % username)).first()
        if db_password:
            db_password = str(db_password[0])
        user_object = User(username, password)
        # print('user object')
        # print(user_object)
        # if user_result:
        #     session.pop('username', None)
        if user_result and db_password and bcrypt.check_password_hash(db_password, password):
            login_user(user_object, remember=False)
            # print("Login successful!")
            flash("Logged in successfully!")
            # session['username'] = request.form['useremail']
            return redirect(url_for('hello', username=username))
        else:
            flash("Invalid username or password, please try again.")
            # print("Login unsuccessful")
    return render_template('login.html')

@app.route('/logout')
def logout():
    # session.clear()
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def hello():
    # if 'username' in session:
    return render_template('index.html')
    # else:
    return redirect(url_for('login'))

@app.route('/students')
def students():
    query = 'SELECT a.user_id, a.first_name, a.last_name, b.role_name from advising.USER_TBL a JOIN advising.ROLE_TBL b ON a.role_id = b.role_id WHERE b.role_name = \'Student\';'
    result = engine.execute(query).fetchall()
    return render_template('students.html', data=result)

@app.route('/roles')
@login_required
def roles():
    # if 'username' in session:
    result = engine.execute('SELECT * FROM advising.ROLE_TBL WHERE date_deleted IS NULL;').fetchall()
    return render_template('roles.html', data=result)
    # else:
    return redirect(url_for('login'))

@app.route('/users')
@login_required
def users():
    # if 'username' in session:
    result = engine.execute('SELECT a.user_id, a.first_name, a.last_name, a.email, b.role_name FROM advising.USER_TBL a FULL JOIN advising.ROLE_TBL b ON b.role_id = a.role_id WHERE a.date_deleted IS NULL;').fetchall()
    return render_template('users.html', data=result)
    # else:
    return redirect(url_for('login'))

@app.route('/adduser', methods = ['POST', 'GET'])
@login_required
def render():
    rolequery = 'SELECT * FROM advising.ROLE_TBL'
    roleresult = engine.execute(rolequery).fetchall()
    programquery = 'SELECT program_name FROM advising.PROGRAM_TBL;'
    program_result = engine.execute(programquery).fetchall()
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        role_name = request.form['roletype']
        program_name = request.form['program']
        # print('roletype: '+role_name)
        role_id_result= engine.execute('SELECT role_id FROM advising.ROLE_TBL WHERE role_name = \'%s\'' % (role_name))
        id = str([row[0] for row in role_id_result])
        id = re.sub(r'^\W*', '', id)
        id = re.sub(r'\W*$', '', id)
        query = 'INSERT INTO advising.USER_TBL (first_name, last_name, email, role_id) VALUES (\'%s\', \'%s\', \'%s\', \'%s\');' % (fname, lname, email, id)
        engine.execute(query)
        get_program_id_query = 'SELECT program_id FROM advising.PROGRAM_TBL WHERE program_name = \'%s\';' % (program_name)
        program_id_result = engine.execute(get_program_id_query).fetchall()
        program_id = program_id_result [0][0]
        #Get the newly created user's id, so that the id and the program id can be added to the link table
        get_new_user_id_query = 'SELECT user_id FROM advising.USER_TBL WHERE first_name = \'%s\' AND last_name = \'%s\';' % (fname, lname)
        user_id_result = engine.execute(get_new_user_id_query).fetchall()
        user_id = user_id_result [0][0]
        link_tbl_query = 'INSERT INTO advising.USER_PROGRAM_LNK (user_id, program_id) VALUES (\'%s\', \'%s\');' % (user_id, program_id)
        engine.execute(link_tbl_query)
        flash(f'User added successfully!')
        return redirect(url_for('users'))
    return render_template('adduser.html', data=roleresult, programs=program_result)

@app.route('/addrole', methods = ['POST', 'GET'])
@login_required
def addrole():
    if request.method == 'POST':
        rname = request.form['rname']
        query = 'INSERT INTO advising.ROLE_TBL (role_name) VALUES (\'%s\');' % (rname)
        engine.execute(query)
        # print(fname)
        print(query)
        return redirect(url_for('roles'))
    return render_template('addrole.html')

@app.route('/deluser/<string:id>', methods = ['POST', 'GET'])
@login_required
def deluser(id):
    # print('deluser')
    sql = 'UPDATE advising.USER_TBL SET date_deleted = CURRENT_TIMESTAMP WHERE user_id = \'%s\';' %(id)
    engine.execute(sql)
    # print (sql)
    return redirect(url_for('users'))

@app.route('/edituser/<string:id>', methods = ['POST', 'GET'])
@login_required
def edituser(id):
    sql = 'SELECT a.user_id, a.first_name, a.last_name, a.email, b.role_name FROM advising.USER_TBL a JOIN advising.ROLE_TBL b on a.role_id = b.role_id WHERE user_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    result2 = engine.execute('SELECT * FROM advising.ROLE_TBL;').fetchall()
    print(result)
    return render_template('edituser.html', data=result, data2=result2)

@app.route('/delrole/<string:id>', methods = ['POST', 'GET'])
@login_required
def delrole(id):
    # print('deluser')
    sql = 'UPDATE advising.ROLE_TBL SET date_deleted = CURRENT_TIMESTAMP WHERE role_id = \'%s\';' %(id)
    engine.execute(sql)
    # print (sql)
    return redirect(url_for('roles'))

@app.route('/editrole/<string:id>', methods = ['POST', 'GET'])
@login_required
def editrole(id):
    sql = 'SELECT * FROM advising.ROLE_TBL WHERE role_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    print(result)
    return render_template('editrole.html', data=result)

@app.route('/commitupdate/<string:id>', methods=['GET', 'POST'])
@login_required
def commitupdate(id):
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        role_name = request.form['roletype']
        # print(role_name)
        find_role_query = 'SELECT role_id from advising.ROLE_TBL WHERE role_name = \'%s\'' %(role_name)
        role_id_result = engine.execute(find_role_query).fetchall()
        # fetchall() method returns a list of lists, so need to index in to find the role id to update
        raw_id = role_id_result[0][0]
        # print(raw_id)
        query = 'UPDATE advising.USER_TBL SET first_name = \'%s\', last_name = \'%s\', email = \'%s\', role_id = \'%s\' WHERE user_id = \'%s\';' % (fname, lname, email, raw_id, id)
        # print(query)
        engine.execute(query)
        return redirect(url_for('users'))


@app.route('/commitroleupdate/<string:id>', methods=['GET', 'POST'])
@login_required
def commitroleupdate(id):
    if request.method == 'POST':
        rname = request.form['rname']
        query = 'UPDATE advising.ROLE_TBL SET role_name = \'%s\' WHERE role_id = \'%s\';' % (rname, id)
        # print(query)
        engine.execute(query)
        return redirect(url_for('roles'))


@app.route('/courses')
@login_required
def courses():
    sql = 'SELECT * from advising.COURSE_TBL WHERE date_deleted IS NULL;'
    result = engine.execute(sql).fetchall()
    return render_template('courses.html', data = result)


@app.route('/addcourse', methods = ['POST', 'GET'])
@login_required
def addcourse():
    if request.method == 'POST':
        course_code = request.form['coursecode']
        course_desc = request.form['coursedesc']
        program_name = request.form['programname']
        required = 'required' in request.form
        if required == True:
            required = 1
            print(required)
        elif required == False:
            required = 0
            print(required)
        instruction_type = request.form['instructiontype']
        category = request.form['category']
        subcategory = request.form['subcategory']
        print(required)
        #  Program id, term id, prerequisites not set up here yet because they are not elsewhere in the app
        query = 'INSERT INTO advising.COURSE_TBL (course_code, course_description, required, instruction_type, category, sub_category) VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\');' % (course_code, course_desc, required, instruction_type, category,subcategory)
        engine.execute(query)
        # print(fname)
        print(query)
        return redirect(url_for('courses'))
    return render_template('addcourse.html')    

@app.route('/viewcourse/<string:id>')
@login_required
def viewcourse(id):
    sql = 'SELECT course_id, course_code, course_description, required, instruction_type, category, sub_category FROM advising.COURSE_TBL WHERE course_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    # print(result)
    return render_template('viewcourse.html', data = result)


@app.route('/delcourse/<string:id>', methods = ['POST', 'GET'])
@login_required
def delcourse(id):
    # print('deluser')
    sql = 'UPDATE advising.COURSE_TBL SET date_deleted = CURRENT_TIMESTAMP WHERE course_id = \'%s\';' %(id)
    engine.execute(sql)
    # print (sql)
    return redirect(url_for('courses'))

@app.route('/editcourse/<string:id>')
@login_required
def editcourse(id):
    sql = 'SELECT course_id, course_code, course_description, required, instruction_type, category, sub_category FROM advising.COURSE_TBL WHERE course_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    # print(result)
    # Having a difficult time getting box to check on 'true' value in update form
    return render_template('editcourse.html', data=result)




@app.route('/commitcourseupdate/<string:id>', methods=['GET', 'POST'])
@login_required
def commitcourseupdate(id):
    if request.method == 'POST':
        course_code = request.form['coursecode']
        course_desc = request.form['coursedesc']
        # program_name = request.form['programname']
        required = 'required' in request.form
        if required == True:
            required = 1
            print(required)
        elif required == False:
            required = 0
            print(required)
        instruction_type = request.form['instructiontype']
        category = request.form['category']
        subcategory = request.form['subcategory']
        query = 'UPDATE advising.COURSE_TBL SET course_code = \'%s\', course_description = \'%s\', required = \'%s\', instruction_type = \'%s\', category = \'%s\', sub_category = \'%s\' WHERE course_id = \'%s\';' % (course_code,course_desc,required,instruction_type,category,subcategory, id)
        # print(query)
        engine.execute(query)
        return redirect(url_for('courses'))    



@app.route('/programs')
@login_required
def programs():
    sql = "SELECT * FROM advising.PROGRAM_TBL;"
    result = engine.execute(sql).fetchall()
    return render_template('programs.html', data=result)



@app.route('/addprogram', methods=['GET', 'POST'])
@login_required
def addprogram():
    if request.method == 'POST':
        code = request.form['programcode']
        name = request.form['programname']
        desc = request.form['programdesc']
        credits = request.form['credits']
        sql = "INSERT INTO advising.PROGRAM_TBL (program_code, program_name, program_description, program_credits) VALUES (\'%s\', \'%s\', \'%s\', \'%s\')" % (code, name, desc, credits)
        engine.execute(sql)
        return redirect(url_for('programs'))
    return render_template('addprogram.html')

@app.route('/delprogram/<string:id>')
@login_required
def delprogram(id):
    sql = "DELETE FROM advising.PROGRAM_TBL WHERE program_id = \'%s\'" % (id)
    engine.execute(sql)
    return redirect(url_for('programs'))

@app.route('/editprogram/<string:id>', methods = ['GET', 'POST'])
@login_required
def editprogram(id):
    sql = "SELECT * FROM advising.PROGRAM_TBL WHERE program_id = \'%s\'" % (id)
    result = engine.execute(sql).fetchall()
    return render_template('editprogram.html', data=result)

@app.route('/commitprogramupdate/<string:id>', methods=['GET','POST'])
@login_required
def commitprogramupdate(id):
    if request.method == 'POST':
        code = request.form['programcode']
        name = request.form['programname']
        desc = request.form['programdesc']
        credits = request.form['credits']
        sql = "UPDATE advising.PROGRAM_TBL SET program_code = \'%s\', program_name = \'%s\', program_description = \'%s\', program_credits = \'%s\' WHERE program_id = \'%s\';" % (code, name, desc, credits, id)
        engine.execute(sql)
        return redirect(url_for('programs'))


@app.route('/classes')
@login_required
def classes():
    sql = "SELECT * FROM advising.CLASS_TBL;"
    result = engine.execute(sql).fetchall()
    return render_template('classes.html', data=result)

@app.route('/addclass', methods = ['GET', 'POST'])
@login_required
def addclass():
    courses_query = "SELECT course_code FROM advising.COURSE_TBL;"
    course_result = engine.execute(courses_query).fetchall()
    term_query = "SELECT season FROM advising.TERM_TBL;"
    term_result = engine.execute(term_query).fetchall()
    if request.method == 'POST':
        course = request.form['courseselect']
        term = request.form['termselect']
        start_date = request.form['startdate']
        end_date = request.form['enddate']
        find_course_id_query = "SELECT course_id FROM advising.COURSE_TBL WHERE course_code = \'%s\' AND date_deleted IS NULL;" % (course)
        course_id_result = engine.execute(find_course_id_query).fetchall()[0][0]
        find_term_id_query = "SELECT term_id FROM advising.TERM_TBL WHERE season = \'%s\' AND date_deleted IS NULL;"
        term_id_result = engine.execute(find_course_id_query).fetchall()[0][0]
        # print(course_id_result)
        sql = "INSERT INTO advising.CLASS_TBL (course_id, term_id, start_date, end_date) VALUES (\'%s\', \'%s\', \'%s\', \'%s\');" % (course_id_result, term_id_result, start_date, end_date)
        engine.execute(sql)
        print(start_date)
        return redirect(url_for('classes'))
    return render_template('addclass.html', courses=course_result, terms=term_result)

if __name__ == "__main__":
    app.run(debug=True)


    #test333