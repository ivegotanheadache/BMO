import subprocess

p1 = subprocess.Popen(["python3", "speak.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
p2 = subprocess.Popen(["python3", "face.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


for line in p1.stdout:
    print("[speak.py]", line.decode(), end="")

