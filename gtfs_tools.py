# gtfs_tools.py -- tools to fetch, parse, and manage gtfs data

import csv
import feedparser
import os.path
import sqlite3
import sys
import termcolor

color_map ={
   "Metro Green Line (803)": "green",
   "Metro Red Line (802)": "red",
   "Metro Blue Line (801)": "blue",
   "Metro Expo Line (806)": "cyan",
   "Metro Purple Line (805)": "magenta",
   "Metro Gold Line (804)": "yellow",
}

class GTFS_manager(object):
    def __init__(self, data_dir):

        # Make sure data dir ended in a slash
        if data_dir[-1] != '/':
            data_dir += '/'
        self.data_dir = data_dir
        self.db_file = data_dir + "data.sqlite3"

        # Check to see if the database exists already
        if not os.path.isfile(self.db_file):
            self.conn = sqlite3.connect(self.db_file) 
            self.load_all() 

        # If it does, load the connection
        else:
            self.conn = sqlite3.connect(self.db_file) 
    
       	self.load_routes()
    
    #### Functions to manage keeping the GTFS files up to date

    #... Someday soon

    def fetch_latest_id(self):
        url = 'https://gitlab.com/LACMTA/gtfs_rail/commits/master.atom'
        d = feedparser.parse(url)
        lastupdate = d['feed']['updated']
        return lastupdate

    #### Functions to load up the current GTFS files and puke out some info 
    def load_all(self):
        """ Load all the GTFS files into a sqlite database """
        files = ["agency.txt", "calendar.txt", "calendar_dates.txt",
                 "routes.txt", "shapes.txt", "stops.txt", "stop_times.txt",
                 "trips.txt"]

        for gtfs_file in files:
            # Open the file and read the headers
            gtfs_file_path = self.data_dir + gtfs_file
            raw_name = gtfs_file[:-4] # Drop the .txt
            c = self.conn.cursor()
            with open(gtfs_file_path, 'r') as g_file:
                header = g_file.readline()
                # Let's build the query to make the table
                # Dangerous?
                #header_text = ", ".join(header)
                query = "CREATE TABLE %s ("%(raw_name) + header + ")" 
                c.execute(query)
                
                # Now put all the data in
                data_lines = g_file.readlines()
                data_lines_split = [x.split(',') for x in data_lines]

                row_size = len(header.split(','))
                args = "?, " * row_size
                args = args[:-2]
                query = "INSERT INTO %s VALUES ("%(raw_name) + args + ")"

                c.executemany(query, data_lines_split)

            self.conn.commit()

    def load_routes(self):
        """ Load the set of routes """

        self.routes = {}

        route_file_name = self.data_dir + "routes.txt"
        with open(route_file_name, 'r') as route_file:
            reader = csv.reader(route_file)
            row1 = next(reader)
            for row in reader:
                # Save that route
                self.routes[row[0]] = row[1:]

    #### Functions that query the database and spit out answers
    def get_routes(self):
        """ Return all the routes """

        c = self.conn.cursor()
        c.execute("SELECT * FROM routes")
        data = c.fetchall()

        return data

class MenuState(object):
    def __init__(self, manager):
        self.state = 'route'
      
        # Dictionary of functions to run for each state
        self.switch_dict = {
            'route': self.route,
            'stop': self.stop,
        }

        self.manager = manager

        self.data = None

    def run(self):
        # Run the current state function
        self.switch_dict[self.state]()

    def route(self):
        """ Print the current set of routes in a pretty format """

        route_data = self.manager.get_routes()

        print "Select a route: (1-%d)"%(len(route_data))

        route_keys = sorted(self.manager.routes.keys())

        for index, route in enumerate(route_keys):
            route_name = self.manager.routes[route][1]
            route_color = color_map[route_name]

            choice  = index + 1 # 1 indexed

            output = route_name
            c_output = termcolor.colored(output, route_color)

            print "\t" + str(choice) + ". " +  c_output

    def stop(self):
        """Print the current set of stops in a pretty format """
        print self.data

    def update(self, user):
        """Update the state, based on user info """
        
        # What's the current state?
        if self.state == "route":
            # Ok so that means the user has chosen a route, let's print it
            self.state = "stop"
            # the current data now is the route selected
            route_keys = sorted(self.manager.routes.keys())
            index = int(user) - 1
            route = self.manager.routes[route_keys[index]]
            self.data = [route_keys[index]] + route
        else:
            raise RuntimeError("Unknow state transition: %s"%(self.state))

def run_menu(manager):
    """ Stupid menu that manages CLI metro into """
    print "A Silly Metro Rail CLI Interface"

    not_quit = True
    menu_obj = MenuState(manager)

    while not_quit:
        # Do whatever our current state calls for
        menu_obj.run()

        user = raw_input()
        if user == "q" or user == "quit" or user == "exit":
            break 

        # Update state based on user input
        menu_obj.update(user) 
    sys.exit(0)


if __name__ == "__main__":

    # Inst a manager

    manager = GTFS_manager("data/")

    # Fire up the menu
    run_menu(manager)

