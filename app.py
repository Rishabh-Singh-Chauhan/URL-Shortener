from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import string, re, pickle
import os
from sklearn.tree import DecisionTreeClassifier
import pandas as pd
import sklearn

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db_object = SQLAlchemy(app)

@app.before_request
def create_tables():
    app.before_request_funcs[None].remove(create_tables)

    db_object.create_all()

def url_generated():
    letters = string.ascii_lowercase + string.ascii_uppercase
    while True:
        random_letters = random.choices(letters, k=4)
        random_letters = "".join(random_letters)
        short_url = URLStorage.query.filter_by(short=random_letters).first()
        if not short_url:
            return random_letters

def get_company_name(url):
    pattern = r'https?://(?:www\.)?([A-Za-z_0-9.-]+)\.com'
    
    match = re.search(pattern, url)
    
    if match:
        company = match.group(1)
        if company.lower() == 'youtube':
            comp_type = 'Entertainment'
        elif company.lower() == 'geeksforgeeks' or company.lower() == 'w3schools':
            comp_type = 'Education'
        else:
            comp_type = ''
        return company, comp_type        
    else:
        return '', ''

@app.route('/', methods = ['POST', 'GET'])
def home():
    if request.method == "POST":
        url_input = request.form['url_input']
        alreadyExistedURL = URLStorage.query.filter_by(long=url_input).first()
        
        company, industry = get_company_name(url_input)
        print(company)
        prob = get_prediction(company)

        if alreadyExistedURL:
            return redirect(url_for("display_new_url", url=alreadyExistedURL.short, company = company, comp_type = industry, predict_prob = prob))
        else:
            newURL = url_generated()
            newURLGenerated = URLStorage(url_input, newURL)
            db_object.session.add(newURLGenerated)
            db_object.session.commit()

            return redirect(url_for("display_new_url", url = newURL, company = company, comp_type = industry, predict_prob = prob))
    else:
        return render_template('home.html')

def get_prediction(comp):
    file= open('K:\\My Drive\\Study\\100 CF\\URL Shortener\\models\\DecisionTree.pkl', 'rb')
    dt = pickle.load(file)
    if comp.lower() == 'youtube':
        first = False
        second = True
        third = True
    elif comp.lower() == 'w3schools':
        first = True
        second = False
        third = False
    else:
        first = False
        second = False
        third = False
    
    df = {
        'Company_W3Schools': [first],
        'Company_Youtube': [second],
        'Type_Entertainment': [third]
    }

    df = pd.DataFrame(df)
    pred = dt.predict_proba(df)

    return pred[0][1] * 100
    
@app.route('/display/<url>/<company>/<comp_type>/<predict_prob>')
def display_new_url(url, company, comp_type, predict_prob):
    return render_template('newURL.html', short_url_display=url, type = comp_type, company = company.capitalize(), pred_prob = predict_prob)

@app.route('/<newURL>')
def redirection(newURL):
    oldURL = URLStorage.query.filter_by(short=newURL).first()
    if oldURL:
        return redirect(oldURL.long)
    else:
        return f'<h1>Wrong URL</h1>'
    
class URLStorage(db_object.Model):
    id_ = db_object.Column("id_", db_object.Integer, primary_key=True)
    long = db_object.Column("long", db_object.String())
    short = db_object.Column("short", db_object.String(4))

    def __init__(self, long, short):
        self.long = long
        self.short = short

if __name__ == '__main__':
    app.run(port = 5000, debug = True)