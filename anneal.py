import copy
import itertools
import math
import pandas
import random
import tqdm


class Location(object):
    def __init__(self, init_tuple):
        self.name = init_tuple.Name
        self.coords = coords[self.name]
        self.travel_time = 0  # travel time to next event/location

    def __repr__(self):
        return "{{name: {0}, travel time: {1}}}".format(self.name, self.travel_time)


class Event(Location):
    def __init__(self, init_tuple):
        self.time = init_tuple.Time
        self.dest = init_tuple.Destination
        self.dest_coords = coords[self.dest]
        self.type = init_tuple.Type
        self.restart = False
        super().__init__(init_tuple)

    def __repr__(self):
        return "{{name: {0}, type: {1}, time: {2}, travel time: {3}, restart: {4}}}".format(
            self.name, self.type, self.time, self.travel_time, self.restart)


class Route(object):
    def __init__(self, event_tuples, start_loc, end_loc=None):
        self.events = []
        self.total_time = 0
        self.event_time = 0
        self.start_loc = Location(start_loc)
        self.end_loc = None if not end_loc else Location(end_loc)

        for event in event_tuples:
            self.event_time += event.Time
            self.total_time += event.Time
            self.events.append(Event(event))
        self.calculate_time()

    def swap(self, idx1, idx2):
        self.events[idx1], self.events[idx2] = self.events[idx2], self.events[idx1]
        self.total_time = self.event_time
        self.calculate_time()

    def calculate_time(self):
        for i in range(r - 1):
            old, new = self.events[i], self.events[i + 1]
            old.travel_time, old.restart = best_path(old, new)
            self.total_time += old.travel_time
        self.start_loc.travel_time = time_between_coords(self.start_loc.coords, self.events[0].coords)
        self.total_time += self.start_loc.travel_time
        if self.end_loc:
            self.events[r - 1].travel_time, self.events[r - 1].restart = best_path(self.events[r - 1], self.end_loc)
            self.total_time += self.events[r - 1].travel_time


def time_between_coords(coords1, coords2):
    return math.hypot(coords1.X - coords2.X, coords1.Y - coords2.Y) * pixels_to_secs


def best_path(source, dest):  # Only works if source is an Event
    direct_route_time = time_between_coords(source.dest_coords, dest.coords)
    restart_route_time = restart_times[source.type] + time_between_coords(source.coords, dest.coords)
    return min(direct_route_time, restart_route_time), restart_route_time < direct_route_time


if __name__ == "__main__":
    # User sets these at beginning
    car_name = "Fastback"
    start_loc_names = ["Downtown Paradise Yard", "Palm Bay Heights Yard", "Harbor Town Yard", "Silver Lake Yard",
                       "White Mountain Yard"]
    # start_loc_names = ["Downtown Paradise Yard"]
    end_loc_names = ["Downtown Paradise Yard", "Palm Bay Heights Yard", "Harbor Town Yard", "Silver Lake Yard",
                     "White Mountain Yard"]
    # end_loc_names = None
    event_types = ["Race", "Marked Man", "Stunt Run"]
    r = 26  # use r events
    file_name = "B to A License 2"
    travel_time_cutoff = 40  # average time between one race and another
    # Annealing parameters
    starting_temp = 10 ** 10
    ending_temp = 0.0001
    cooling_factor = 0.99
    num_restarts = 3

    cars = pandas.read_excel("event_info.xlsx", sheetname="Cars")
    car = cars[cars["Car"].str.contains(car_name)].iloc[0]
    cruise_speed = car["Cruising Speed (MPH)"]
    boost_speed = car["Boosting Speed (MPH)"]

    coords_raw = pandas.read_excel("map_data.xlsx", sheetname=None)
    coords = {}
    for sheet in coords_raw.values():
        coords.update({t.Name: t for t in sheet.itertuples(index=False)})

    event_times_raw = pandas.read_excel("event_info.xlsx", sheetname=event_types)
    event_times = pandas.DataFrame()
    for sheet_name, sheet in event_times_raw.items():
        sheet = sheet.rename(columns={car_name + " Time (s)": "Time"})
        sheet = sheet[["Name", "Time", "Destination"]]
        sheet.loc[:, "Type"] = sheet_name
        event_times = event_times.append(sheet, ignore_index=True)
    event_times = event_times[pandas.notnull(event_times["Destination"])]
    event_times = event_times.sort_values("Time")

    cutscene_times = pandas.read_excel("event_info.xlsx", sheetname="Cutscenes & Actions", index_col=0)
    restart_times = {}
    restart_time = cutscene_times.loc["Restart Event", "Time (s)"] + cutscene_times.loc["Cancel Event", "Time (s)"]
    for event_type in event_types:
        restart_times[event_type] = restart_time + cutscene_times.loc[event_type + " Intro", "Time (s)"]
        if event_type == "Stunt Run" or event_type == "Road Rage":
            restart_times[event_type] += cutscene_times.loc["Fail " + event_type, "Time (s)"]

    # Other parameters
    scale = 315  # number of pixels per mile
    pixels_to_secs = 3600 / (cruise_speed * scale)

    if end_loc_names:
        permutations = itertools.product(start_loc_names, end_loc_names)
    else:
        permutations = [[start_loc_name, None] for start_loc_name in start_loc_names]
    total_permutations = len(start_loc_names) if not end_loc_names else len(start_loc_names) * len(end_loc_names)
    open(file_name, 'w').close()  # clear file
    for start, end in tqdm.tqdm(permutations, total=total_permutations):
        current_event_times = event_times.head(r)
        current_event_times = current_event_times.sample(frac=1)
        if end:
            best_route = Route(current_event_times.itertuples(index=False), coords[start], coords[end])
        else:
            best_route = Route(current_event_times.itertuples(index=False), coords[start])
        # print("Initial time: {0}".format(best_route.total_time))
        reasonable_travel = False
        extra_idx = r
        local_best_route = copy.deepcopy(best_route)
        while not reasonable_travel and extra_idx < event_times.shape[0]:
            for _ in range(num_restarts):  # repeat simulated annealing a couple times
                current_route = copy.deepcopy(local_best_route)
                temp = starting_temp
                while temp > ending_temp:
                    swap_idx1, swap_idx2 = random.sample(range(r), 2)
                    new_route = copy.deepcopy(current_route)
                    new_route.swap(swap_idx1, swap_idx2)
                    diff = new_route.total_time - current_route.total_time
                    if diff < 0 or math.exp(-diff / temp) > random.random():
                        current_route = new_route
                    if current_route.total_time < local_best_route.total_time:
                        local_best_route = current_route
                    temp *= cooling_factor
            if local_best_route.total_time < best_route.total_time:
                best_route = copy.deepcopy(local_best_route)

            # Replace a race if travel time is large
            max_idx = 0
            max_travel_time = 0
            for i in range(len(local_best_route.events) - 1):
                current_travel_time = local_best_route.events[i].travel_time + \
                                      local_best_route.events[i + 1].travel_time
                if current_travel_time > max_travel_time:
                    max_idx = i + 1
                    max_travel_time = current_travel_time
            current_travel_time = local_best_route.start_loc.travel_time + local_best_route.events[0].travel_time
            if current_travel_time > max_travel_time:
                max_idx = 0
                max_travel_time = current_travel_time
            reasonable_travel = True
            # print(max_travel_time, travel_time_cutoff * 2)
            if max_travel_time > travel_time_cutoff * 2:
                # print(local_best_route.events[max_idx - 1])
                # print(local_best_route.events[max_idx])
                reasonable_travel = False
                local_best_route.events[max_idx] = Event(event_times.iloc[extra_idx])
                random.shuffle(local_best_route.events)
                local_best_route.calculate_time()
                extra_idx += 1
                # print("------")

        with open(file_name, 'a') as f:
            f.write("Final time: {0}\n".format(best_route.total_time))
            f.write("Start location: {0}\n".format(start))
            f.write("End location: {0}\n".format(end))
            f.write("{0}\n".format(best_route.start_loc))
            for event in best_route.events:
                f.write("{0}\n".format(event))
            f.write("---------------------------------\n")

        # print("Final time: {0}".format(best_route.total_time))
        # print("Start location: {0}".format(start))
        # print("End location: {0}".format(end))
        # for event in best_route.events:
        #     print("{0}".format(event))
        # print("---------------------------------")
