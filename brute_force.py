import itertools
import math
import pandas
import tqdm  # loading bar


# User sets these at beginning
car_name = "Cavalry"
start_junkyard_name = "Downtown Paradise Yard"
r = 2

cars = pandas.read_excel("event_info.xlsx", sheetname="Cars")
cruise_speed = cars[cars["Car"].str.contains(car_name)].loc[0, "Cruising Speed (MPH)"]
boost_speed = cars[cars["Car"].str.contains(car_name)].loc[0, "Boosting Speed (MPH)"]

races = pandas.read_excel("event_info.xlsx", sheetname="Races")
races = races[[col for col in races.columns if ("Time" not in col and "Distance" not in col) or car_name in col]]
races.rename(columns={car_name + " Time (s)": "Time"}, inplace=True)
races = {t.Name: t for t in races.itertuples(index=False)}

coords = pandas.read_excel("map_data.xlsx", sheetname=None)
event_coords = {t.Name: t for t in coords["Events"].itertuples(index=False)}
dest_coords = {t.Name: t for t in coords["Event Destinations"].itertuples(index=False)}
junkyard_coords = {t.Name: t for t in coords["Junkyards"].itertuples(index=False)}
start_junkyard = junkyard_coords[start_junkyard_name]

total_perms = 1
for i in range(len(races), len(races) - r, -1):
    total_perms *= i

race_restart_time = 17.5
scale = 315  # number of pixels per mile
pixels_to_secs = 3600 / (cruise_speed * scale)
loc_times = {}
for perm in tqdm.tqdm(itertools.permutations(races.keys(), r), total=total_perms):
    first_start = event_coords[perm[0]]
    time_taken = math.hypot(start_junkyard.X - first_start.X,
                            start_junkyard.Y - first_start.Y) * pixels_to_secs
    route = [""] * (r + 1)
    route[0] = start_junkyard_name

    for i in range(0, r - 1):
        this_race = races[perm[i]]
        time_taken += this_race.Time
        route[i + 1] = this_race.Name
        next_start = event_coords[perm[i + 1]]
        event_start = event_coords[this_race.Name]
        event_dest = dest_coords[this_race.Destination]
        restart_time = race_restart_time + math.hypot(event_start.X - next_start.X,
                                                      event_start.Y - next_start.Y) * pixels_to_secs
        direct_time = math.hypot(event_dest.X - next_start.X,
                                 event_dest.Y - next_start.Y) * pixels_to_secs
        if direct_time <= restart_time:
            time_taken += direct_time
        else:
            time_taken += restart_time
            route[i + 1] += " (Restart)"

    last_race = races[perm[-1]]
    time_taken += last_race.Time
    route[-1] = last_race.Name
    if (last_race.Destination not in loc_times) or (time_taken < loc_times[last_race.Destination][0]):
        loc_times[last_race.Destination] = [time_taken, route]
    time_taken += race_restart_time
    if (last_race.Name not in loc_times) or (time_taken < loc_times[last_race.Name][0]):
        loc_times[last_race.Name] = [time_taken, list(route)]
        loc_times[last_race.Name][1][-1] += " (Restart)"

loc_times_list = [[i, loc_times[i][0], loc_times[i][1]] for i in loc_times]
loc_times_list = sorted(loc_times_list, key=lambda item: item[1])
for i in loc_times_list:
    print(i)