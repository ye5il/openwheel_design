@echo off
title Openwheel Design
cd /d "%~dp0"
python -m openwheel_design.gui.main_window
if errorlevel 1 pause
