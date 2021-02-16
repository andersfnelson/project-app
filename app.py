from flask import Flask, render_template
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
    result = engine.execute('SELECT * FROM advising.USER_TBL;').fetchall()
    print(result)
    return render_template('index.html')

@app.route('/users')
def users():
    result = engine.execute('SELECT * FROM advising.USER_TBL;').fetchall()
    return render_template('users.html', data=result)


if __name__ == "__main__":
    app.run(debug=True)