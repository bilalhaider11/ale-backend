#!/bin/bash

echo Running app..

rococo-postgres rf  # Run forward migrations
echo Done db stuff
python3 version.py
if [ "$APP_ENV" == "production" ] || [ "$APP_ENV" == "test" ]
then
    waitress-serve --port=5000 --call 'main:create_app'
else
    python3 main.py
fi