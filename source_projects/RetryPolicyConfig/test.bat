@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call build.bat
if errorlevel 1 (
  echo [test.bat] fragment build FAILED
  exit /b 1
)

if not exist "tests\build" mkdir "tests\build"
dir /s /b "tests\*.java" > ".testfilelist.txt"
javac -encoding UTF-8 -cp "build;deps\lib\*;tests\lib\*" -d "tests\build" "@.testfilelist.txt"
if errorlevel 1 (
  echo [test.bat] test compile FAILED
  exit /b 1
)

set "TESTPREFIX=%~dp0tests\"
set "CLASSES="
for /r "tests" %%F in (*Test.java) do call :addclass "%%F"
if not defined CLASSES (
  echo [test.bat] no test classes found under tests\
  exit /b 1
)

java -cp "tests\build;build;deps\lib\*;tests\lib\*" org.junit.runner.JUnitCore %CLASSES%
set "RC=%errorlevel%"
del /q ".testfilelist.txt" 2>nul
exit /b %RC%

:addclass
set "F=%~1"
set "F=!F:%TESTPREFIX%=!"
set "F=!F:.java=!"
set "F=!F:\=.!"
set "CLASSES=!CLASSES! !F!"
exit /b 0
