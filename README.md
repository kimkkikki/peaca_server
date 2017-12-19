# Dependencies install
```bash
# PostgrSQL, PostGIS
sudo apt install postgresql, postgis

# Python 3
sudo api install python3-dev, python3-pip, build-essential, python3-psycopg2

# Bower
sudo apt install nodejs nodejs-legacy npm
sudo npm install -g bower

# PIP
sudo pip3 install -r requirements.txt
```

# SSL Install (certbot)
```bash
$ sudo apt-get update
$ sudo apt-get install software-properties-common
$ sudo add-apt-repository ppa:certbot/certbot
$ sudo apt-get update
$ sudo apt-get install python-certbot-nginx 

$ sudo certbot --nginx
```

# Distribution
```bash
git pull
source bin/activate
python manage.py makemigations
python manage.py migrate
python manage.py bower install
python manage.py collectstatic
sudo systemctl restart gunicorn
```
