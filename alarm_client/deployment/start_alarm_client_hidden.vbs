' CV Alarm Client - Hidden Startup Script for Windows
' This VBScript runs the alarm client without showing a console window
' Useful for running as a scheduled task at startup

Set objShell = CreateObject("WScript.Shell")

' Change the path below to match your installation
' Example: "C:\Users\YourName\cv_alarm\alarm_client"
installPath = "C:\Users\YourName\cv_alarm\alarm_client"

' Build the command
pythonExe = installPath & "\venv\Scripts\python.exe"
mainScript = installPath & "\main.py"

' Run hidden (0 = hide window)
objShell.Run """" & pythonExe & """ """ & mainScript & """", 0, False

Set objShell = Nothing
