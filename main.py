from src.vrp_instance import VRPInstance
from src.vrp_solution import VRPSolution
from src.algorithm.exact_model import exact_model
from src.algorithm.nearest_neighbour import nearest_neighbour
from src.algorithm.two_opt import two_opt
import folium as folium
from folium.plugins import MarkerCluster
import pickle
from pathlib import Path
import time
import os
import pandas as pd

# Creamos una lista de diccionarios
summary_results = []

dataset_folder = Path('/Users/nataliaalvareztejero/Desktop/CLASE/MASTER/SEGUNDO/Truckster/camion_electrico/datasets/')
results_folder = Path('/Users/nataliaalvareztejero/Desktop/CLASE/MASTER/SEGUNDO/Truckster/camion_electrico/results/')
csv_file = results_folder / 'solutions_metadata.csv'

# Iterate over all pickle files in the folder
for pkl_file in dataset_folder.glob('*.pkl'):
    
    print(f'Processing {pkl_file.name}')

    # Load dataset
    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)

    # Create VRP instance
    instance = VRPInstance(
        locations=data['locations'],
        distance_matrix=data['distance_matrix'],
        time_matrix=data['time_matrix'],
        charging_costs=data['chargin_cost'],  # verify spelling
        cost_matrix=data['cost_matrix']
    )
    instance.plot_vrp_instance_default_icons(
        save_path=os.path.join(dataset_folder, pkl_file.stem + '_instance.html')
    )

    # Solve using exact_model and measure execution time
    start_time = time.perf_counter()
    solution = exact_model(instance)
    exec_time = time.perf_counter() - start_time
    # Save solution pickle
    solution.execution_time = exec_time
    solution.save(
        filepath = os.path.join(results_folder, 'gurobi', pkl_file.stem + '_solution.pkl')
        )
    solution.plot_vrp_solution(
                               save_path=os.path.join(results_folder, 'gurobi', pkl_file.stem + '_solution.html')
                               )

    summary_results.append({
        'instance_name': pkl_file.stem,
        'algorithm': 'gurobi',
        'execution_time': exec_time,
        'cost': solution.total_cost
    })

    # Solve using nearest_neighbour and measure execution time        
    start_time = time.perf_counter()
    solution = nearest_neighbour(instance)
    exec_time = time.perf_counter() - start_time

    # Save solution pickle
    solution.execution_time = exec_time
    solution.save(
        filepath = os.path.join(results_folder, 'nearest_neighbour', pkl_file.stem + '_solution.pkl')
        )
    solution.plot_vrp_solution(save_path=os.path.join(results_folder, 'nearest_neighbour', pkl_file.stem + '_solution.html'))


    summary_results.append({
        'instance_name': pkl_file.stem,
        'algorithm': 'nearest_neighbour',
        'execution_time': exec_time,
        'cost': solution.total_cost
    })

    # Solve using 2-opt and measure execution time        
    start_time = time.perf_counter()
    solution = two_opt(solution)
    exec_time = time.perf_counter() - start_time

    # Save solution pickle
    solution.execution_time = exec_time
    solution.save(
        filepath = os.path.join(results_folder, 'two_opt', pkl_file.stem + '_solution.pkl')
        )
    solution.plot_vrp_solution(save_path=os.path.join(results_folder, 'two_opt', pkl_file.stem + '_solution.html'))

    summary_results.append({
        'instance_name': pkl_file.stem,
        'algorithm': 'two_opt',
        'execution_time': exec_time,
        'cost': solution.total_cost
    })


# Convertimos a DataFrame
df = pd.DataFrame(summary_results)
print(df)
df.to_csv("/Users/nataliaalvareztejero/Desktop/CLASE/MASTER/SEGUNDO/Truckster/camion_electrico/resultados.csv", index=False, encoding="utf-8")


