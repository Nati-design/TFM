import pickle
import math
from typing import List, Dict, Tuple, Optional
import folium


class VRPSolution:
    """
    Represents a solution for a VRP instance.

    Attributes:
        instance (VRPInstance): The VRP instance this solution belongs to.
        routes (List[List[str]]): List of routes. Each route is a list of location names.
        total_distance (float): Total distance of all routes (km).
        total_time (float): Total travel time of all routes (minutes).
        total_cost (float): Total travel cost of all routes.
        charging_stops (Dict[str, int]): Number of times each charger is used.
        execution_time (Optional[float]): Execution time of the heuristic (if measured).
        short_feasibility_flag (Optional[bool]): True if all routes pass route-level checks.
        complete_feasibility_flag (Optional[bool]): True if all load/unload points visited.
    """

    def __init__(self, instance) -> None:
        self.instance = instance
        self.routes: List[List[str]] = []
        self.total_distance: float = 0
        self.total_time: float = 0
        self.total_cost: float = 0
        self.charging_stops: Dict[str, int] = {loc: 0 for loc in instance.chargers}
        self.execution_time: Optional[float] = None
        self.short_feasibility_flag: Optional[bool] = None
        self.complete_feasibility_flag: Optional[bool] = None

    # ---------------------------
    # Route-level methods
    # ---------------------------
    def add_route(self, route: List[str]) -> None:
        """
        Adds a route to the solution and updates totals and charger counts.

        Charging cost is only added when a charger is actually visited.
        """
        if not self.short_feasibility_check(route):
            raise ValueError("Route failed feasibility check and cannot be added.")

        self.routes.append(route)
        for i in range(len(route) - 1):
            from_loc = route[i]
            to_loc = route[i + 1]

            self.total_distance += self.instance.get_distance(from_loc, to_loc)
            self.total_time += self.instance.get_time(from_loc, to_loc)
            self.total_cost += self.instance.get_cost(from_loc, to_loc)

            # Add charging cost only if vehicle stops at a charger
            if self.instance.is_type(from_loc, 'charger'):
                self.total_cost += self.instance.get_charging_cost(from_loc)
                self.charging_stops[from_loc] += 1

    # ---------------------------
    # Solution-level methods
    # ---------------------------
    def all_loads_unloads_visited(self) -> bool:
        """Check if all loading and unloading points are visited in the solution."""
        visited = {loc for route in self.routes for loc in route}
        missing_loadings = [loc for loc in self.instance.loadings if loc not in visited]
        missing_unloadings = [loc for loc in self.instance.unloadings if loc not in visited]

        return not (missing_loadings or missing_unloadings)

    def short_feasibility_check(self, route: List[str]) -> bool:
        """
        Check route-level feasibility:
        1. Starts and ends at parking
        2. No loading after unloading
        Returns True if feasible, False otherwise.
        """
        if not route:
            print("Route is empty")
            self.short_feasibility_flag = False
            return False

        if not self.instance.is_type(route[0], 'parking'):
            print(f"Route does not start at a parking: {route[0]}")
            self.short_feasibility_flag = False
            return False

        if not self.instance.is_type(route[-1], 'parking'):
            print(f"Route does not end at a parking: {route[-1]}")
            self.short_feasibility_flag = False
            return False

        unloading_seen = False
        for loc in route:
            if self.instance.is_type(loc, 'unloading'):
                unloading_seen = True
            if unloading_seen and self.instance.is_type(loc, 'loading'):
                print(f"Route has loading after unloading: {loc}")
                self.short_feasibility_flag = False
                return False

        self.short_feasibility_flag = True
        return True

    def complete_feasibility(self) -> None:
        """
        Run all feasibility tests and update flags:
        - self.short_feasibility_flag: True if all routes pass route-level check
        - self.complete_feasibility_flag: True if all load/unload points visited
        """
        all_routes_ok = all(self.short_feasibility_check(r) for r in self.routes)
        self.short_feasibility_flag = all_routes_ok
        loads_unloads_ok = self.all_loads_unloads_visited()
        self.complete_feasibility_flag = all_routes_ok and loads_unloads_ok

    # ---------------------------
    # Persistence
    # ---------------------------
    def save(self, filepath: str) -> None:
        """
        Save the VRPSolution instance to a pickle file.

        :param filepath: Full path to the pickle file.
        """
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Solution saved to {filepath}")

    # ---------------------------
    # Plotting helpers
    # ---------------------------
    def offset_segment(self, p1: Tuple[float, float], p2: Tuple[float, float], offset: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Shift a segment perpendicular to its direction by 'offset' (latitude/longitude approximation).
        """
        lat1, lon1 = p1
        lat2, lon2 = p2

        dx = lon2 - lon1
        dy = lat2 - lat1
        length = math.hypot(dx, dy)
        if length == 0:
            return p1, p2

        px = -dy / length
        py = dx / length

        return (
            (lat1 + py * offset, lon1 + px * offset),
            (lat2 + py * offset, lon2 + px * offset),
        )

    def plot_vrp_solution(self, save_path: str = "vrp_solution.html") -> None:
        """
        Generate an HTML map with the VRP solution:
        - Routes offset to avoid overlapping lines
        - Different colors per vehicle
        - Nodes with icons per type
        """
        instance = self.instance

        # Map center
        all_lats = [loc["coords"][0] for loc in instance.locations.values()]
        all_lons = [loc["coords"][1] for loc in instance.locations.values()]
        map_center = [sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons)]
        m = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

        # Colors for routes
        colors = ["blue", "red", "green", "orange", "purple", "brown", "pink", "darkcyan"]
        OFFSET = 0.00035

        # Draw routes
        for idx, route in enumerate(self.routes):
            color = colors[idx % len(colors)]
            route_offset = (idx - len(self.routes) / 2) * OFFSET
            coords = []

            for i in range(len(route) - 1):
                p1 = instance.locations[route[i]]["coords"]
                p2 = instance.locations[route[i + 1]]["coords"]
                p1o, p2o = self.offset_segment(p1, p2, route_offset)
                if i == 0:
                    coords.append(p1o)
                coords.append(p2o)

            fg = folium.FeatureGroup(name=f"Route {idx + 1}")
            folium.PolyLine(locations=coords, color=color, weight=4, opacity=0.85).add_to(fg)
            fg.add_to(m)

        # Draw nodes
        ICONS = {
            "parking": ("green", "home"),
            "loading": ("blue", "arrow-up"),
            "unloading": ("red", "arrow-down"),
            "charger": ("orange", "bolt"),
        }
        nodes_fg = folium.FeatureGroup(name="Nodes")
        for loc_name, loc_data in instance.locations.items():
            lat, lon = loc_data["coords"]
            node_type = loc_data.get("node", "other")
            color, icon = ICONS.get(node_type, ("gray", "circle"))
            folium.Marker(
                location=(lat, lon),
                popup=f"{loc_name} ({node_type})",
                icon=folium.Icon(color=color, icon=icon, icon_color="white", prefix="fa"),
            ).add_to(nodes_fg)
        nodes_fg.add_to(m)

        folium.LayerControl().add_to(m)
        m.save(save_path)

    # ---------------------------
    # Representation
    # ---------------------------
    def __repr__(self) -> str:
        return (
            f"<VRPSolution: {len(self.routes)} routes, "
            f"total_distance={self.total_distance:.2f} km, "
            f"short_feasibility_flag={self.short_feasibility_flag}, "
            f"complete_feasibility_flag={self.complete_feasibility_flag}>"
        )
