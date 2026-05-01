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