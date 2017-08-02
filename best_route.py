from collections import namedtuple
from itertools import product

License = namedtuple("License", "time start end")
license_times = []
files = ["C to B License", "B to A License", "A to Burnout License"]
for file in files:
    with open(file, "r") as f:
        license_time = []
        line = f.readline().rstrip('\n')
        while line:
            if "Final time" in line:
                time = float(line.replace("Final time: ", ""))
                start = f.readline().rstrip('\n').replace("Start location: ", "")
                end = f.readline().rstrip('\n').replace("End location: ", "")
                license_time.append(License(time=time, start=start, end=end))
            line = f.readline()
        license_times.append(license_time)

perms = list(product(*license_times))
perms = [perm for perm in perms if perm[0].end == perm[1].start and perm[1].end == perm[2].start]
perms.sort(key=lambda row: row[0].time + row[1].time + row[2].time)
for perm in perms:
    print("{0}, {1}".format(perm[0].time + perm[1].time + perm[2].time, perm))