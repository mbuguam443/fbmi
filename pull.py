import os, subprocess
os.chdir('/home/wlsihszp/fbmi')

result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
print("Latest commits on server:")
print(result.stdout)
print("---")
result2 = subprocess.run(['git', 'status'], capture_output=True, text=True)
print(result2.stdout)
