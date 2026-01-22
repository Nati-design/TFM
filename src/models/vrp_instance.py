import folium

class VRPInstance:
    """
    Represents a Vehicle Routing Problem (VRP) instance with multiple node types.

    Supported node types:
        - 'loading'    : locations where products are loaded
        - 'unloading'  : locations where products are unloaded
        - 'charger'    : electric vehicle charging stations
        - 'parking'    : parking or depot locations for route start/end

    Attributes:
        locations (dict):
            Dictionary of all locations, keyed by name.
            Each value must include:
                - 'coords': tuple (latitude, longitude)
                - 'node'  : node type ('loading', 'unloading', 'charger', 'parking')
        distance_matrix (dict of tuple: float):
            Distance (km) between location pairs, key: (from_loc, to_loc)
        time_matrix (dict of tuple: float):
            Travel time (minutes) between location pairs
        cost_matrix (dict of tuple: float):
            Travel cost between location pairs
        charging_cost (dict):
            Charging cost for each 'charger' location

    Convenience attributes (automatically computed):
        chargers (list): names of all 'charger' locations
        loadings (list): names of all 'loading' locations
        unloadings (list): names of all 'unloading' locations
        parkings (list): names of all 'parking' locations

    Main methods:
        - get_distance(from_loc, to_loc)
        - get_time(from_loc, to_loc)
        - get_cost(from_loc, to_loc)
        - is_type(loc_name, node_type)
        - get_charging_cost(loc_name)
        - get_location_names()
        - get_center_coords()
        - plot_vrp_instance(save_path)
    """

    node_types = ['charger', 'loading', 'unloading', 'parking']

    def __init__(self, locations, distance_matrix, time_matrix, charging_cost, cost_matrix, max_km_per_vehicle = None):
        # Basic validations
        assert isinstance(locations, dict) and locations, "locations must be a non-empty dict"
        for name, info in locations.items():
            assert "coords" in info and "node" in info, f"{name} must have 'coords' and 'node'"

        self.locations = locations
        self.distance_matrix = distance_matrix
        self.time_matrix = time_matrix
        self.charging_cost = charging_cost
        self.cost_matrix = cost_matrix
        self.max_km_per_vehicle = max_km_per_vehicle

        # Automatic classification of nodes
        for node_type in self.node_types:
            setattr(self, f"{node_type}s", [name for name, loc in locations.items() if loc['node'] == node_type])

    # -----------------------
    # Access methods
    # -----------------------
    def get_location_names(self):
        return list(self.locations.keys())

    def get_distance(self, from_loc, to_loc):
        try:
            return self.distance_matrix[(from_loc, to_loc)]
        except KeyError:
            raise ValueError(f"Distance not defined between {from_loc} and {to_loc}")

    def get_time(self, from_loc, to_loc):
        try:
            return self.time_matrix[(from_loc, to_loc)]
        except KeyError:
            raise ValueError(f"Time not defined between {from_loc} and {to_loc}")

    def get_cost(self, from_loc, to_loc):
        try:
            return self.cost_matrix[(from_loc, to_loc)]
        except KeyError:
            raise ValueError(f"Cost not defined between {from_loc} and {to_loc}")

    def is_type(self, loc_name, node_type):
        return self.locations[loc_name]['node'] == node_type

    def get_charging_cost(self, loc_name):
        if self.is_type(loc_name, 'charger'):
            return self.charging_cost.get(loc_name, 0)
        return 0

    # -----------------------
    # Visualization
    # -----------------------
    def get_center_coords(self):
        lats = [loc["coords"][0] for loc in self.locations.values()]
        lons = [loc["coords"][1] for loc in self.locations.values()]
        return [sum(lats)/len(lats), sum(lons)/len(lons)]

    def plot_vrp_instance(self, save_path="vrp_instance.html"):
        """Generates an HTML map with all VRP nodes using layers by node type."""
        m = folium.Map(location=self.get_center_coords(), zoom_start=6, tiles="CartoDB positron")

        ICONS = {
            "parking":    ("green",  "home"),
            "loading":    ("blue",   "arrow-up"),
            "unloading":  ("red",    "arrow-down"),
            "charger":    ("orange", "bolt"),
        }

        for node_type in self.node_types:
            fg = folium.FeatureGroup(name=node_type.capitalize())
            for name in getattr(self, f"{node_type}s"):
                loc = self.locations[name]
                lat, lon = loc["coords"]
                color, icon = ICONS[node_type]
                folium.Marker(
                    location=(lat, lon),
                    popup=f"{name}<br>Type: {node_type}",
                    icon=folium.Icon(color=color, icon_color="white", icon=icon, prefix="fa")
                ).add_to(fg)
            fg.add_to(m)

        folium.LayerControl().add_to(m)
        m.save(save_path)

    # -----------------------
    # Representation
    # -----------------------
    def __repr__(self):
        summary = {nt: len(getattr(self, f"{nt}s")) for nt in self.node_types}
        return f"<VRPInstance: {len(self.locations)} locations, {summary}>"
