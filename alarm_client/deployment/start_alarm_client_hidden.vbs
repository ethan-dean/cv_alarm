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
pythonExe = installPath & "\venv\Scripts\python.exe"
mainScript = installPath & "\main.py"
logFile = installPath & "\vbscript_startup.log"

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

' Change to the correct directory and run
objShell.CurrentDirectory = installPath
objShell.Run """" & pythonExe & """ """ & mainScript & """", 0, False

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
