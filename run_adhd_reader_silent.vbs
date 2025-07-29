' Prism Silent VBScript Launcher
' Completely hides all console windows for seamless context menu integration

Dim objShell, command, projectPath, filePath

Set objShell = CreateObject("WScript.Shell")

' Get the directory where this script is located
projectPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Check if a file argument was provided
If WScript.Arguments.Count > 0 Then
    filePath = WScript.Arguments(0)
    ' Build command with file argument
    command = "pythonw """ & projectPath & "src\ui\main.py"" """ & filePath & """"
Else
    ' No file argument - run in demo mode
    command = "pythonw """ & projectPath & "src\ui\main.py"""
End If

' Run completely hidden (0 = hidden window, False = don't wait)
objShell.Run command, 0, False
