import pickle
import random
from pathlib import Path
from geopy.distance import geodesic
import re

# ---------- CONSTANTS ----------
FIXED_LOCATIONS = [
    {'node': 'parking', 'name': 'ES08191 Rubi', 'coords': (41.46930679260032, 2.029808746545829)},
    {'node': 'unloading', 'name': 'ES08040 Barcelona', 'coords': (41.325060, 2.141684)},
    {'node': 'charger', 'name': 'IONITY Palleja', 'coords': (41.420342, 2.001644)}, 
    {'node': 'charger', 'name': 'IONITY Barcera del Valles', 'coords': (41.51182358577195, 2.1345502627626303)},
    {'node': 'charger', 'name': 'IONITY Montcada i Reixac', 'coords': (41.491422605263075, 2.1823508377517684)},
    {'node': 'charger', 'name': 'Atlante - Nieves Zona Franca', 'coords': (41.33194049366559, 2.134952349708804)},
    {'node': 'charger', 'name': 'Atlante - Atlante - Nieves Sant Esteve', 'coords': (41.504070650751906, 1.883253906745552)},
]

VARIABLE_LOCATIONS = [
    {'node': 'loading', 'name': 'ES08840 Viladecans', 'coords': (41.319512, 2.031505)},
    {'node': 'loading', 'name': 'ES08272 Sant Fruitós de Bages', 'coords': (41.77803590470732, 1.867141253552206)},    
    {'node': 'loading', 'name': 'ES08650 Sallent', 'coords': (41.60289038509304, 2.2569771240231096)},    
    {'node': 'loading', 'name': 'ES8739 Casablanca', 'coords': (41.42833, 1.819261)},
    {'node': 'loading', 'name': 'ES8170 Montornès del Vallès', 'coords': (41.5573862, 2.2609581)},    
    {'node': 'loading', 'name': 'ES8755 Castellbisbal', 'coords': (41.45037, 1.979796)},    
    {'node': 'loading', 'name': 'ES8130 Santa Perpètua de Mogoda', 'coords': (41.53960, 2.183749)},    
    {'node': 'loading', 'name': 'ES8755 Castellbisbal 2', 'coords': (41.4680828, 1.9515915)},
    {'node': 'loading', 'name': 'ES8740 Sant Andreu de la Barca', 'coords': (41.44667, 1.983210)},    
    {'node': 'loading', 'name': 'ES08186 Lliça de Amunt', 'coords': (41.60827, 2.239330)}
]

PRICE_IONITY = 0.61
PRICE_ATLANTE = 0.64
KWH = 300
PRICE_PER_KM = 0.623
AVERAGE_SPEED_KMH = 70

# ---------- FUNCTIONS ----------
def calculate_distance_matrix(locations):
    """Distance matrix with location names as keys."""

    matrix = {}
    
    for loc_i in locations:
        for loc_j in locations:
            if loc_i['name'] == loc_j['name']:
                matrix[loc_i['name'],loc_j['name']] = 0
            else:
                coord_i = loc_i['coords']
                coord_j = loc_j['coords']
                if coord_i and coord_j:
                    matrix[loc_i['name'], loc_j['name']] = round(geodesic(coord_i, coord_j).km, 2)
                    matrix[loc_j['name'], loc_i['name']] = round(geodesic(coord_i, coord_j).km, 2)
                else:
                    matrix[loc_i['name'],loc_j['name']] = None
                    matrix[loc_j['name'],loc_i['name']] = None
    return matrix

def calculate_time_matrix(distance_matrix, speed_kmh=AVERAGE_SPEED_KMH):
    """Time matrix in minutes using named indices."""
    matrix = {}
    for key in distance_matrix.keys():
        matrix[key] = round(distance_matrix[key] / speed_kmh * 60, 2)
    return matrix

def calculate_charging_cost_vector(locations):
    """Vector of charging costs w."""
    w = {}
    for loc in locations:
        if re.search("IONITY", loc["name"], re.IGNORECASE):
            w[loc['name']] = round(KWH * PRICE_IONITY, 2)
        elif re.search("Atlante", loc["name"], re.IGNORECASE):
            w[loc['name']] = round(KWH * PRICE_ATLANTE, 2)
        else:
            w[loc['name']] = 0
    return w

def calculate_cost_matrix(distance_matrix, price_per_km=PRICE_PER_KM):
    """Cost matrix using named indices."""
    matrix = {}
    for key in distance_matrix.keys():
        matrix[key] = round(distance_matrix[key] * price_per_km, 2)
    return matrix

def generate_datasets(fixed_locations, variable_locations,
                      min_size=3, max_size=9, samples_per_size=3,
                      output_folder="datasets"):
    """Generate EV datasets with named matrices."""
    Path(output_folder).mkdir(exist_ok=True)

    print(f"Generating datasets in folder: {output_folder}")

    for size in range(min_size, max_size+1):
        existing_combinations = set()  # keep track of already used combinations
        
        for sample in range(1, samples_per_size + 1):
            tries = 0
            while True:
                tries += 1
                selected_variable = random.sample(variable_locations, size)
                names_set = frozenset(loc['name'] for loc in selected_variable)
                
                if names_set not in existing_combinations or tries > 50:
                    break
            
            existing_combinations.add(names_set)
            
            dataset_locations = fixed_locations + selected_variable
            
            distance_matrix = calculate_distance_matrix(dataset_locations)
            time_matrix = calculate_time_matrix(distance_matrix)
            chargin_cost = calculate_charging_cost_vector(dataset_locations)
            cost_matrix = calculate_cost_matrix(distance_matrix)
            
            dataset = {
                "locations": {loc['name']: loc for loc in dataset_locations},
                "distance_matrix": distance_matrix,
                "time_matrix": time_matrix,
                "chargin_cost": chargin_cost,
                "cost_matrix": cost_matrix
            }
            
            filename = f"{output_folder}/dataset_size{size}_{sample}.pkl"
            print(f"Writing dataset to {filename}...")
            with open(filename, "wb") as f:
                pickle.dump(dataset, f)
            print(f"Generated: {filename}")
            
# ---------- RUN ----------
generate_datasets(FIXED_LOCATIONS, VARIABLE_LOCATIONS)

