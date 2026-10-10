@echo off
setlocal
cd /d "%~dp0"
if not exist build mkdir build
dir /s /b deps\*.java > .filelist.txt
dir /b *.java >> .filelist.txt
javac -encoding UTF-8 -cp "deps\lib\*" -processorpath "deps\lib\lombok-1.18.43.jar" -d build @.filelist.txt
if errorlevel 1 exit /b 1
echo BUILD OK
