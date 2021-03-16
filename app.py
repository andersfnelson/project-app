from flask import Flask, render_template, request, redirect, url_for
# from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import urllib
import config
import re
import os

app = Flask(__name__)
app.secret_key = 'secret key'

# Trouble installing pyodbc on azure app service container.  Follow this: https://stackoverflow.com/questions/64640016/how-to-access-odbc-driver-on-azure-app-service
# Seems like pyodbc depends on unixodbc, which may not be installed on the container instance that Azure uses.

######
# FOR MAKING IT WORK ON AZURE
# params="DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:dunwoody-soe-dev.database.windows.net;PORT=1433;Database=soe-dev-db;Uid=dunwoody-dev;Pwd=engineering1!;Encrypt=no;TrustServerCertificate=no;Connection Timeout=30;"
# params = urllib.parse.quote_plus(params)


#Locally, reading from .env file
params = urllib.parse.quote_plus(config.params)
engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)



@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/roles')
def roles():
    result = engine.execute('SELECT * FROM advising.ROLE_TBL;').fetchall()
    return render_template('roles.html', data=result)

@app.route('/users')
def users():
    result = engine.execute('SELECT a.user_id, a.first_name, a.last_name, a.email, b.role_name FROM advising.USER_TBL a JOIN advising.ROLE_TBL b ON b.role_id = a.role_id;').fetchall()
    return render_template('users.html', data=result)

@app.route('/adduser', methods = ['POST', 'GET'])
def render():
    rolequery = 'SELECT * FROM advising.ROLE_TBL'
    roleresult = engine.execute(rolequery).fetchall()
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        role_name = request.form['roletype']
        # print('roletype: '+role_name)
        role_id_result= engine.execute('SELECT role_id FROM advising.ROLE_TBL WHERE role_name = \'%s\'' % (role_name))
        id = str([row[0] for row in role_id_result])
        id = re.sub(r'^\W*', '', id)
        id = re.sub(r'\W*$', '', id)
        print(id)
        query = 'INSERT INTO advising.USER_TBL (first_name, last_name, email, role_id) VALUES (\'%s\', \'%s\', \'%s\', \'%s\');' % (fname, lname, email, id)
        engine.execute(query)
        # print(fname)
        print(query)
        return redirect(url_for('users'))
    return render_template('adduser.html', data=roleresult)

@app.route('/addrole', methods = ['POST', 'GET'])
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
def deluser(id):
    # print('deluser')
    sql = 'DELETE FROM advising.USER_TBL WHERE user_id = \'%s\';' %(id)
    engine.execute(sql)
    # print (sql)
    return redirect(url_for('users'))

@app.route('/edituser/<string:id>', methods = ['POST', 'GET'])
def edituser(id):
    sql = 'SELECT a.user_id, a.first_name, a.last_name, a.email, b.role_name FROM advising.USER_TBL a JOIN advising.ROLE_TBL b on a.role_id = b.role_id WHERE user_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    result2 = engine.execute('SELECT * FROM advising.ROLE_TBL;').fetchall()
    print(result)
    return render_template('edituser.html', data=result, data2=result2)

@app.route('/delrole/<string:id>', methods = ['POST', 'GET'])
def delrole(id):
    # print('deluser')
    sql = 'DELETE FROM advising.ROLE_TBL WHERE role_id = \'%s\';' %(id)
    engine.execute(sql)
    # print (sql)
    return redirect(url_for('roles'))

@app.route('/editrole/<string:id>', methods = ['POST', 'GET'])
def editrole(id):
    sql = 'SELECT * FROM advising.ROLE_TBL WHERE role_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    print(result)
    return render_template('editrole.html', data=result)

@app.route('/commitupdate/<string:id>', methods=['GET', 'POST'])
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
def commitroleupdate(id):
    if request.method == 'POST':
        rname = request.form['rname']
        query = 'UPDATE advising.ROLE_TBL SET role_name = \'%s\' WHERE role_id = \'%s\';' % (rname, id)
        # print(query)
        engine.execute(query)
        return redirect(url_for('roles'))


@app.route('/courses')
def courses():
    sql = 'SELECT * from advising.COURSE_TBL'
    result = engine.execute(sql).fetchall()
    return render_template('courses.html', data = result)


@app.route('/addcourse', methods = ['POST', 'GET'])
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
def viewcourse(id):
    sql = 'SELECT * FROM advising.COURSE_TBL WHERE course_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    # print(result)
    return render_template('viewcourse.html', data = result)


@app.route('/delcourse/<string:id>', methods = ['POST', 'GET'])
def delcourse(id):
    # print('deluser')
    sql = 'DELETE FROM advising.COURSE_TBL WHERE course_id = \'%s\';' %(id)
    engine.execute(sql)
    # print (sql)
    return redirect(url_for('courses'))

@app.route('/editcourse/<string:id>')
def editcourse(id):
    sql = 'SELECT * FROM advising.COURSE_TBL WHERE course_id = \'%s\';' % (id)
    result = engine.execute(sql).fetchall()
    # print(result)
    # Having a difficult time getting box to check on 'true' value in update form
    return render_template('editcourse.html', data=result)




@app.route('/commitcourseupdate/<string:id>', methods=['GET', 'POST'])
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
def programs():
    sql = "SELECT * FROM advising.PROGRAM_TBL;"
    result = engine.execute(sql).fetchall()
    return render_template('programs.html', data=result)



@app.route('/addprogram', methods=['GET', 'POST'])
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
def delprogram(id):
    sql = "DELETE FROM advising.PROGRAM_TBL WHERE program_id = \'%s\'" % (id)
    engine.execute(sql)
    return redirect(url_for('programs'))

@app.route('/editprogram/<string:id>', methods = ['GET', 'POST'])
def editprogram(id):
    sql = "SELECT * FROM advising.PROGRAM_TBL WHERE program_id = \'%s\'" % (id)
    result = engine.execute(sql).fetchall()
    return render_template('editprogram.html', data=result)

@app.route('/commitprogramupdate/<string:id>', methods=['GET','POST'])
def commitprogramupdate(id):
    if request.method == 'POST':
        code = request.form['programcode']
        name = request.form['programname']
        desc = request.form['programdesc']
        credits = request.form['credits']
        sql = "UPDATE advising.PROGRAM_TBL SET program_code = \'%s\', program_name = \'%s\', program_description = \'%s\', program_credits = \'%s\' WHERE program_id = \'%s\';" % (code, name, desc, credits, id)
        engine.execute(sql)
        return redirect(url_for('programs'))
if __name__ == "__main__":
    app.run(debug=True)


    #test333