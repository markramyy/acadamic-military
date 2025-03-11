#!/bin/bash

echo "Setting up virtual environment..."
if [ ! -d "env" ]; then
    python3 -m venv env
fi

echo "Activating virtual environment..."
source env/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Making migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

echo "Loading mock data..."
python manage.py load_mock

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting development server..."
python manage.py runserver &

# Wait a bit for the server to start
sleep 2

# Open the browser
open http://127.0.0.1:8000/
