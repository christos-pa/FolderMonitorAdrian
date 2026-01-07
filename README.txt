FolderMonitor – Quick Setup Guide
1️⃣ Files you should have

Make sure these files are together in one folder (don’t separate them):

FolderMonitor.exe

config.json

setup.bat

uninstall.bat

2️⃣ First-time setup (only once per computer)

Right-click setup.bat → Run as administrator.

A black window will appear for a few seconds.

Setup will:

Create the needed folders (inbox, backup).

Add FolderMonitor to Windows Task Scheduler to run every 15 minutes automatically.

Test-run once to make sure it works.

3️⃣ How it works

Drop any file into the inbox folder.

Every 15 minutes, FolderMonitor will:

Detect new files.

Email them to the address(es) in config.json.

Move them to the backup folder.

You can double-click FolderMonitor.exe at any time to run it immediately.

4️⃣ Changing settings

Right-click config.json → Open with Notepad.

You can edit:

"watch_folder" → folder to monitor.

"backup_folder" → where files get moved after emailing.

"to_addrs" → list of recipient emails (in quotes, separated by commas).

Save the file.

No need to reinstall — changes apply next run.

5️⃣ Uninstalling

Right-click uninstall.bat → Run as administrator.

This removes the scheduled task from Windows.

💡 Tips:

Do not move the program folder after setup. If you do, run uninstall then setup again.

Keep FolderMonitor.exe and config.json together — they work as a pair.