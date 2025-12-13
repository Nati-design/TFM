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
    {'node': 'loading', 'name': '08020 -  Barcelona'	, 'coords': (41.4302546	,2.2040522)},
    {'node': 'loading', 'name': '08020 -  El Prat de Llobregat'	, 'coords': (41.31422670000001	,2.1364696)},
    {'node': 'loading', 'name': '08021 -  Barcelona'	, 'coords': (41.397617	,2.1413415)},
    {'node': 'loading', 'name': '08029 -  Barcelona'	, 'coords': (41.384183	,2.145430799999999)},
    {'node': 'loading', 'name': '08033 -  Barcelona'	, 'coords': (41.4528007	,2.1962535)},
    {'node': 'loading', 'name': '08038 -  Barcelona'	, 'coords': (41.3624928	,2.1401013)},
    {'node': 'loading', 'name': '08039 -  Barcelona'	, 'coords': (41.3451957	,2.1502652)},
    {'node': 'loading', 'name': '08040 -  Barcelona'	, 'coords': (41.32251239999999	,2.1381923)},
    {'node': 'loading', 'name': '08100 -  Mollet del Vallès'	, 'coords': (41.53608150000001	,2.2220117)},
    {'node': 'loading', 'name': '08105 -  Barcelona'	, 'coords': (41.5283298	,2.2229068)},
    {'node': 'loading', 'name': '08105 -  Sant Fost de Campsentelles'	, 'coords': (41.5263456	,2.2223639)},
    {'node': 'loading', 'name': '08107 -  Barcelona'	, 'coords': (41.532788	,2.236171)},
    {'node': 'loading', 'name': '08107 -  Martorelles'	, 'coords': (41.53310159999999	,2.2284628)},
    {'node': 'loading', 'name': '08110 -  Moncada y Reixach'	, 'coords': (41.4891833	,2.1798573)},
    {'node': 'loading', 'name': '08110 -  Montcada i Reixac'	, 'coords': (41.4896656	,2.1732027)},
    {'node': 'loading', 'name': '08120 -  La Llagosta'	, 'coords': (41.5142572	,2.2020062)},
    {'node': 'loading', 'name': '08130 -  Barcelona'	, 'coords': (41.5387018	,2.1780299)},
    {'node': 'loading', 'name': '08130 -  Santa Perpètua de Mogoda'	, 'coords': (41.5329649	,2.1942534)},
    {'node': 'loading', 'name': '08130 -  Santa Perpetua de moguda'	, 'coords': (41.53233809999999	,2.1957663)},
    {'node': 'loading', 'name': '08140 -  Barcelona'	, 'coords': (41.629631	,2.1782569)},
    {'node': 'loading', 'name': '08150 -  Barcelona'	, 'coords': (41.5530014	,2.2361474)},
    {'node': 'loading', 'name': '08150 -  Parets del Vallés'	, 'coords': (41.5713433	,2.246509)},
    {'node': 'loading', 'name': '08150 -  Parets del Vallès'	, 'coords': (41.5521138	,2.2358454)},
    {'node': 'loading', 'name': '08160 -  Barcelona'	, 'coords': (41.5478975	,2.255087)},
    {'node': 'loading', 'name': '08160 -  Montmeló'	, 'coords': (41.5553124	,2.2574973)},
    {'node': 'loading', 'name': '08170 -  Montornès del Vallès'	, 'coords': (41.5427877	,2.2402156)},
    {'node': 'loading', 'name': '08170 -  Montornès del Vallès, Barcelona'	, 'coords': (41.5417126	,2.2368123)},
    {'node': 'loading', 'name': '08174 -  Sant Cugat del Vallès'	, 'coords': (41.48723709999999	,2.0502636)},
    {'node': 'loading', 'name': '08181 -  Sentmenat'	, 'coords': (41.61493	,2.1401212)},
    {'node': 'loading', 'name': '08184 -  Palau de Plegamans'	, 'coords': (41.5721774	,2.1741112)},
    {'node': 'loading', 'name': '08184 -  Palau-solità i Plegamans'	, 'coords': (41.5630363	,2.1796268)},
    {'node': 'loading', 'name': '08185 -  Lliçà de Vall'	, 'coords': (41.583538	,2.2428925)},
    {'node': 'loading', 'name': '08186 -  Barcelona'	, 'coords': (41.60058799999999	,2.2543248)},
    {'node': 'loading', 'name': '08186 -  Lliçà dAmunt'	, 'coords': (41.60008730000001	,2.2546087)},
    {'node': 'loading', 'name': '08191 -  Rubí'	, 'coords': (41.463355	,2.006648600000001)},
    {'node': 'loading', 'name': '08192 -  Sabadell'	, 'coords': (41.5332105	,2.0986784)},
    {'node': 'loading', 'name': '08192 -  San Quirico del Vallés'	, 'coords': (41.5373203	,2.0930336)},
    {'node': 'loading', 'name': '08192 -  Sant Quirze del Vallès'	, 'coords': (41.5249202	,2.0917022)},
    {'node': 'loading', 'name': '08197 -  Badalona'	, 'coords': (41.45648920000001	,2.2277434)},
    {'node': 'loading', 'name': '08202 -  Sabadell'	, 'coords': (41.5360568	,2.1335997)},
    {'node': 'loading', 'name': '08203 -  Sabadell'	, 'coords': (41.5326917	,2.1105682)},
    {'node': 'loading', 'name': '08205 -  Sabadell'	, 'coords': (41.5122087	,2.1035824)},
    {'node': 'loading', 'name': '08210 -  Barberà del Vallès'	, 'coords': (41.51551419999999	,2.1536586)},
    {'node': 'loading', 'name': '08210 -  Barcelona'	, 'coords': (41.5178429	,2.1453861)},
    {'node': 'loading', 'name': '08210 -  Sabadell'	, 'coords': (41.5326019	,2.1328531)},
    {'node': 'loading', 'name': '08211 -  Castellar del Vallès'	, 'coords': (41.5909932	,2.0925553)},
    {'node': 'loading', 'name': '08213 -  Polinyà'	, 'coords': (41.5409891	,2.1631942)},
    {'node': 'loading', 'name': '08224 -  Terrassa'	, 'coords': (41.545267	,2.011013)},
    {'node': 'loading', 'name': '08227 -  Terrassa'	, 'coords': (41.5467888	,2.0428639)},
    {'node': 'loading', 'name': '08228 -  Terrassa'	, 'coords': (41.535	,2.03225)},
    {'node': 'loading', 'name': '08231 -  Barcelona'	, 'coords': (41.5176052	,1.9539851)},
    {'node': 'loading', 'name': '08232 -  Viladecavalls'	, 'coords': (41.5614681	,1.977750400000001)},
    {'node': 'loading', 'name': '08233 -  Vacarisses'	, 'coords': (41.5942125	,1.9132165)},
    {'node': 'loading', 'name': '08243 -  Manresa'	, 'coords': (41.7390192	,1.8488473)},
    {'node': 'loading', 'name': '08251 -  Santpedor'	, 'coords': (41.7758347	,1.8519902)},
    {'node': 'loading', 'name': '08272 -  San Fructuoso de Bages'	, 'coords': (41.7644996	,1.900823100000001)},
    {'node': 'loading', 'name': '08272 -  Sant Fruitós de Bages'	, 'coords': (41.7644996	,1.900823100000001)},
    {'node': 'loading', 'name': '08290 -  Barcelona'	, 'coords': (41.503435	,2.126708)},
    {'node': 'loading', 'name': '08290 -  Cerdanyola del Vallès'	, 'coords': (41.4849832	,2.1240103)},
    {'node': 'loading', 'name': '08291 -  Barcelona'	, 'coords': (41.5100696	,2.1487813)},
    {'node': 'loading', 'name': '08291 -  Ripollet'	, 'coords': (41.491089	,2.168863)},
    {'node': 'loading', 'name': '08292 -  Esparraguera'	, 'coords': (41.52908399999999	,1.868341)},
    {'node': 'loading', 'name': '08292 -  Esparreguera'	, 'coords': (41.5454532	,1.8594949)},
    {'node': 'loading', 'name': '08295 -  Sant Vicenç de Castellet'	, 'coords': (41.6565259	,1.8565696)},
    {'node': 'loading', 'name': '08302 -  Mataró'	, 'coords': (41.5219981	,2.4257231)},
    {'node': 'loading', 'name': '08380 -  Malgrat de Mar'	, 'coords': (41.649923759213294	,2.7516889572143555)},
    {'node': 'loading', 'name': '08389 -  Palafolls'	, 'coords': (41.6881558	,2.7329239)},
    {'node': 'loading', 'name': '08401 -  Granollers'	, 'coords': (41.59595849999999	,2.2803173)},
    {'node': 'loading', 'name': '08402 -  Barcelona'	, 'coords': (41.5695466	,2.2665082)},
    {'node': 'loading', 'name': '08402 -  Granollers'	, 'coords': (41.5898376	,2.2736586)},
    {'node': 'loading', 'name': '08403 -  Granollers'	, 'coords': (41.5844901	,2.2726569)},
    {'node': 'loading', 'name': '08430 -  La Roca del Vallès'	, 'coords': (41.59530599999999	,2.3045285)},
    {'node': 'loading', 'name': '08450 -  Barcelona'	, 'coords': (41.605766	,2.384151)},
    {'node': 'loading', 'name': '08450 -  Llinars del Vallès'	, 'coords': (41.6275163	,2.3746621)},
    {'node': 'loading', 'name': '08459 -  Sant Antoni de Vilamajor'	, 'coords': (41.64717479999999	,2.412446699999999)},
    {'node': 'loading', 'name': '08470 -  Sant Celoni'	, 'coords': (41.6763091	,2.4857268)},
    {'node': 'loading', 'name': '08471 -  Vallgorguina'	, 'coords': (41.6699821	,2.4791803)},
    {'node': 'loading', 'name': '08480 -  LAmetlla del Vallès'	, 'coords': (41.64926819999999	,2.2726776)},
    {'node': 'loading', 'name': '08490 -  Tordera'	, 'coords': (41.692346	,2.732659)},
    {'node': 'loading', 'name': '08496 -  Fogars de la Selva'	, 'coords': (41.7413902	,2.6577626)},
    {'node': 'loading', 'name': '08500 -  Vic'	, 'coords': (41.94651040000001	,2.2843117)},
    {'node': 'loading', 'name': '08503 -  Gurb'	, 'coords': (41.9478657	,2.244844000000001)},
    {'node': 'loading', 'name': '08504 -  Sant Julià de Vilatorta'	, 'coords': (41.91733259999999	,2.3135184)},
    {'node': 'loading', 'name': '08520 -  Barcelona'	, 'coords': (41.63716540000001	,2.2885112)},
    {'node': 'loading', 'name': '08520 -  Canovelles'	, 'coords': (41.6421148	,2.2855555)},
    {'node': 'loading', 'name': '08520 -  Granollers'	, 'coords': (41.64084249999999	,2.286344799999999)},
    {'node': 'loading', 'name': '08520 Les Franqueses del Valles -  Barcelona'	, 'coords': (41.64782750000001	,2.3123031)},
    {'node': 'loading', 'name': '08550 -  Els Hostalets de Balenyà'	, 'coords': (41.837714	,2.234626)},
    {'node': 'loading', 'name': '08550 -  Sant Miquel de Balenyà'	, 'coords': (41.8424748	,2.2458771)},
    {'node': 'loading', 'name': '08560 -  Manlleu'	, 'coords': (42.00669999999999	,2.29583)},
    {'node': 'loading', 'name': '08620 -  Sant Vicenç dels Horts'	, 'coords': (41.3836669	,2.0044643)},
    {'node': 'loading', 'name': '08630 -  Abrera'	, 'coords': (41.5069548	,1.8969394)},
    {'node': 'loading', 'name': '08635 -  Abrera'	, 'coords': (41.5081545	,1.8922449)},
    {'node': 'loading', 'name': '08635 -  San Esteban de Sasroviras'	, 'coords': (41.4678123	,1.8795263)},
    {'node': 'loading', 'name': '08635 -  Sant Esteve Sesrovires'	, 'coords': (41.4646888	,1.8757697)},
    {'node': 'loading', 'name': '08650 -  Cabrianes'	, 'coords': (41.7889542	,1.9082042)},
    {'node': 'loading', 'name': '08650 -  Sallent'	, 'coords': (41.78153859999999	,1.8958142)},
    {'node': 'loading', 'name': '08700 -  Igualada'	, 'coords': (41.5963697	,1.6275449)},
    {'node': 'loading', 'name': '08711 -  Òdena'	, 'coords': (41.5776975	,1.6542844)},
    {'node': 'loading', 'name': '08720 -  Vilafranca del Penedès'	, 'coords': (41.3311601	,1.6703638)},
    {'node': 'loading', 'name': '08729 -  Barcelona'	, 'coords': (41.25383300000001	,1.5806526)},
    {'node': 'loading', 'name': '08730 -  Barcelona'	, 'coords': (41.3088987	,1.6546415)},
    {'node': 'loading', 'name': '08734 -  Barcelona'	, 'coords': (41.35772989999999	,1.73245)},
    {'node': 'loading', 'name': '08735 -  Barcelona'	, 'coords': (41.3975542	,1.6604322)},
    {'node': 'loading', 'name': '08737 -  Torrelles de Foix'	, 'coords': (41.3835639	,1.5805016)},
    {'node': 'loading', 'name': '08739 -  Barcelona'	, 'coords': (41.4026006	,1.7625759)},
    {'node': 'loading', 'name': '08740 -  Sant Andreu de la Barca'	, 'coords': (41.4604856	,1.9699415)},
    {'node': 'loading', 'name': '08750 -  Molins de Rei'	, 'coords': (41.3984819	,2.028467)},
    {'node': 'loading', 'name': '08755 -  Barcelona'	, 'coords': (41.46595	,1.9557043)},
    {'node': 'loading', 'name': '08755 -  Castellbisbal'	, 'coords': (41.44180679999999	,1.9902515)},
    {'node': 'loading', 'name': '08758 -  Cervelló'	, 'coords': (41.3996644	,1.97378)},
    {'node': 'loading', 'name': '08759 -  Barcelona'	, 'coords': (41.3753468	,1.9122118)},
    {'node': 'loading', 'name': '08760 -  Barcelona'	, 'coords': (41.4882733	,1.905053399999999)},
    {'node': 'loading', 'name': '08760 -  Martorell'	, 'coords': (41.4850611	,1.9233214)},
    {'node': 'loading', 'name': '08770 -  Barcelona'	, 'coords': (41.42433339999999	,1.7721231)},
    {'node': 'loading', 'name': '08770 -  Sant Sadurní dAnoia'	, 'coords': (41.4314699	,1.8037745)},
    {'node': 'loading', 'name': '08773 -  Sant Joan de Mediona'	, 'coords': (41.48352149999999	,1.603908)},
    {'node': 'loading', 'name': '08777 -  Sant Quintí de Mediona'	, 'coords': (41.462869	,1.6635606)},
    {'node': 'loading', 'name': '08783 -  Masquefa'	, 'coords': (41.480554	,1.803655)},
    {'node': 'loading', 'name': '08784 -  Barcelona'	, 'coords': (41.50039779999999	,1.7229223)},
    {'node': 'loading', 'name': '08784 -  Piera'	, 'coords': (41.5278612	,1.7479431)},
    {'node': 'loading', 'name': '08785 -  Vallbona dAnoia'	, 'coords': (41.5129138	,1.7054756)},
    {'node': 'loading', 'name': '08787 -  Barcelona'	, 'coords': (41.5688852	,1.6703585)},
    {'node': 'loading', 'name': '08787 -  La Pobla de Claramunt'	, 'coords': (41.565226	,1.6676806)},
    {'node': 'loading', 'name': '08790 -  Gelida'	, 'coords': (41.44721450000001	,1.8698797)},
    {'node': 'loading', 'name': '08791 -  San Juan Samora'	, 'coords': (41.4671831	,1.8798745)},
    {'node': 'loading', 'name': '08792 -  Barcelona'	, 'coords': (41.38001999999999	,1.713261)},
    {'node': 'loading', 'name': '08796 -  Barcelona'	, 'coords': (41.3651317	,1.6753478)},
    {'node': 'loading', 'name': '08796 -  Pacs del Penedès'	, 'coords': (41.3651311	,1.6752607)},
    {'node': 'loading', 'name': '08799 -  Olèrdola'	, 'coords': (41.35600629999999	,1.7407276)},
    {'node': 'loading', 'name': '08799 -  San Pedro Molanta'	, 'coords': (41.3548402	,1.7298103)},
    {'node': 'loading', 'name': '08799 -  Vilafranca del Penedès'	, 'coords': (41.3521166	,1.7274228)},
    {'node': 'loading', 'name': '08800 -  Vilanova i la Geltrú'	, 'coords': (41.2225092	,1.741144)},
    {'node': 'loading', 'name': '08800 -  Villanueva y Geltrú'	, 'coords': (41.24773139999999	,1.708469899999999)},
    {'node': 'loading', 'name': '08810 -  Sant Pere de Ribes'	, 'coords': (41.25754919999999	,1.7614309)},
    {'node': 'loading', 'name': '08820 -  Barcelona'	, 'coords': (41.31402	,2.13896)},
    {'node': 'loading', 'name': '08820 -  El Prat de Llobregat'	, 'coords': (41.2980651	,2.0617465)},
    {'node': 'loading', 'name': '08820 -  EL PRAT DE LLOBREGAT'	, 'coords': (41.3260389	,2.0315625)},
    {'node': 'loading', 'name': '08830 -  Sant Boi de Llobregat'	, 'coords': (41.29977539999999	,2.0574591)},
    {'node': 'loading', 'name': '08840 -  Barcelona'	, 'coords': (41.3037137	,2.0195406)},
    {'node': 'loading', 'name': '08840 -  Viladecans'	, 'coords': (41.3207889	,2.0300121)},
    {'node': 'loading', 'name': '08850 -  Barcelona'	, 'coords': (41.2941454	,2.0169223)},
    {'node': 'loading', 'name': '08850 -  Gavà'	, 'coords': (41.2979249	,2.0161806)},
    {'node': 'loading', 'name': '08907 -  LHospitalet de Llobregat'	, 'coords': (41.3504229	,2.1033222)},
    {'node': 'loading', 'name': '08908 -  LHospitalet de Llobregat'	, 'coords': (41.3432483	,2.11)},
    {'node': 'loading', 'name': '08911 -  Badalona'	, 'coords': (41.461731	,2.265106)},
    {'node': 'loading', 'name': '08924 -  Santa Coloma de Gramenet'	, 'coords': (41.4587202	,2.1933917)},
    {'node': 'loading', 'name': '08940 -  Cornellà de Llobregat'	, 'coords': (41.3478666	,2.0882713)}
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
                      min_size=3, max_size=9, samples_per_size=10,
                      output_folder="datasets"):
    """Generate EV datasets with named matrices."""
    Path(output_folder).mkdir(exist_ok=True)

    print(f"Generating datasets in folder: {output_folder}")

    for size in [25, 50, 75, 100]:
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

