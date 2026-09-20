:: Create a bogus pending execution queue in the Component Based Servicing (CBS) hive
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\SessionsPending" /v Exclusive /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending" /v RebootPending /t REG_DWORD /d 1 /f
