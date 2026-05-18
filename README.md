To run the app locally (updated 27/APR/2026)

1. Pull the latest branch first from Github
#Github main branch is updated. Please see.
2. Make sure you are in the project root folder to run the app
#cd Capstone-Project-B (depends on your root folder location on your device)
3. Run the app with Doceker. 
#Use 'docker compose up --build'
4. Open the app in your browser
#Use 'http://localhost:3000/'
5. There is also a temporary DB test route, but not working for some reason (I already email Rod about db denying extrenal access)
#Use 'http://localhost:3000/db-test'

At the moment, the Flask app itself runs in Docker. 
DB has a bit of problem. VPS is responding when ping, but direct access to the db extrenally seems blocked. Emailed Rod, so this will be resolved soon. Better focus on UI development for now.

__init__.py: Create Flask app
routes.py: define URL pages
db.py: MariaDB connection functions
templates/ : HTML files
static/ : CSS, IMAGES
run.py: Starting point of running the app
.env: private setting/info for db,etc

Please do not modify the files related to MariaDB (mySQL... / phpMyAdminSQL / PCT / etc)

Deployment Process & Some useful commands:
1. Login with SSH account in Powershell
2. Confirmed the server prevents external access - sudo grep -R "bind-address" /etc/MySQL/ /etc/my.cnf* 2>/dev/null
3. Backup the current setting file - sudo cp /etc/mysql/mariadb.conf.d/50-server.cnf /etc/mysql/mariadb.conf.d/50-server.cnf.bak
4. sudo nano /etc/MySQL/MariaDB.conf.d/50-server.cnf
5. look up for bind-address line in the file
6. changed address from 127.0.0.1 to 0.0.0.0
7. restart MariaDB - sudo systemctl restart MariaDB
8. confirm the db is active - sudo systemctl status MariaDB
9. ufw does not work. Need to find out what firewall server has
10. confirmed the serves has iptables
11. add my public ip to the server - sudo iptables -I INPUT -p tcp -s 115.70.99.61 --dport 3306 -j ACCEPT
12. test connection in Powershell - Test-NetConnection vps.biogeoda.au -Port 3306
13. access MariaDB in Powershell MariaDB -h vps.biogeoda.au -P 3306 -u flora-admin_flora-admin -p
14. check if tables can be seen USE `flora-admin_Project.ID.10`;
SHOW TABLES;
15.exit
16. confirmed connection in Flask app

adminuser
PARTNERS_realizes0beneath
sudo iptables -S INPUT | grep 3306 -> displays all allowed IP addresses for port 3306

1. SSH Access (Windows Powershell)
ssh adminuser@vps.biogeoda.au

2. confirm server folder structure
ls /home
ls /home/flora-admin/web
cd /home/flora-admin/web/flora.biogeoda.au/private
pwd

3. create deployment folder
sudo mkdir -p /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B

4. folder authority confirm
ls -ld /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B

5. folder owner change
sudo chown -R adminuser:adminuser /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B
sudo chown -R flora-admin:flora-admin /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B

6. Python venv install
sudo apt update
sudo apt install python3.12-venv -y

7. move to app folder
cd /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B

8. virtual environment setu p
python3 -m venv venv

9. python package install
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

10. numpy / pandas compatilibility issue
venv/bin/pip uninstall -y numpy pandas
venv/bin/pip install "numpy==1.26.4" "pandas==2.2.2" openpyxl
venv/bin/python -c "import numpy; import pandas; print(numpy.__version__, pandas.__version__)"

11. .env for the server
nano .env (/home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B/.env)

FLASK_ENV=production
SECRET_KEY=change-this

DB_HOST=localhost
DB_PORT=3306
DB_USER=flora-admin_flora-admin
DB_PASSWORD=your_db_password
DB_NAME=flora-admin_Project.ID.10

12. port status 
sudo ss -tulpn | grep ':8010'

13. Gunicorn test
venv/bin/gunicorn --bind 127.0.0.1:8010 run:app
Ctrl + C

14. gunicron daemon
venv/bin/gunicorn --bind 127.0.0.1:8010 --daemon run:app
ps aux | grep gunicorn

15. internal flask test
curl http://127.0.0.1:8010/
curl http://127.0.0.1:8010/home
curl http://127.0.0.1:8010/login
curl http://127.0.0.1:8010/db-test

16. apache proxy activate
sudo a2enmod proxy
sudo a2enmod proxy_http

17. apache conf confirm
ls /etc/apache2/conf.d/domains/
ls /home/flora-admin/conf/web/flora.biogeoda.au/

18. apache backup
sudo cp /home/flora-admin/conf/web/flora.biogeoda.au/apache2.conf /home/flora-admin/conf/web/flora.biogeoda.au/apache2.conf.bak
sudo cp /home/flora-admin/conf/web/flora.biogeoda.au/apache2.ssl.conf /home/flora-admin/conf/web/flora.biogeoda.au/apache2.ssl.conf.bak
sudo cp /etc/apache2/conf.d/domains/flora.biogeoda.au.conf /etc/apache2/conf.d/domains/flora.biogeoda.au.conf.bak
sudo cp /etc/apache2/conf.d/domains/flora.biogeoda.au.ssl.conf /etc/apache2/conf.d/domains/flora.biogeoda.au.ssl.conf.bak

19. apache conf change
sudo nano /home/flora-admin/conf/web/flora.biogeoda.au/apache2.conf
sudo nano /home/flora-admin/conf/web/flora.biogeoda.au/apache2.ssl.conf

add
ProxyPass / http://127.0.0.1:8010/
ProxyPassReverse / http://127.0.0.1:8010/

20. confirm conf
sudo apachectl configtest

21. restart apache
sudo systemctl restart apache2

22. public URL test
curl https://flora.biogeoda.au/db-test
curl https://flora.biogeoda.au/home
curl https://flora.biogeoda.au/login

23. browser test
https://flora.biogeoda.au/
https://flora.biogeoda.au/login
https://flora.biogeoda.au/home
https://flora.biogeoda.au/db-test

Gunicorn restart process (after update)
1. file owner change back and forth
sudo chown -R flora-admin:flora-admin /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B

2. gunicorn restart
cd /home/flora-admin/web/flora.biogeoda.au/private/Capstone-Project-B
sudo fuser -k 8010/tcp
venv/bin/gunicorn --bind 127.0.0.1:8010 --daemon run:app