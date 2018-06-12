from datetime import datetime
import time
import os
import zipfile
import re
import shutil


def backup(ffxiv_path, backup_path):
    zip_name = "FFXIV-Backup-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip"
    try:
        with zipfile.ZipFile(backup_path + "\\" + zip_name, 'w') as backup_zip:
            for folder, subfolders, files in os.walk(ffxiv_path):
                final_directory = os.path.basename(os.path.normpath(folder))
                if re.compile("FFXIV_CHR\w{16}").match(final_directory) or final_directory in ["FINAL FANTASY XIV - KOREA", "log"]:
                    for file in files:
                        backup_zip.write(os.path.join(folder, file),
                                         os.path.relpath(os.path.join(folder, file), ffxiv_path),
                                         compress_type=zipfile.ZIP_DEFLATED)
    except Exception as e:
        return False, str(e)
    else:
        return True, zip_name


def restore(backup_file, ffxiv_path):
    try:
        # Deletes all current settings file
        for dirname in os.listdir(ffxiv_path):
            if re.compile("FFXIV_CHR\w{16}").match(dirname) or dirname == "log":
                subpath = os.path.join(ffxiv_path, dirname)
                if os.path.isdir(subpath):
                    shutil.rmtree(subpath)
                else:
                    os.remove(subpath)
        # Restoration
        with zipfile.ZipFile(backup_file) as backup_zip:
            backup_zip.extractall(ffxiv_path)
            # Restoring the last modification date
            for f in backup_zip.infolist():
                fullpath = os.path.join(ffxiv_path, f.filename)
                date_time = time.mktime(f.date_time + (0, 0, -1))
                os.utime(fullpath, (date_time, date_time))
    except Exception as e:
        return False, str(e)
    else:
        return True, "Success"
