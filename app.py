import os
from datetime import datetime
from random import randint
from flask import Flask, render_template, redirect, url_for, request, abort, session
from flask_sqlalchemy import SQLAlchemy

#
# Setup
#

class JinjaReloadingFlask(Flask):
    """A workaround for a bug in Flask 0.11.1 where templates do not reload on
    save if you have custom Jinja filters.

    https://github.com/pallets/flask/pull/1910#issuecomment-228988778
    """

    def create_jinja_environment(self):
        self.config['TEMPLATES_AUTO_RELOAD'] = True
        return Flask.create_jinja_environment(self)

app = JinjaReloadingFlask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'devTestKey')
db = SQLAlchemy(app)

#
# Models
#

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    why = db.Column(db.String, nullable=False)
    regret = db.Column(db.String)
    upvotes = db.Column(db.Integer, nullable=False, default=0)
    created = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

#
# Filters
#

@app.template_filter('date')
def date_filter(value):
    return value.strftime('%b %d, %Y')

#
# Routes
#

@app.route('/')
def index():
    entries = Entry.query.order_by(Entry.created.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/sort-by-upvotes')
def index_by_upvotes():
    entries = Entry.query.order_by(Entry.upvotes.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/add')
def add():
    return render_template('add.html')

@app.route('/add', methods=['POST'])
def add_post():
    why = request.form.get('why', None)
    regret = request.form.get('regret', None)

    if why:
        why = why.strip()

    if regret:
        regret = regret.strip()

    if why and len(why) > 0:
        entry = Entry()
        entry.why = why
        entry.regret = regret
        db.session.add(entry)
        db.session.commit()

    return redirect(url_for('index'))

@app.route('/upvote/<int:entry_id>')
def upvote_entry(entry_id):
    if str(entry_id) in session:
        return abort(409)

    session[str(entry_id)] = True

    entry = Entry.query.get(entry_id)
    entry.upvotes += 1
    db.session.commit()

    return 'success'

@app.route('/<int:entry_id>')
def view_entry_id(entry_id):
    entry = Entry.query.get(entry_id)
    return render_template('index.html', entries=[entry])

#
# Run locally
#

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
