#! /bin/sh

set -e
echo "started startscript"
sleep 3
python ./manage.py wait_for_db
echo "waited for db"
python ./manage.py migrate
echo "ran migrations"
python ./manage.py runserver 0.0.0.0:8000