Git-Post-Receive-Hook-Deploy
============================

Deploy your applications automatically after push. 

Flask Application to Manage your Post-Receive Hooks from Github or BitBucket. Automatically pull changes, and run a custom script.

GitHub and BitBucket support. 

<img border="1" src="http://cl.ly/image/1j3X3M3H2O17/Screen%20Shot%202013-09-30%20at%2012.28.21%20AM.png">

<img border="1" src="http://cl.ly/image/2D1r2n1z1b2y/Screen%20Shot%202013-09-30%20at%201.11.31%20AM.png">


##Set up locally
####Without virtual environment:

	git clone git@github.com:NickWoodhams/Git-Post-Receive-Hook-Deploy.git
	cd Git-Post-Receive-Hook-Deploy
	pip install -r requirements.txt

####With virtual environment:

	git clone git@github.com:NickWoodhams/Git-Post-Receive-Hook-Deploy.git
	cd Git-Post-Receive-Hook-Deploy
	virtualenv venv
	source venv/bin/activate
	pip install -r requirements.txt

##Create Development Database
Create a Postgres or MySQL database locally, and use your database credentials in the next step. The database tables will be created the first time the code is executed. 

##Update server.py

Update your Database settings, secret key, as well as admin login/password credentials. The admin user will be created when you first run your application


##Start the Webserver

Simply run `python app.py`

The project should be accessable at [http://localhost:9340](http://localhost:9340)

===
#Important Notes

- Tail your application log file to debug the setup. 
- Your repositories should be owned by your web worker, most likely www-data. Or you could change this to run under your UID/GID. 
