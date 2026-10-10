@echo off
setlocal
cd /d "%~dp0"
if not exist build mkdir build
dir /s /b deps\*.java > .filelist.txt
dir /b *.java >> .filelist.txt
javac -encoding UTF-8   -d build @.filelist.txt
if errorlevel 1 (
  echo BUILD FAILED
  exit /b 1
)
echo BUILD OK