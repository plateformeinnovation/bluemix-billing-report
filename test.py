import subprocess

out = subprocess.check_output('bx bss orgs-usage-summary --json', shell=True)
print out