
import folium
from folium.plugins import BeautifyIcon

class VRPInstance:
    """
    Represents a Vehicle Routing Problem (VRP) instance with multiple node types.
    
    Node types include:
        - 'loading'
        - 'unloading'
        - 'charger'
        - 'parking'
    
    Attributes:
        locations (dict): All locations, keyed by name.
        distance_matrix (dict of dict): Distance between locations (km).
        time_matrix (dict of dict): Travel time between locations (minutes).
        charging_costs (dict): Charging cost per charger.
        cost_matrix (dict of dict): Travel cost between locations.
        
        # Convenience attributes
        chargers (list): Names of all charger locations.
        loadings (list): Names of all loading locations.
        unloadings (list): Names of all unloading locations.
        parkings (list): Names of all parking locations.
    """

    def __init__(self, locations, distance_matrix, time_matrix, charging_costs, cost_matrix):
        self.locations = locations
        self.distance_matrix = distance_matrix
        self.time_matrix = time_matrix
        self.charging_costs = charging_costs
        self.cost_matrix = cost_matrix

        # Separate entities for easy access
        self.chargers = [name for name, loc in locations.items() if loc['node'] == 'charger']
        self.loadings = [name for name, loc in locations.items() if loc['node'] == 'loading']
        self.unloadings = [name for name, loc in locations.items() if loc['node'] == 'unloading']
        self.parkings = [name for name, loc in locations.items() if loc['node'] == 'parking']

    # -----------------------
    # Access methods
    # -----------------------
    def get_location_names(self):
        return list(self.locations.keys())

    def get_distance(self, from_loc, to_loc):
        return self.distance_matrix[from_loc,to_loc]

    def get_time(self, from_loc, to_loc):
        return self.time_matrix[from_loc,to_loc]

    def get_cost(self, from_loc, to_loc):
        return self.cost_matrix[from_loc,to_loc]

    def is_type(self, loc_name, node_type):
        return self.locations[loc_name]['node'] == node_type

    def get_charging_cost(self, loc_name):
        if self.is_type(loc_name, 'charger'):
            return self.charging_costs.get(loc_name, 0)
        return 0

    def plot_vrp_instance_default_icons(self, save_path="vrp_instance.html"):
        """
        Genera un mapa HTML con todos los nodos del VRP,
        usando iconos normales de Folium, sin agruparlos.
            """
        # Centro del mapa
        lats = [loc["coords"][0] for loc in self.locations.values()]
        lons = [loc["coords"][1] for loc in self.locations.values()]
        center = [sum(lats)/len(lats), sum(lons)/len(lons)]

        m = folium.Map(
            location=center,
            zoom_start=6,
            tiles="CartoDB positron"  # menos saturado que OpenStreetMap
        )

        # Iconos por tipo de nodo
        ICONS = {
            "parking":    ("green",  "home"),
            "loading":    ("blue",   "arrow-up"),
            "unloading":  ("red",    "arrow-down"),
            "charger":    ("orange", "bolt"),
        }

        # Añadir nodos sin agrupar
        for name, loc in self.locations.items():
            lat, lon = loc["coords"]
            node_type = loc["node"]

            color, icon = ICONS.get(node_type, ("black", "circle"))

            # Aquí la chincheta tiene color según tipo y el icono interno es blanco
            folium.Marker(
                location=(lat, lon),
                popup=f"{name}<br>Tipo: {node_type}",
                icon=folium.Icon(
                    color=color,      # color de la chincheta
                    icon_color="white", # color del icono dentro
                    icon=icon,
                    prefix="fa"
                )
            ).add_to(m)

        # Guardar archivo HTML
        m.save(save_path)

    def __repr__(self):
        types_summary = {t: len(lst) for t, lst in zip(
            ['chargers', 'loadings', 'unloadings', 'parkings'],
            [self.chargers, self.loadings, self.unloadings, self.parkings]
        )}
        return f"<VRPInstance: {len(self.locations)} locations, {types_summary}>"
