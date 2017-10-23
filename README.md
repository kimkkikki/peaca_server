# Installation

1. Dependencies install
```bash
sudo apt install postgresql, postgis, python3-dev, python3-pip, build-essential, python3-psycopg2
sudo pip3 install -r requirements.txt
```

2. SSL Install (certbot)
```bash
$ sudo apt-get update
$ sudo apt-get install software-properties-common
$ sudo add-apt-repository ppa:certbot/certbot
$ sudo apt-get update
$ sudo apt-get install python-certbot-nginx 

$ sudo certbot --nginx
```