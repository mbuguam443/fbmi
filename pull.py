import os
os.chdir('/home/wlsihszp/fbmi')
os.system("git fetch origin")
os.system("git reset --hard origin/main")
print("Updated to latest from GitHub.")
