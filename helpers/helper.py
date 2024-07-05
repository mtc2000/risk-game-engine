class Map:
    def __init__(self, vertices, edges, continents, continent_bonuses):
        self.vertices = vertices
        self.edges = edges
        self.continents = continents
        self.continent_bonuses = continent_bonuses



def create_map():
    vertices = {
        "ALASKA": 0,
        "ALBERTA": 1,
        "CENTRAL_AMERICA": 2,
        "EASTERN_US": 3,
        "GREENLAND": 4,
        "NORTHWEST_TERRITORY": 5,
        "ONTARIO": 6,
        "QUEBEC": 7,
        "WESTERN_US": 8,
        "GREAT_BRITAIN": 9,
        "ICELAND": 10,
        "NORTHERN_EUROPE": 11,
        "SCANDINAVIA": 12,
        "SOUTHERN_EUROPE": 13,
        "UKRAINE": 14,
        "WESTERN_EUROPE": 15,
        "AFGHANISTAN": 16,
        "CHINA": 17,
        "INDIA": 18,
        "IRKUTSK": 19,
        "JAPAN": 20,
        "KAMCHATKA": 21,
        "MIDDLE_EAST": 22,
        "MONGOLIA": 23,
        "SIAM": 24,
        "SIBERIA": 25,
        "URAL": 26,
        "YAKUTSK": 27,
        "ARGENTINA": 28,
        "BRAZIL": 29,
        "VENEZUELA": 30,
        "PERU": 31,
        "CONGO": 32,
        "EAST_AFRICA": 33,
        "EGYPT": 34,
        "MADAGASCAR": 35,
        "NORTH_AFRICA": 36,
        "SOUTH_AFRICA": 37,
        "EASTERN_AUSTRALIA": 38,
        "NEW_GUINEA": 39,
        "INDONESIA": 40,
        "WESTERN_AUSTRALIA": 41,
    }

    continents = {
        0 : [
                vertices["ALASKA"],
                vertices["ALBERTA"],
                vertices["CENTRAL_AMERICA"],
                vertices["EASTERN_US"],
                vertices["GREENLAND"],
                vertices["NORTHWEST_TERRITORY"],
                vertices["ONTARIO"],
                vertices["QUEBEC"],
                vertices["WESTERN_US"]
            ],
        1 : [
                vertices["GREAT_BRITAIN"],
                vertices["ICELAND"],
                vertices["NORTHERN_EUROPE"],
                vertices["SCANDINAVIA"],
                vertices["SOUTHERN_EUROPE"],
                vertices["UKRAINE"],
                vertices["WESTERN_EUROPE"],
            ],
        2 : [
                vertices["AFGHANISTAN"],
                vertices["CHINA"],
                vertices["INDIA"],
                vertices["IRKUTSK"],
                vertices["JAPAN"],
                vertices["KAMCHATKA"],
                vertices["MIDDLE_EAST"],
                vertices["MONGOLIA"],
                vertices["SIAM"],
                vertices["SIBERIA"],
                vertices["URAL"],
                vertices["YAKUTSK"],
            ],
        3: [
                vertices["ARGENTINA"],
                vertices["BRAZIL"],
                vertices["VENEZUELA"],
                vertices["PERU"],
            ],
        4: [
                vertices["CONGO"],
                vertices["EAST_AFRICA"],
                vertices["EGYPT"],
                vertices["MADAGASCAR"],
                vertices["NORTH_AFRICA"],
                vertices["SOUTH_AFRICA"]
            ],
        5: [
                vertices["EASTERN_AUSTRALIA"],
                vertices["NEW_GUINEA"],
                vertices["INDONESIA"],
                vertices["WESTERN_AUSTRALIA"],
            ],
    }

    continent_bonuses = {
        0 : 5,
        1 : 5,
        2 : 7,
        3 : 2,
        4 : 3,
        5 : 2,
    }

    edges = {
        vertices["ALASKA"]: [
            vertices["ALBERTA"],
            vertices["NORTHWEST_TERRITORY"],
            vertices["KAMCHATKA"],
        ],
        vertices["ALBERTA"]: [
            vertices["ONTARIO"],
            vertices["NORTHWEST_TERRITORY"],
            vertices["ALASKA"],
            vertices["WESTERN_US"],
        ],
        vertices["CENTRAL_AMERICA"]: [
            vertices["EASTERN_US"],
            vertices["WESTERN_US"],
            vertices["VENEZUELA"],
        ],
        vertices["EASTERN_US"]: [
            vertices["QUEBEC"],
            vertices["ONTARIO"],
            vertices["WESTERN_US"],
            vertices["CENTRAL_AMERICA"],
        ],
        vertices["GREENLAND"]: [
            vertices["NORTHWEST_TERRITORY"],
            vertices["ONTARIO"],
            vertices["QUEBEC"],
            vertices["ICELAND"],
        ],
        vertices["NORTHWEST_TERRITORY"]: [
            vertices["GREENLAND"],
            vertices["ALASKA"],
            vertices["ALBERTA"],
            vertices["ONTARIO"],
        ],
        vertices["ONTARIO"]: [
            vertices["QUEBEC"],
            vertices["GREENLAND"],
            vertices["NORTHWEST_TERRITORY"],
            vertices["ALBERTA"],
            vertices["WESTERN_US"],
            vertices["EASTERN_US"],
        ],
        vertices["QUEBEC"]: [
            vertices["GREENLAND"],
            vertices["ONTARIO"],
            vertices["EASTERN_US"],
        ],
        vertices["WESTERN_US"]: [
            vertices["EASTERN_US"],
            vertices["ONTARIO"],
            vertices["ALBERTA"],
            vertices["CENTRAL_AMERICA"],
        ],
        vertices["GREAT_BRITAIN"]: [
            vertices["NORTHERN_EUROPE"],
            vertices["SCANDINAVIA"],
            vertices["ICELAND"],
            vertices["WESTERN_EUROPE"],
        ],
        vertices["ICELAND"]: [
            vertices["SCANDINAVIA"],
            vertices["GREENLAND"],
            vertices["GREAT_BRITAIN"],
        ],
        vertices["NORTHERN_EUROPE"]: [
            vertices["UKRAINE"],
            vertices["SCANDINAVIA"],
            vertices["GREAT_BRITAIN"],
            vertices["WESTERN_EUROPE"],
            vertices["SOUTHERN_EUROPE"],
        ],
        vertices["SCANDINAVIA"]: [
            vertices["UKRAINE"],
            vertices["ICELAND"],
            vertices["GREAT_BRITAIN"],
            vertices["NORTHERN_EUROPE"],
        ],
        vertices["SOUTHERN_EUROPE"]: [
            vertices["MIDDLE_EAST"],
            vertices["UKRAINE"],
            vertices["NORTHERN_EUROPE"],
            vertices["WESTERN_EUROPE"],
            vertices["NORTH_AFRICA"],
            vertices["EGYPT"],
        ],
        vertices["UKRAINE"]: [
            vertices["AFGHANISTAN"],
            vertices["URAL"],
            vertices["SCANDINAVIA"],
            vertices["NORTHERN_EUROPE"],
            vertices["SOUTHERN_EUROPE"],
            vertices["MIDDLE_EAST"],
        ],
        vertices["WESTERN_EUROPE"]: [
            vertices["SOUTHERN_EUROPE"],
            vertices["NORTHERN_EUROPE"],
            vertices["GREAT_BRITAIN"],
            vertices["NORTH_AFRICA"],
        ],
        vertices["AFGHANISTAN"]: [
            vertices["CHINA"],
            vertices["URAL"],
            vertices["UKRAINE"],
            vertices["MIDDLE_EAST"],
            vertices["INDIA"],
        ],
        vertices["CHINA"]: [
            vertices["MONGOLIA"],
            vertices["SIBERIA"],
            vertices["URAL"],
            vertices["AFGHANISTAN"],
            vertices["INDIA"],
            vertices["SIAM"],
        ],
        vertices["INDIA"]: [
            vertices["SIAM"],
            vertices["CHINA"],
            vertices["AFGHANISTAN"],
            vertices["MIDDLE_EAST"],
        ],
        vertices["IRKUTSK"]: [
            vertices["KAMCHATKA"],
            vertices["YAKUTSK"],
            vertices["SIBERIA"],
            vertices["MONGOLIA"],
        ],
        vertices["JAPAN"]: [
            vertices["KAMCHATKA"],
            vertices["MONGOLIA"],
        ],
        vertices["KAMCHATKA"]: [
            vertices["ALASKA"],
            vertices["YAKUTSK"],
            vertices["IRKUTSK"],
            vertices["MONGOLIA"],
            vertices["JAPAN"],
        ],
        vertices["MIDDLE_EAST"]: [
            vertices["INDIA"],
            vertices["AFGHANISTAN"],
            vertices["UKRAINE"],
            vertices["SOUTHERN_EUROPE"],
            vertices["EGYPT"],
            vertices["EAST_AFRICA"],
        ],
        vertices["MONGOLIA"]: [
            vertices["JAPAN"],
            vertices["KAMCHATKA"],
            vertices["IRKUTSK"],
            vertices["SIBERIA"],
            vertices["CHINA"],
        ],
        vertices["SIAM"]: [
            vertices["CHINA"],
            vertices["INDIA"],
            vertices["INDONESIA"],
        ],
        vertices["SIBERIA"]: [
            vertices["YAKUTSK"],
            vertices["URAL"],
            vertices["CHINA"],
            vertices["MONGOLIA"],
            vertices["IRKUTSK"],
        ],
        vertices["URAL"]: [
            vertices["SIBERIA"],
            vertices["UKRAINE"],
            vertices["AFGHANISTAN"],
            vertices["CHINA"],
        ],
        vertices["YAKUTSK"]: [
            vertices["KAMCHATKA"],
            vertices["SIBERIA"],
            vertices["IRKUTSK"],
        ],
        vertices["ARGENTINA"]: [
            vertices["BRAZIL"],
            vertices["PERU"],
        ],
        vertices["BRAZIL"]: [
            vertices["NORTH_AFRICA"],
            vertices["VENEZUELA"],
            vertices["PERU"],
            vertices["ARGENTINA"],
        ],
        vertices["VENEZUELA"]: [
            vertices["CENTRAL_AMERICA"],
            vertices["PERU"],
            vertices["BRAZIL"],
        ],
        vertices["PERU"]: [
            vertices["BRAZIL"],
            vertices["VENEZUELA"],
            vertices["ARGENTINA"],
        ],
        vertices["CONGO"]: [
            vertices["EAST_AFRICA"],
            vertices["NORTH_AFRICA"],
            vertices["SOUTH_AFRICA"],
        ],
        vertices["EAST_AFRICA"]: [
            vertices["MIDDLE_EAST"],
            vertices["EGYPT"],
            vertices["NORTH_AFRICA"],
            vertices["CONGO"],
            vertices["SOUTH_AFRICA"],
            vertices["MADAGASCAR"],
        ],
        vertices["EGYPT"]: [
            vertices["MIDDLE_EAST"],
            vertices["SOUTHERN_EUROPE"],
            vertices["NORTH_AFRICA"],
            vertices["EAST_AFRICA"],
        ],
        vertices["MADAGASCAR"]: [
            vertices["EAST_AFRICA"],
            vertices["SOUTH_AFRICA"],
        ],
        vertices["NORTH_AFRICA"]: [
            vertices["EAST_AFRICA"],
            vertices["EGYPT"],
            vertices["SOUTHERN_EUROPE"],
            vertices["WESTERN_EUROPE"],
            vertices["BRAZIL"],
            vertices["CONGO"],
        ],
        vertices["SOUTH_AFRICA"]: [
            vertices["MADAGASCAR"],
            vertices["EAST_AFRICA"],
            vertices["CONGO"],
        ],
        vertices["EASTERN_AUSTRALIA"]: [
            vertices["NEW_GUINEA"],
            vertices["WESTERN_AUSTRALIA"],
        ],
        vertices["NEW_GUINEA"]: [
            vertices["INDONESIA"],
            vertices["WESTERN_AUSTRALIA"],
            vertices["EASTERN_AUSTRALIA"],
        ],
        vertices["INDONESIA"]: [
            vertices["NEW_GUINEA"],
            vertices["SIAM"],
            vertices["WESTERN_AUSTRALIA"],
        ],
        vertices["WESTERN_AUSTRALIA"]: [
            vertices["EASTERN_AUSTRALIA"],
            vertices["NEW_GUINEA"],
            vertices["INDONESIA"],
        ],
    }

    return Map(vertices=vertices, edges=edges, continents=continents, continent_bonuses=continent_bonuses)

def create_priority_list(map):
    # Calculate priority scores
    priority_scores = {}
    
    for territory, vertex_id in map.vertices.items():
        continent = next(cont for cont, verts in map.continents.items() if vertex_id in verts)
        num_borders = len(map.edges[vertex_id])
        is_border = vertex_id in [edge for cont in map.continents.values() for edge in cont if edge in map.edges and any(v not in cont for v in map.edges[edge])]
        
        # Calculate the score based on continent bonus, number of borders, and border status
        score = (map.continent_bonuses[continent] * 10) - (num_borders * 2)
        if is_border:
            score += 5  # Additional weight for border territories
        
        priority_scores[territory] = score
    
    sorted_territories = sorted(priority_scores.items(), key=lambda item: item[1], reverse=True)
    sorted_territories_id = [map.vertices[territory[0]] for territory in sorted_territories]
    print(sorted_territories_id)
    
    return [territory[0] for territory in sorted_territories]

def create_priority_list_early(map):
    # Adjust weights based on early game strategy
    early_continent_priority = {
        3: 10,  # South America
        4: 8,   # Africa
        5: 6,   # Australia
        0: 4,   # North America
        1: 2,   # Europe
        2: 1,   # Asia
    }
    
    priority_scores = {}
    
    for territory, vertex_id in map.vertices.items():
        # Determine the continent for the current territory
        continent = next(cont for cont, verts in map.continents.items() if vertex_id in verts)
        num_borders = len(map.edges[vertex_id])
        
        # Calculate the score based on early continent priority and number of borders
        score = early_continent_priority[continent] * 10 - num_borders
        
        priority_scores[territory] = score
    
    # Sort territories by score in descending order (higher scored territories first)
    sorted_territories = sorted(priority_scores.items(), key=lambda item: item[1], reverse=True)
    sorted_territories_id = [map.vertices[territory[0]] for territory in sorted_territories]
    print(sorted_territories_id)
    
    return [territory[0] for territory in sorted_territories]

# Example usage
risk_map = create_map()
priority_list = create_priority_list_early(risk_map)
print('Priority list for initial map distribution:', priority_list)
