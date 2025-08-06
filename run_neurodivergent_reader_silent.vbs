' ADHD Reader - Enhanced Silent Launcher for Context Menu  
' Handles video/audio files with proper processing while staying silent
' Includes model creation functionality from Modelfiles
Dim objShell, objFSO, command, projectPath, filePath, fileExt
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
projectPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Function to check if Ollama models exist and create them if needed
Sub EnsureModelsExist()
    Dim checkCommand, createE2bCommand, createE4bCommand, listOutput
    
    ' Check if accessibility models exist by listing models and checking for them
    checkCommand = "ollama list"
    
    ' Create a temporary file to capture output
    Dim tempFile
    tempFile = objShell.ExpandEnvironmentStrings("%TEMP%") & "\ollama_models.txt"
    
    ' Run ollama list and capture output
    objShell.Run "cmd /c " & checkCommand & " > """ & tempFile & """", 0, True
    
    ' Read the output
    Dim file, content
    Set file = objFSO.OpenTextFile(tempFile, 1)
    content = file.ReadAll()
    file.Close()
    
    ' Clean up temp file
    objFSO.DeleteFile tempFile
    
    ' Check if our models exist
    Dim needE2b, needE4b
    needE2b = InStr(content, "accessibility-e2b") = 0
    needE4b = InStr(content, "accessibility-e4b") = 0
    
    ' Create missing models
    If needE2b Then
        createE2bCommand = "cd /d """ & projectPath & "src\models"" && ollama create accessibility-e2b:latest -f Modelfile.e2b"
        objShell.Run "cmd /c " & createE2bCommand, 0, True
    End If
    
    If needE4b Then
        createE4bCommand = "cd /d """ & projectPath & "src\models"" && ollama create accessibility-e4b:latest -f Modelfile.e4b"
        objShell.Run "cmd /c " & createE4bCommand, 0, True
    End If
End Sub

' Ensure models exist before running the application
EnsureModelsExist()

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
