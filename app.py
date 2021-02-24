from flask import Flask, render_template, request, redirect, url_for
# from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import urllib
import config

app = Flask(__name__)
app.secret_key = 'secret key'



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
    result = engine.execute('SELECT * FROM advising.USER_TBL;').fetchall()
    return render_template('users.html', data=result)

@app.route('/adduser', methods = ['POST', 'GET'])
def render():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        query = 'INSERT INTO advising.USER_TBL (first_name, last_name, email) VALUES (\'%s\', \'%s\', \'%s\');' % (fname, lname, email)
        engine.execute(query)
        # print(fname)
        print(query)
        return redirect(url_for('users'))
    return render_template('adduser.html')

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
    sql = 'SELECT * FROM advising.USER_TBL WHERE user_id = \'%s\';' %(id)
    result = engine.execute(sql).fetchall()
    print(result)
    return render_template('edituser.html', data=result)

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
        query = 'UPDATE advising.USER_TBL SET first_name = \'%s\', last_name = \'%s\', email = \'%s\' WHERE user_id = \'%s\';' % (fname, lname, email, id)
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


if __name__ == "__main__":
    app.run(debug=True)