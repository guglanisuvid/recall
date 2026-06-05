@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Building executable...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "Recall" ^
  --hidden-import win32timezone ^
  --hidden-import win32process ^
  --hidden-import win32api ^
  --hidden-import pystray._win32 ^
  main.py

echo.
echo Done. Find WindowMemory.exe in the dist\ folder.
pause
