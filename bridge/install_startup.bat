@echo off
rem Kopruyu Windows acilisina ekler ve hemen baslatir.
set "DIR=%~dp0"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Startup')+'\TS3 Bot DJ Kopru.lnk'); $s.TargetPath='wscript.exe'; $s.Arguments='\"%DIR%start_bridge.vbs\"'; $s.WorkingDirectory='%DIR%'; $s.Save()"
wscript.exe "%DIR%start_bridge.vbs"
echo Kopru baslatildi ve acilisa eklendi: http://127.0.0.1:8765/status
pause
