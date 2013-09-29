# -*- coding: utf-8 -*-
"""
    git deployment server
    ~~~~~~~~

    autodeploy applications when pushed to git
"""

import json
import datetime

from pprint import pprint

from flask import Flask, request, render_template, flash
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, validators, TextAreaField, SelectField, SelectMultipleField, HiddenField, RadioField, BooleanField, FileField
from wtforms.validators import DataRequired, ValidationError, Required, Optional
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required


# Create App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the-red-skittles-are-my-favorite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sql'
app.debug = True


#create db instance
db = SQLAlchemy(app)


# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    branch = db.Column(db.String(255))
    basepath = db.Column(db.String(255))
    touchpath = db.Column(db.String(255))
    scriptpath = db.Column(db.String(255))
    disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create first user
# user_datastore.create_user(email='nicholas.woodhams@gmail.com', password='super-secure-password')
# db.session.commit()


# Create/Edit App Form
class createEditApp(Form):
    name = TextField('Repository Name', [Required()], description="Must be exactly as it appears on GitHub or BitBucket.")
    branch = TextField('Branch Name', [Required()], description="Watch this branch for updates and pull changes.")
    basepath = TextField('Absolute Base Path', [Required()], description="Base path is the location of your application on the server. This is the root of your repository. Must be an absolute path.")
    touchpath = TextField('Touch this File Path', [Optional()], description="This file will be touched after the webhook is executed.")
    scriptpath = TextField('Execute this Bash Script Path', [Optional()], description="This bash script will be executed after all other tasks are complete.")
    disabled = BooleanField('Disable this hook?', [Optional()])


@app.route("/")
@login_required
def index():
    apps = Application.query.all()
    return render_template('index.html', apps=apps)


@app.route("/create", methods=['POST', 'GET'])
@login_required
def create_app():
    form = createEditApp()
    if form.validate_on_submit():
        app = Application()
        form.populate_obj(app)
        if not Application.query.filter_by(name=field.data).count():
            db.session.add(app)
            db.session.commit()
            flash('Successfully created.', 'success')
        else:
            flash('That repository name already exists!', 'error')
    return render_template('create-edit.html', form=form)


@app.route("/edit/<application_id>", methods=['POST', 'GET'])
@login_required
def edit_app(application_id):
    app = Application.query.get_or_404(application_id)
    form = createEditApp(obj=app)
    if form.validate_on_submit():
        form.populate_obj(app)
        db.session.commit()
        flash('Successfully updated.', 'success')
    return render_template('create-edit.html', form=form)


@app.route("/deploy", methods=['POST'])
def autodeploy():
    payload = json.loads(request.form['payload'])
    repo = payload['repository']
    pprint(repo)
    return "yay"


if __name__ == "__main__":
    app.run('0.0.0.0', port=9340)



















