# -*- coding: utf-8 -*-
"""
    git deployment server
    ~~~~~~~~

    autodeploy applications when pushed to git
"""

import os
import json
import datetime

from pprint import pprint
from os.path import basename
from netaddr import IPNetwork, IPAddress
from subprocess import Popen, PIPE, STDOUT

from flask import Flask, request, render_template, flash, jsonify
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, validators, TextAreaField, SelectField, SelectMultipleField, HiddenField, RadioField, BooleanField, FileField
from wtforms.validators import DataRequired, ValidationError, Required, Optional
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required


# Create App
app = Flask(__name__)
app.config.from_pyfile('settings.cfg', silent=False)


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
    name = db.Column(db.String(255))
    branch = db.Column(db.String(255))
    basepath = db.Column(db.String(255))
    touchpath = db.Column(db.String(255))
    scriptpath = db.Column(db.String(255))
    disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create/Edit App Form
class createEditApp(Form):
    name = TextField('Repository Name', [Required()],description="Must be exactly as it appears on GitHub or BitBucket.")
    branch = TextField('Branch Name', [Required()], description="Watch this branch for updates and pull changes.")
    basepath = TextField('Absolute Base Path', [Required()], description="Base path is the location of your application on the server. This is the root of your repository. Must be an absolute path.")
    touchpath = TextField('Touch this File Path', [Optional()], description="This file will be touched after the webhook is executed.")
    scriptpath = TextField('Execute this Bash Script Path', [Optional()], description="This bash script will be executed after all other tasks are complete.")
    disabled = BooleanField('Disable this hook?', [Optional()])


whitelist_ip_blocks = [
    '207.97.227.224/27',  # github
    '173.203.140.192/27',  # github
    '204.232.175.64/27',  # github
    '72.4.117.96/27',  # github
    '192.30.252.0/22',  # github
    '131.103.20.165',  # bitbucket
    '131.103.20.166',  # bitbucket
]


def ip_allowed(ip_address):
    for ip_block in whitelist_ip_blocks:
        if IPAddress(ip_address) in IPNetwork(ip_block):
            return True
    return False


def demote(user_uid):
    def result():
        os.setuid(user_uid)
    return result


# Create your login
@app.before_first_request
def create_user():
    db.create_all()
    user_datastore.create_user(email=app.config['ADMIN_EMAIL'], password=app.config['ADMIN_PASSWORD'])
    if not User.query.filter_by(email=app.config['ADMIN_EMAIL']).count():
        db.session.commit()


@app.route("/", methods=['POST', 'GET'])
@login_required
def index():
    apps = Application.query.all()
    return render_template('index.html', apps=apps)


@app.route("/create", methods=['POST', 'GET'])
@login_required
def create_app():
    form = createEditApp()
    if form.validate_on_submit():
        application = Application()
        form.populate_obj(application)
        if not Application.query.filter_by(name=form.name.data, branch=form.branch.data).count():
            db.session.add(application)
            db.session.commit()
            flash('Successfully created.', 'success')
        else:
            flash('That repository name & branch already exists!', 'error')
    return render_template('create-edit.html', form=form)


@app.route("/edit/<application_id>", methods=['POST', 'GET'])
@login_required
def edit_app(application_id):
    application = Application.query.get_or_404(application_id)
    form = createEditApp(obj=application)
    if form.validate_on_submit():
        form.populate_obj(application)
        db.session.commit()
        flash('Successfully updated.', 'success')
    return render_template('create-edit.html', form=form)


@app.route("/deploy", methods=['POST'])
def autodeploy():
    if ip_allowed(request.remote_addr):
        payload = json.loads(request.form['payload'])
        pprint(payload)

        if payload.get('canon_url') == 'https://bitbucket.org':
            #bitbucket style
            repo = payload['repository']
            name = repo['name']
            branch = payload['commits'][0]['branch']
        else:
            #github style
            repo = payload['repository']
            name = repo['name']
            branch = basename(payload['ref'])

        application = Application.query.filter_by(name=name, branch=branch, disabled=False).first()
        if application:
            # Overwrite all files with current Git Version
            command = '''
                cd %s
                git fetch --all
                git reset --hard origin/%s
            ''' % (application.basepath, application.branch)
            Popen(command, shell=True)

            # Run optional commands if they are set
            if application.touchpath:
                # Ex. touch /etc/uwsgi/application.ini will restart your UWSGI workers
                Popen('touch %s' % application.touchpath, shell=True)

            if application.scriptpath:
                # Run a script to wrap things up. Change permissions, send an email, whatever
                Popen('bash %s' % application.scriptpath, preexec_fn=demote(1000), shell=True)

            status = 'Post-receive hook for %s triggered.' % repo['name']
            print status
            return jsonify(status=status)
        else:
            status = 'No active application hooks found'
            print status
            return jsonify(status=status)
    else:
        status = 'Bad IP source address. Only GitHub and BitBucket IP addresses allowed. Check "whitelist_ip_blocks."'
        print status
        return jsonify(status=status)


if __name__ == "__main__":
    app.run('0.0.0.0', port=9340)
