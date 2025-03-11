@echo off
setlocal enabledelayedexpansion

REM Set path to embedded Python
set PYTHON_PATH=.\python-3.13.2-embed-amd64\python.exe

echo Using embedded Python from %PYTHON_PATH%
echo Setting up environment...

REM Set up Python path to include the current directory and site-packages
set PYTHONPATH=%CD%;%CD%\python-3.13.2-embed-amd64\Lib\site-packages

REM Create python3._pth file to ensure proper module loading
echo python313.zip> .\python-3.13.2-embed-amd64\python313._pth
echo .>> .\python-3.13.2-embed-amd64\python313._pth
echo Lib\site-packages>> .\python-3.13.2-embed-amd64\python313._pth
echo %CD%>> .\python-3.13.2-embed-amd64\python313._pth
echo import site>> .\python-3.13.2-embed-amd64\python313._pth

echo Installing dependencies...
%PYTHON_PATH% -m pip install -r requirements.txt

echo Making migrations...
%PYTHON_PATH% manage.py makemigrations

echo Applying migrations...
%PYTHON_PATH% manage.py migrate

echo Loading mock data...
%PYTHON_PATH% manage.py load_mock

echo Collecting static files...
%PYTHON_PATH% manage.py collectstatic --noinput

echo Starting development server...
start /B %PYTHON_PATH% manage.py runserver

REM Wait a bit for the server to start
timeout /t 2 /nobreak > NUL

REM Open the browser
start http://127.0.0.1:8000/

echo Server is running. Press Ctrl+C to stop.
