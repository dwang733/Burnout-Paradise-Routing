import copy
import math
import pandas
import random


class Location(object):
    def __init__(self, init_tuple):
        self.name = init_tuple.Name
        self.coords = coords[self.name]
        self.travel_time = 0  # travel time to next event/location

    def __repr__(self):
        return "{{name: {0}, travel time: {1}".format(self.name, self.travel_time)


class Event(Location):
    def __init__(self, init_tuple):
        self.time = init_tuple.Time
        self.dest = init_tuple.Destination
        self.dest_coords = coords[self.dest]
        self.restart = False
        super().__init__(init_tuple)

    def __repr__(self):
        return "{{name: {0}, time: {1}, travel time: {2}, restart: {3}}}".format(self.name, self.time, self.travel_time,
                                                                               self.restart)


class Route(object):
    def __init__(self, event_tuples, start_loc=None, end_loc=None):
        self.events = []
        self.time = 0
        # TODO: Maybe allow start_loc and end_loc to be Events if it's an event?
        self.start_loc = None if not start_loc else Location(start_loc)
        self.end_loc = None if not end_loc else Location(end_loc)

        for event in event_tuples:
            self.time += event.Time
            self.events.append(Event(event))

        for i in range(len(self.events) - 1):
            old, new = self.events[i], self.events[i + 1]
            old.travel_time, old.restart = best_path(old, new)
            self.time += old.travel_time
        if self.start_loc:
            self.start_loc.travel_time = time_between_coords(self.start_loc.coords, self.events[0].coords)
            self.time += self.start_loc.travel_time
        if self.end_loc:
            self.events[-1].travel_time, self.events[-1].restart = best_path(self.events[-1].coords, self.end_loc)
            self.time += self.events[-1].travel_time

    def swap_consecutive(self, idx):
        event1, event2 = self.events[idx], self.events[idx + 1]
        event1_prev = self.events[idx - 1] if idx - 1 >= 0 else self.start_loc
        event2_next = self.events[idx + 2] if idx + 2 < len(self.events) else self.end_loc
        if event1_prev:
            self.time -= event1_prev.travel_time
            if type(event1_prev).__name__ == "Location":
                event1_prev.travel_time = time_between_coords(event1_prev.coords, event2.coords)
            else:
                event1_prev.travel_time, event1_prev.restart = best_path(event1_prev, event2)
            self.time += event1_prev.travel_time
        self.time -= event2.travel_time
        event2.travel_time, event2.restart = best_path(event2, event1)
        self.time += event2.travel_time
        self.time -= event1.travel_time
        if event2_next:
            event1.travel_time, event1.restart = best_path(event1, event2_next)
            self.time += event1.travel_time
        else:
            event1.travel_time, event1.restart = 0, False
        self.events[idx], self.events[idx + 1] = self.events[idx + 1], self.events[idx]


def time_between_coords(coords1, coords2):
    return math.hypot(coords1.X - coords2.X, coords1.Y - coords2.Y) * pixels_to_secs


def best_path(source, dest):  # Only works if source is an Event
    direct_route_time = time_between_coords(source.dest_coords, dest.coords)
    restart_route_time = race_restart_time + time_between_coords(source.coords, dest.coords)
    return min(direct_route_time, restart_route_time), restart_route_time < direct_route_time


if __name__ == "__main__":
    # User sets these at beginning
    car_name = "Cavalry"
    start_loc_name = "Maplemount Country Club"
    end_loc_name = "Downtown Paradise Yard"
    r = 7  # only use r shortest races
    # Annealing parameters
    starting_temp = 10 ** 10
    ending_temp = 0.0001
    cooling_factor = 0.99

    cars = pandas.read_excel("event_info.xlsx", sheetname="Cars")
    car = cars[cars["Car"].str.contains(car_name)].iloc[0]
    cruise_speed = car["Cruising Speed (MPH)"]
    boost_speed = car["Boosting Speed (MPH)"]

    coords_raw = pandas.read_excel("map_data.xlsx", sheetname=None)
    coords = {}
    for sheet in coords_raw.values():
        coords.update({t.Name: t for t in sheet.itertuples(index=False)})

    races = pandas.read_excel("event_info.xlsx", sheetname="Races", skip_footer=42)
    races.rename(columns={car_name + " Time (s)": "Time"}, inplace=True)
    # races = races[[col for col in races.columns if car_name in col or "Destination" in col or "Name" in col]]
    races = races[["Name", "Time", "Destination"]]
    races = races.head(r)

    # Other parameters
    race_restart_time = 17.5
    scale = 315  # number of pixels per mile
    pixels_to_secs = 3600 / (cruise_speed * scale)

    best_route = Route(races.itertuples(index=False), coords[start_loc_name])
    print("Initial time: {0}".format(best_route.time))
    current_route = copy.deepcopy(best_route)
    temp = starting_temp
    while temp > ending_temp:
        swap_idx = random.randrange(r - 1)
        new_route = copy.deepcopy(current_route)
        new_route.swap_consecutive(swap_idx)
        diff = new_route.time - current_route.time
        if diff < 0 or math.exp(-diff / temp) > random.random():
            current_route = new_route
        if current_route.time < best_route.time:
            best_route = current_route
        temp *= cooling_factor

    print("Final time: {0}".format(best_route.time))
    print("Start location: {0}".format(start_loc_name))
    print("End location: {0}".format(end_loc_name))
    for event in best_route.events:
        print(event)
