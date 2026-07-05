@echo off
REM Build TransImageLite.exe with PyInstaller. Run from the project root.
setlocal

if not exist .venv (
    echo [build] .venv not found. Create it first with a non-Anaconda Python 3.11:
    echo   py -V:3.11 -m venv .venv
    exit /b 1
)

echo [build] installing build dependencies...
.venv\Scripts\python.exe -m pip install -r requirements-build.txt --quiet
if errorlevel 1 exit /b 1

echo [build] running PyInstaller...
.venv\Scripts\python.exe -m PyInstaller build.spec --noconfirm
if errorlevel 1 exit /b 1

echo [build] done: dist\TransImageLite.exe
endlocal
