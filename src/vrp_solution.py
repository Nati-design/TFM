import os
import pickle
import plotly.graph_objects as go
import folium
from folium.plugins import BeautifyIcon


class VRPSolution:
    """
    Represents a solution for a VRP instance.

    Attributes:
        instance (VRPInstance): The VRP instance this solution belongs to.
        routes (list of list): List of routes. Each route is a list of location names.
        total_distance (float): Total distance of all routes (km).
        total_time (float): Total travel time of all routes (minutes).
        total_cost (float): Total travel cost of all routes.
        charging_stops (dict): Number of times each charger is used.
        short_feasibility_flag (bool | None): True if all routes pass route-level checks.
        complete_feasibility_flag (bool | None): True if all load/unload points visited.
    """

    def __init__(self, instance):
        self.instance = instance
        self.routes = []
        self.total_distance = 0
        self.total_time = 0
        self.total_cost = 0
        self.charging_stops = {loc: 0 for loc in instance.chargers}
        self.execution_time = None
        self.short_feasibility_flag = None
        self.complete_feasibility_flag = None

    # ---------------------------
    # Route-level methods
    # ---------------------------
    def add_route(self, route):
        self.short_feasibility_check(route)

        self.routes.append(route)
        for i in range(len(route)-1):
            from_loc = route[i]
            to_loc = route[i+1]
            self.total_distance += self.instance.get_distance(from_loc, to_loc)
            self.total_time += self.instance.get_time(from_loc, to_loc)
            self.total_cost += self.instance.get_cost(from_loc, to_loc)
            self.total_cost += self.instance.charging_costs.get(from_loc, 0)
            
            if self.instance.is_type(to_loc, 'charger'):
                self.charging_stops[to_loc] += 1

    # ---------------------------
    # Solution-level methods
    # ---------------------------
    def all_loads_unloads_visited(self):
        visited = set(loc for route in self.routes for loc in route)
        missing_loadings = [loc for loc in self.instance.loadings if loc not in visited]
        missing_unloadings = [loc for loc in self.instance.unloadings if loc not in visited]

        return not (missing_loadings or missing_unloadings)

    def short_feasibility_check(self, route):
        """
        Check route-level feasibility:
        1. Starts and ends at parking
        2. No loading after unloading
        Returns True/False and prints the reason if False.
        """
        self.short_feasibility_flag = False
        if not route:
            print("Route is empty")
            return False

        if not self.instance.is_type(route[0], 'parking'):
            print(f"Route does not start at a parking: {route[0]}")
            return False

        if not self.instance.is_type(route[-1], 'parking'):
            print(f"Route does not end at a parking: {route[-1]}")
            return False

        unloading_seen = False
        for loc in route:
            if self.instance.is_type(loc, 'unloading'):
                unloading_seen = True
            if unloading_seen and self.instance.is_type(loc, 'loading'):
                print(f"Route has loading after unloading: {loc}")
                return False
        
        self.short_feasibility_flag = True
        return True
    
    def complete_feasibility(self):
        """
        Run all feasibility tests and update flags:
        - self.short_feasibility_flag: True if all routes pass the route-level check
        - self.complete_feasibility_flag: True if both route-level and global load/unload checks pass
        """

        # Route-level check: all routes pass
        all_routes_ok = all(self.short_feasibility_check(r) for r in self.routes)
        self.short_feasibility_flag = all_routes_ok

        # Solution-level check: all load/unload points visited
        loads_unloads_ok = self.all_loads_unloads_visited()

        # Overall solution feasible only if both are True
        self.complete_feasibility_flag = all_routes_ok and loads_unloads_ok


    def save(self, filepath):
        """
        Save the VRPSolution instance to a pickle file.
        
        :param directory: Path to the folder where the file will be saved.
        :param filename: Optional filename. If None, use default 'vrp_solution.pkl'.
        """
        
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

        print(f"Solution saved to {filepath}")


    def plot_vrp_solution(self, save_path="vrp_solution.html"):
        """
        Genera un mapa HTML con la solución VRP:
        - Nodos con iconos por tipo (parking, loading, unloading, charger)
        - Rutas de los vehículos en colores
        - Sin agrupación de marcadores
        """

        instance = self.instance

        # -------------------------
        # Centro del mapa
        # -------------------------
        all_lats = [loc['coords'][0] for loc in instance.locations.values()]
        all_lons = [loc['coords'][1] for loc in instance.locations.values()]
        map_center = [sum(all_lats)/len(all_lats), sum(all_lons)/len(all_lons)]

        m = folium.Map(
            location=map_center,
            zoom_start=6,
            tiles="CartoDB positron"  # fondo claro
        )

        # -------------------------
        # Colores para rutas
        # -------------------------
        colors = ["blue", "red", "green", "orange", "purple", "brown", "pink", "darkcyan"]

        # -------------------------
        # 1. Dibujar rutas
        # -------------------------
        for idx, route in enumerate(self.routes):
            color = colors[idx % len(colors)]

            # Coordenadas de la ruta (lat, lon)
            coords = [(instance.locations[loc]['coords'][0],
                    instance.locations[loc]['coords'][1]) for loc in route]

            # Línea de la ruta
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=4,
                opacity=0.7,
                tooltip=f"Route {idx+1}"
            ).add_to(m)

            # Pequeños círculos en los puntos de la ruta
            for loc in route:
                lat, lon = instance.locations[loc]['coords']
                folium.CircleMarker(
                    location=(lat, lon),
                    radius=5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=1
                ).add_to(m)

        # -------------------------
        # 2. Dibujar nodos con iconos por tipo
        # -------------------------
        ICONS = {
            "parking":    ("green",  "home"),
            "loading":    ("blue",   "arrow-up"),
            "unloading":  ("red",    "arrow-down"),
            "charger":    ("orange", "bolt"),
        }

        for loc_name, loc_data in instance.locations.items():
            lat, lon = loc_data['coords']
            node_type = loc_data['node']

            color, icon = ICONS.get(node_type, ("black", "circle"))

            folium.Marker(
                location=(lat, lon),
                popup=f"{loc_name} ({node_type})",
                icon=folium.Icon(
                    color=color,       # color de la chincheta
                    icon_color="white", # icono dentro blanco
                    icon=icon,
                    prefix="fa"
                )
            ).add_to(m)

        # -------------------------
        # Guardar mapa
        # -------------------------
        m.save(save_path)
        
    def __repr__(self):
        return (f"<VRPSolution: {len(self.routes)} routes, "
                f"total_distance={self.total_distance:.2f} km, "
                f"short_feasibility_flag={self.short_feasibility_flag}, "
                f"complete_feasibility_flag={self.complete_feasibility_flag}>")
