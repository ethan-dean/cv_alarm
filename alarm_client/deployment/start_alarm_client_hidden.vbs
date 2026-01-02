' CV Alarm Client - Hidden Startup Script for Windows
' This VBScript runs the alarm client without showing a console window
' Useful for running as a scheduled task at startup

On Error Resume Next

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Change the path below to match your installation
' Example: "C:\Users\YourName\cv_alarm\alarm_client"
installPath = "C:\Users\YourName\cv_alarm\alarm_client"

' Build the command
pythonExe = installPath & "\venv\Scripts\pythonw.exe"
mainScript = installPath & "\main.py"
logFile = installPath & "\vbscript_startup.log"
errorLog = installPath & "\logs\alarm_client_error.log"

' Log startup attempt
Set objLog = objFSO.OpenTextFile(logFile, 8, True)
objLog.WriteLine Now & " - Starting alarm client"
objLog.WriteLine "Python: " & pythonExe
objLog.WriteLine "Script: " & mainScript

' Check if files exist
If Not objFSO.FileExists(pythonExe) Then
    objLog.WriteLine "ERROR: Python executable not found at: " & pythonExe
    objLog.Close
    WScript.Quit 1
End If

If Not objFSO.FileExists(mainScript) Then
    objLog.WriteLine "ERROR: main.py not found at: " & mainScript
    objLog.Close
    WScript.Quit 1
End If

' Ensure logs directory exists
If Not objFSO.FolderExists(installPath & "\logs") Then
    objFSO.CreateFolder(installPath & "\logs")
End If

' Build command with explicit working directory change
' Use cmd.exe to change directory first, then run Python
command = "cmd.exe /c cd /d """ & installPath & """ && """ & pythonExe & """ main.py 2>> """ & errorLog & """"

objLog.WriteLine "Command: " & command
objShell.Run command, 0, False

If Err.Number <> 0 Then
    objLog.WriteLine "ERROR: " & Err.Description
    objLog.Close
    WScript.Quit 1
Else
    objLog.WriteLine "Successfully launched alarm client"
    objLog.Close
End If

Set objShell = Nothing
Set objFSO = Nothing
