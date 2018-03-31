import requests
import termcolor
import sys

color_map ={
   "Metro Green Line (803)": "green",
   "Metro Red Line (802)": "red",
   "Metro Blue Line (801)": "blue",
   "Metro Expo Line (806)": "cyan",
   "Metro Purple Line (805)": "magenta",
   "Metro Gold Line (804)": "yellow",
}

line_map = {
   803: "Metro Green Line (803)", 
   802: "Metro Red Line (802)",
   801: "Metro Blue Line (801)",
   806: "Metro Expo Line (806)",
   805: "Metro Purple Line (805)",
   804: "Metro Gold Line (804)",
}

# Couldn't find ground truth for these, so hard coded
# based on matching Nextbus
run_id_map = {
    801: { 0: "Los Angeles",
           1: "Long Beach",},
    802: { 0: "Union Station",
           1: "North Hollywood",},
    803: { 0: "Norwalk",
           1: "Redondo Beach",},
    804: { 0: "APU/Citrus",
           1: "Atlantic",},
    805: { 0: "Union Station",
           1: "Wilshire and Western",},
    806: { 0: "Los Angeles",
           1: "Santa Monica",},
}

############# Rest API functions ###############

def get_routes():
    """ Get all the routes for metro rail """
    routes_url = "http://api.metro.net/agencies/lametro-rail/routes/"
    resp = requests.get(routes_url)
    return resp.json()

def get_sequence(route):
    """ Get the sequence of stops for a route"""
    sequence_url = "http://api.metro.net/agencies/lametro-rail/routes/%s/sequence/"%(route)
    resp = requests.get(sequence_url)
    return resp.json()

def get_predictions(stop):
    """ Get the predictions for a stop """
    pred_url = "http://api.metro.net/agencies/lametro-rail/stops/%s/predictions"%(stop)
    resp = requests.get(pred_url)
    return resp.json()

class MenuState(object):
    def __init__(self):
        self.state = 'route'
      
        # Dictionary of functions to run for each state
        self.switch_dict = {
            'route': self.route,
            'stop': self.stop,
            "pred": self.pred,
        }


    def run(self):
        # Run the current state function
        return self.switch_dict[self.state]()

    def route(self):
        """ Print the current set of routes in a pretty format """

        route_data = get_routes()["items"]

        print "Select a route:"

        route_keys = sorted(route_data)

        for route in route_data:
            route_name = route["display_name"]
            route_color = color_map[route_name]

            choice = route["id"]
            output = route_name
            c_output = termcolor.colored(output, route_color)

            print "\t" + str(choice) + ". " +  c_output
    
        return True

    def stop(self):
        """Print the current set of stops in a pretty format """
        try:
            seq = get_sequence(self.data)
        except ValueError as e:
            # Almost certainly a value error here means bogus input
            # Just kick it back to previous menu
            print "Unknown route!"
            self.state = 'route'
            return False


        for stop in seq["items"]:
            choice = stop["id"]
            output = stop["display_name"]
            c_output = termcolor.colored(output, "white")

            print "\t" + str(choice) + ". " +  c_output

        return True

    def pred(self):
        """Print the current predictions for a stop"""
        try:
            predict = get_predictions(self.data)
        except ValueError as e:
            print "Unknown stop!"
            self.state = "stop"
            return False
        # A dictionary keyed by line, then direction
        run_dict = {}
        for pre in predict["items"]:
            run_info = pre["run_id"] 
            time = pre["minutes"]

            line, direction, var = run_info.split("_")

            if line not in run_dict:
                run_dict[line] = {}
            if direction not in run_dict[line]:
                run_dict[line][direction] = []

            run_dict[line][direction].append(time)

        # Now let's print 
        for line in run_dict:
            line_name = line_map[int(line)]
            line_color = color_map[line_name]
            print termcolor.colored(line_name, line_color)

            # Spin over the directions
            for direction in run_dict[line]:
                #print "\t%s"%(direction)
                dir_lookup = run_id_map[int(line)][int(direction)]
                print "\t%s"%(dir_lookup)

                # Spin over the times...
                for time in run_dict[line][direction]:
                    print "\t\t%s"%(time)

        return True

    def update(self, user):
        """Update the state, based on user info """
        
        # What's the current state?
        if self.state == "route":
            # Ok so that means the user has chosen a route, let's print it
            self.state = "stop"
            # the current data now is the route selected
            #route_keys = sorted(self.manager.routes.keys())
            self.data = user
        elif self.state == "stop":
            # They chose a stop, dump the predictions 
            self.data = user
            self.state = "pred"
        elif self.state == "pred":
            # Now they've seen the predictions  
            self.state = "route"
        else:
            raise RuntimeError("Unknow state transition: %s"%(self.state))

def run_menu():
    """ Stupid menu that manages CLI metro into """
    print "A Silly Metro Rail CLI Interface"

    not_quit = True
    menu_obj = MenuState()

    while not_quit:
        # Do whatever our current state calls for
        if not menu_obj.run():
            continue


        user = raw_input()
        if user == "q" or user == "quit" or user == "exit":
            break 

        if user == "" and menu_obj.state == "pred":
            menu_obj.update(user)
            continue
        elif user == "":
            continue

        # Update state based on user input
        menu_obj.update(user) 
    sys.exit(0)


if __name__ == "__main__":
    run_menu()
