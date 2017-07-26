import math
import pandas
import random

# User sets these at beginning
car_name = "Cavalry"
start_junkyard_name = "Downtown Paradise Yard"
r = 7
# Annealing parameters
starting_temperature = 10 ** 10
ending_temperature = 0.001
cooling_factor = 0.99

cars = pandas.read_excel("event_info.xlsx", sheetname="Cars")
cruise_speed = cars[cars["Car"].str.contains(car_name)].loc[0, "Cruising Speed (MPH)"]
boost_speed = cars[cars["Car"].str.contains(car_name)].loc[0, "Boosting Speed (MPH)"]
scale = 315  # number of pixels per mile
pixels_to_secs = 3600 / (cruise_speed * scale)

races = pandas.read_excel("event_info.xlsx", sheetname="Races", skip_footer=42)
races = races[[col for col in races.columns if car_name in col or "Destination" in col or "Name" in col]]
races.rename(columns={car_name + " Time (s)": "Time"}, inplace=True)
races = races.head(r)
races = [t for t in races.itertuples()]

coords = pandas.read_excel("map_data.xlsx", sheetname=None)
event_coords = {t.Name: t for t in coords["Events"].itertuples(index=False)}
dest_coords = {t.Name: t for t in coords["Event Destinations"].itertuples(index=False)}
junkyard_coords = {t.Name: t for t in coords["Junkyards"].itertuples(index=False)}
start_junkyard = junkyard_coords[start_junkyard_name]

best_route = list(races)
best_time = math.hypot(start_junkyard.X - event_coords[races[0].Name].X,
                       start_junkyard.Y - event_coords[races[0].Name].Y)
for i in range(len(races) - 1):
    this_dest = dest_coords[races[i].Destination]
    next_start = event_coords[races[i + 1].Name]
    best_time += races[i].Time + math.hypot(this_dest.X - next_start.X, this_dest.Y - next_start.Y) * pixels_to_secs
best_time += races[-1].Time
temp = starting_temperature
print("Initial:")
print(best_time)
print(best_route)

current_route = list(best_route)
current_time = best_time
while temp > ending_temperature:
    swap_idx = random.randrange(len(current_route) - 1)
    race1_start = event_coords[current_route[swap_idx].Name]
    race2_dest = dest_coords[current_route[swap_idx + 1].Destination]
    new_time = best_time

    prev_coords = dest_coords[current_route[swap_idx - 1].Destination] if swap_idx > 0 else start_junkyard
    new_time -= math.hypot(prev_coords.X - race1_start.X, prev_coords.Y - race1_start.Y) * pixels_to_secs
    new_time += math.hypot(prev_coords.X - race2_dest.X, prev_coords.Y - race2_dest.Y) * pixels_to_secs
    if swap_idx + 1 < len(current_route) - 1:
        next_coords = event_coords[current_route[swap_idx + 2].Name]
        new_time -= math.hypot(next_coords.X - race2_dest.X, next_coords.Y - race2_dest.Y) * pixels_to_secs
        new_time += math.hypot(next_coords.X - race1_start.X, next_coords.Y - race1_start.Y) * pixels_to_secs

    diff = new_time - current_time
    if diff < 0 or math.exp(-diff / temp) > random.random():
        current_time = new_time
        current_route[swap_idx], current_route[swap_idx + 1] = current_route[swap_idx + 1], current_route[swap_idx]
    if current_time < best_time:
        best_time = current_time
        best_route = list(current_route)
    temp *= cooling_factor

print("Final:")
print(best_time)
print(best_route)
print("Current:")
print(current_time)
print(current_route)