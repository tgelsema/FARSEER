import os
import sys

with open("full_reqs.txt") as file:
    reqs = file.readlines()
    for req in reqs:
        os.system("pip install " + req)