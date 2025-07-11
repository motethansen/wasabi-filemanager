@echo off
REM Virtual environment setup script for Windows
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt 