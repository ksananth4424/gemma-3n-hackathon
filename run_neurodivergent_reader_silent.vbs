' ADHD Reader - Enhanced Silent Launcher for Context Menu  
' Handles video/audio files with proper processing while staying silent
Dim objShell, objFSO, command, projectPath, filePath, fileExt
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
projectPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Check if a file argument was provided
If WScript.Arguments.Count > 0 Then
    filePath = WScript.Arguments(0)
    
    ' Get file extension to determine processing method
    fileExt = LCase(objFSO.GetExtensionName(filePath))
    
    ' For video/audio files, use PowerShell to run python (hidden execution)
    If fileExt = "mp4" Or fileExt = "avi" Or fileExt = "mov" Or fileExt = "mkv" Or fileExt = "wmv" Or fileExt = "flv" Or _
       fileExt = "mp3" Or fileExt = "wav" Or fileExt = "flac" Or fileExt = "aac" Or fileExt = "m4a" Or fileExt = "ogg" Or fileExt = "wma" Then
        ' Use PowerShell with hidden window for media files
        command = "powershell.exe -WindowStyle Hidden -Command ""python '" & projectPath & "src\ui\main.py' '" & filePath & "'"""
    Else
        ' Use pythonw for text/document files (faster for simple processing)
        command = "pythonw """ & projectPath & "src\ui\main.py"" """ & filePath & """"
    End If
Else
    ' No file argument - run in demo mode
    command = "pythonw """ & projectPath & "src\ui\main.py"""
End If

' Run completely hidden (0 = hidden window, False = don't wait)
objShell.Run command, 0, False
