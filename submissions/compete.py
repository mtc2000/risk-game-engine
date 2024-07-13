from collections import defaultdict, deque
import random
import numpy as np
from typing import Optional, Tuple, Union, cast
from typing import List, Dict, Optional, Union
from risk_helper.game import Game
from risk_shared.models.card_model import CardModel
from risk_shared.queries.query_attack import QueryAttack
from risk_shared.queries.query_claim_territory import QueryClaimTerritory
from risk_shared.queries.query_defend import QueryDefend
from risk_shared.queries.query_distribute_troops import QueryDistributeTroops
from risk_shared.queries.query_fortify import QueryFortify
from risk_shared.queries.query_place_initial_troop import QueryPlaceInitialTroop
from risk_shared.queries.query_redeem_cards import QueryRedeemCards
from risk_shared.queries.query_troops_after_attack import QueryTroopsAfterAttack
from risk_shared.queries.query_type import QueryType
from risk_shared.records.moves.move_attack import MoveAttack
from risk_shared.records.moves.move_attack_pass import MoveAttackPass
from risk_shared.records.moves.move_claim_territory import MoveClaimTerritory
from risk_shared.records.moves.move_defend import MoveDefend
from risk_shared.records.moves.move_distribute_troops import MoveDistributeTroops
from risk_shared.records.moves.move_fortify import MoveFortify
from risk_shared.records.moves.move_fortify_pass import MoveFortifyPass
from risk_shared.records.moves.move_place_initial_troop import MovePlaceInitialTroop
from risk_shared.records.moves.move_redeem_cards import MoveRedeemCards
from risk_shared.records.moves.move_troops_after_attack import MoveTroopsAfterAttack
from risk_shared.records.record_attack import RecordAttack
from risk_shared.records.types.move_type import MoveType
from math import floor

# We will store our enemy in the bot state.
class BotState():
    def __init__(self):
        self.enemy: Optional[int] = None


def main():
    
    # Get the game object, which will connect you to the engine and
    # track the state of the game.
    game = Game()
    bot_state = BotState()
    
    # conquer the continent; 2: attack the weakest player to try eliminate
    # 进攻策略
    # + 是否进攻？ 如果损失不大，进攻拿卡
    # + 进攻优先级： 一波推 > 占领完整大陆 > 破坏完整大陆 > 其他
    
    # 在部署兵力阶段判断我们的进攻模式。
    # 部署模式第一轮我们可以直接判断需要部署兵力的所有格子以及相对应的兵力数量 -> 在第一轮产生一个队列并在之后的query执行

    # 进攻模式汇总: no_attack, conquer_continent, attack_weakest, harrass_continent
    
    glb = {
        "attack_mode": "", # attack_mode = "", "conquer_continent", "harrass_weakest", "try_eliminate", "try_escape"
        "weights": {
            "First to play": 13.38,
            "Second to play": 5.35,
            "uq": -0.07,
            "al": 0.96
        },
        "continents": {
            "north_america": [0, 1, 2, 3, 4, 5, 6, 7, 8],
            "europe": [9, 10, 11, 12, 13, 14, 15],
            "asia": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
            "north_asia": [26, 25, 27, 21, 19, 23, 20],
            "south_asia": [24, 18, 17, 22, 16], 
            "south_america": [28, 29, 30, 31],
            "africa": [32, 33, 34, 35, 36, 37],
            "australia": [38, 40, 39, 41]
        },
        "claim_round": 0,
        "claim_mode": "australia",
        "temp_bound": 0,
        "attack_priority_list": {
            0: [5, 1, 21],
            1: [0, 5, 6, 8],
            2: [3, 8, 30],
            3: [8, 2, 7, 6],
            4: [5, 6, 7, 10],
            5: [0, 1, 6, 4],
            6: [4, 5, 1, 7, 8, 3],
            7: [4, 6, 3],
            8: [3, 2, 1, 6],

            9: [12, 10, 11, 15],
            10: [9, 12, 4],
            11: [14, 15, 13, 9, 12],
            12: [10, 11, 9, 14],
            13: [15, 14, 11, 34, 36, 22],
            14: [12, 11, 13, 26, 22, 16],
            15: [13, 11, 9, 36],

            16: [17, 26, 22, 14, 18],
            17: [24, 18, 16, 23, 25, 26],
            18: [24, 22, 16, 17],
            19: [21, 23, 27, 25],
            20: [21, 23],
            21: [20, 23, 19, 27, 0],
            22: [18, 16, 33, 34, 14, 13],
            23: [20, 21, 19, 25, 17],
            24: [17, 18, 40],
            25: [27, 19, 23, 26, 17],
            26: [25, 16, 17, 14],
            27: [19, 21, 25],
            
            28: [31, 29],
            29: [28, 31, 30, 36],
            30: [31, 29, 2],
            31: [28, 29, 30],

            32: [37, 33, 36],
            33: [35, 37, 32, 34, 36, 22],
            34: [33, 36, 13, 22],
            35: [37, 33],
            36: [32, 33, 34, 29, 15, 13],
            37: [35, 33, 32],

            38: [41, 39],
            39: [38, 41, 40],
            40: [39, 41, 24],
            41: [38, 39, 40]
        },
        "conquer_continent_difficulties": {
            "north_america": 0,
            "europe": 0,
            "asia": 0,
            "south_america": 0,
            "africa": 0,
            "australia": 0
        },
        "elimination_difficulties": {
            0: 0,
            1: 0,
            2: 0,
            3: 0,
            4: 0
        },
        "fork_flags": {}
    }
   
    # Respond to the engine's queries with your moves.
    while True:
        glb["claim_round"] += 1
        # Get the engine's query (this will block until you receive a query).
        query = game.get_next_query()

        # Based on the type of query, respond with the correct move.
        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryClaimTerritory() as q:
                    return handle_claim_territory(game, bot_state, q, glb)

                case QueryPlaceInitialTroop() as q:
                    return handle_place_initial_troop(game, bot_state, q, glb)

                case QueryRedeemCards() as q:
                    return handle_redeem_cards(game, bot_state, q)

                case QueryDistributeTroops() as q:
                    return handle_distribute_troops(game, bot_state, q, glb)

                case QueryAttack() as q:
                    return handle_attack(game, bot_state, q, glb)

                case QueryTroopsAfterAttack() as q:
                    return handle_troops_after_attack(game, bot_state, q, glb)

                case QueryDefend() as q:
                    return handle_defend(game, bot_state, q)

                case QueryFortify() as q:
                    return handle_fortify(game, bot_state, q)
        
        # Send the move to the engine.
        game.send_move(choose_move(query))

# 初始占地盘
def handle_claim_territory(game: Game, bot_state: BotState, query: QueryClaimTerritory, glb: dict) -> MoveClaimTerritory:
    """At the start of the game, you can claim a single unclaimed territory every turn 
    until all the territories have been claimed by players."""

    unclaimed_territories = game.state.get_territories_owned_by(None)
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    
    north_america = [0, 2, 4, 6, 1, 5, 8, 7, 3]
    europe = [13, 14, 15, 10, 9, 11, 12]
    asia = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    south_america = [30, 29, 31, 28]
    africa = [36, 33, 34, 32, 37, 35]
    aus = [40, 39, 41, 38]
    south_asia = [24, 18, 17, 22]
    
    # key locations
    # rfd = risk-free defend
    # area value = (value + 2 * connected_conts + rfd) / keylocs
    
    # val: 5.67
    north_america_value = 5
    north_america_connected_conts = 3
    north_america_keyloc = [0, 2, 4]
    north_america_rfd = [5, 1, 6, 7, 8, 3]
    
    # val: 3.5
    europe_value = 5
    europe_connected_conts = 3
    europe_keyloc = [10, 15, 13, 14]
    europe_keyloc_rfd = [9, 11, 12]
    
    # val:　4.4
    asia_value = 7
    asia_connected_conts = 4
    asia_keyloc = [26, 16, 22, 24, 21]
    asia_keyloc_rfd = [25, 27, 18, 20, 23, 17, 18]
    
    # val: 4
    south_america_value = 2
    south_america_connected_conts = 2
    south_america_keyloc = [30, 29]
    south_america_keyloc_rfd = [31, 28]
    
    # val: 4
    africa_value = 3
    africa_connected_conts = 3
    africa_keyloc = [36, 34, 33]
    africa_keyloc_rfd = [32, 37, 35]
    
    # val: 7
    australia_connected_conts = 1
    australia_value = 2
    aus_keyloc = [40]
    aus_keyloc_rfd = [39, 41, 38]

    priority_asia = [16, 21, 22, 24, 18, 17, 26, 20, 23, 25, 19, 27, 0, 14, 13, 11, 12, 15,]
    priority_africa = [36, 33, 32, 37, 35, 34, 28, 29, 31, 15, 13, 9, 11, 22, 30, 18, 24, 40, 39, 41, 38, 2, 3, 16, 17, 19, 20, 21, 23, 25, 26, 27, 0, 1, 4, 5, 6, 7, 8, 10, 12, 14]
    priority_aus = [38, 40, 39, 41, 24, 18, 17, 22, 19, 23, 20, 16, 13, 15, 14, 25, 27, 21, 0, 2, 7, 1, 3, 4, 5, 26, 8, 6, 10, 9, 12, 11, 30, 31, 29, 28, 35, 32, 37, 34, 33, 36]
    priority_south_america = [30, 29, 31, 28, 2, 3, 36, 15, 8, 37, 32, 33, 34, 35, 7, 1, 6, 13, 11, 10, 9, 12, 14, 0, 4, 5, 21, 20, 24, 18, 22, 19, 23, 25, 17, 27, 26, 40, 39, 38, 41]
    priority_europe = [13, 34, 36, 33, 32, 14, 15, 9, 11, 12, 10, 4, 22, 35, 37, 29, 31, 7, 6, 5, 26, 16, 22, 7, 6, 5, 34, 36, 0, 1, 3, 2, 8, 32, 33, 37, 35, 30, 29, 31, 28, 18, 21, 20, 23, 17, 19, 24, 25, 27, 38, 40, 39, 41]
    priority_north_america = [0, 2, 4, 6, 1, 5, 8, 7, 3, 30, 10, 9, 12, 31, 28, 21, 20, 29, 15, 11, 14, 27, 19, 23, 36, 34, 22, 16, 26, 25, 17, 18, 24, 40, 39, 41, 38]

    def is_continent_contested(continent):
        for territory in continent:
            if territory not in unclaimed_territories and territory not in my_territories:
                return True
        return False
    def bfs_weight(territory: int) -> int:
        queue = deque([territory])
        visited = set()
        count = 0

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)
            if current in unclaimed_territories:
                count += 1
                for neighbor in game.state.map.get_adjacent_to(current):
                    if neighbor not in visited:
                        queue.append(neighbor)
        return count

    if glb["claim_round"] == 1:

        if not is_continent_contested(north_america):
            for territory in north_america:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "north_america"
                    return game.move_claim_territory(query, territory) 

        if not is_continent_contested(aus):
            for territory in aus:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "australia"
                    return game.move_claim_territory(query, territory)
                
        if not is_continent_contested(south_america):
            for territory in south_america:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "south_america"
                    return game.move_claim_territory(query, territory)
                
        if not is_continent_contested(africa):
            for territory in africa:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "africa"
                    return game.move_claim_territory(query, territory)
                                            
        if not is_continent_contested(europe):
            for territory in europe:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "europe"
                    return game.move_claim_territory(query, territory)
                
        if not is_continent_contested(asia):
            for territory in priority_asia:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "asia"
                    return game.move_claim_territory(query, territory)
        
        
        for territory in africa:
            if territory in unclaimed_territories:
                glb["claim_mode"] = "africa"
                return game.move_claim_territory(query, territory)
                                        
        
        
        glb["claim_mode"] = "in_group"
        max_weight_territory = max(unclaimed_territories, key=lambda t: bfs_weight(t))

    elif glb["claim_round"] == 2:

        if not is_continent_contested(north_america):
            for territory in north_america:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "north_america"
                    return game.move_claim_territory(query, territory) 

        if not is_continent_contested(aus):
            for territory in aus:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "australia"
                    return game.move_claim_territory(query, territory)
                
        if not is_continent_contested(south_america):
            for territory in south_america:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "south_america"
                    return game.move_claim_territory(query, territory)
                
        if not is_continent_contested(africa):
            for territory in africa:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "africa"
                    return game.move_claim_territory(query, territory)
                                            
        if not is_continent_contested(europe):
            for territory in europe:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "europe"
                    return game.move_claim_territory(query, territory)
                
        if not is_continent_contested(asia):
            for territory in priority_asia:
                if territory in unclaimed_territories:
                    glb["claim_mode"] = "asia"
                    return game.move_claim_territory(query, territory)
        
    else:

        if glb["claim_mode"] == "africa":
            for territory in priority_africa:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        elif glb["claim_mode"] == "australia":
            for territory in priority_aus:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        elif glb["claim_mode"] == "south_america":
            for territory in priority_south_america:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        elif glb["claim_mode"] == "europe":
            for territory in priority_europe:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        elif glb["claim_mode"] == "north_america":
            for territory in priority_north_america:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        elif glb["claim_mode"] == "asia":
            for territory in priority_asia:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        else:
            # try get the adj territories for our centre choice, fallback: claim base on the priority list
            adjacent_territories = game.state.get_all_adjacent_territories(my_territories)
            available = list(set(unclaimed_territories) & set(adjacent_territories))
            if len(available) != 0:
                max_weight_territory = max(available, key=lambda t: bfs_weight(t))
            else:
                max_weight_territory = max(unclaimed_territories, key=lambda t: bfs_weight(t))
            return game.move_claim_territory(query, max_weight_territory)
    
    # unreachable code
    a_random_unclaimed_territory = random.choice(unclaimed_territories)
    return game.move_claim_territory(query, a_random_unclaimed_territory)

def conquer_continent_difficulty(game: Game, glb) -> None:
    continents = {
        "north_america": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "europe": [9, 10, 11, 12, 13, 14, 15],
        "asia": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
        "south_america": [28, 29, 30, 31],
        "africa": [32, 33, 34, 35, 36, 37],
        "australia": [38, 40, 39, 41]
    }
    difficulties = {
        "north_america": 0,
        "europe": 0,
        "asia": 0,
        "south_america": 0,
        "africa": 0,
        "australia": 0
    }
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    for continent, territories in continents.items():
        for territory in territories:
            if territory not in my_territories:
                difficulties[continent] += 1
    target = min(difficulties, key=difficulties.get)
    glb["claim_mode"] = target

def threat_count(game: Game, territory: int, n: int, decay_factor: float) -> float:
    #遍历n步内的所有敌方兵力，威胁评级相当于造访的区域的兵力总和，但是区域的威胁会随着距离的增加而减少，每一层*decay_factor
    queue = deque([(territory, 0)])  # (territory, depth)
    visited = set([territory])
    threat_rating = 0.0

    while queue:
        current_territory, depth = queue.popleft()
        if depth >= n:
            continue

        adjacent_territories = game.state.map.get_adjacent_to(current_territory)
        for neighbor in adjacent_territories:
            if neighbor not in visited:
                visited.add(neighbor)
                owner_id = game.state.territories[neighbor].occupier
                owner_card_count = game.state.players[owner_id].card_count
                if owner_id is not None and owner_id != game.state.me.player_id:
                    enemy_troops = game.state.territories[neighbor].troops
                    card_adjustment = (owner_card_count//3)* game.state.card_sets_redeemed * 3
                    if len(game.state.recording) > 800:
                        card_adjustment = -card_adjustment
                    threat_rating += (enemy_troops * 1 * (decay_factor ** depth))
                queue.append((neighbor, depth + 1))

    return threat_rating

# 初始兵力布置
def handle_place_initial_troop(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop, glb) -> MovePlaceInitialTroop:
    """After all the territories have been claimed, you can place a single troop on one
    of your territories each turn until each player runs out of troops."""

    # 计算大洲优先级
    conquer_continent_difficulty(game, glb)

    # 获取所有边界领土
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    border_territories = game.state.get_all_border_territories(my_territories)

    priority_africa = [32, 13, 22, 33, 34, 36, 34, 32, 35, 37, 28, 29, 31, 15, 13, 9, 11, 22, 30, 18, 24, 40, 39, 41, 38, 2, 3, 16, 17, 19, 20, 21, 23, 25, 26, 27, 0, 1, 4, 5, 6, 7, 8, 10, 12, 14]
    priority_aus = [24, 40, 24, 39, 38, 41, 17, 18, 22, 34, 19, 23, 20, 16, 13, 15, 14, 25, 27, 21, 0, 2, 7, 1, 3, 4, 5, 26, 8, 6, 10, 9, 12, 11, 30, 31, 29, 28, 35, 32, 37, 33, 36]
    priority_south_america = [29, 30, 31, 28, 36, 2, 3, 15, 8, 37, 32, 33, 34, 35, 7, 1, 6, 13, 11, 10, 9, 12, 14, 0, 4, 5, 21, 20, 24, 18, 22, 19, 23, 25, 17, 27, 26, 40, 39, 38, 41]
    priority_europe = [10, 14, 13, 15, 9, 11, 12, 4, 26, 16, 22, 7, 6, 5, 34, 36, 0, 1, 3, 2, 8, 32, 33, 37, 35, 30, 29, 31, 28, 18, 21, 20, 23, 17, 19, 24, 25, 27, 38, 40, 39, 41]
    priority_north_america = [2, 6, 1, 5, 0, 4, 8, 7, 3, 2, 30, 10, 9, 12, 31, 28, 21, 20, 29, 15, 11, 14, 27, 19, 23, 36, 34, 22, 16, 26, 25, 17, 18, 24, 40, 39, 41, 38]
    priority_asia = [16, 21, 22, 24, 18, 17, 26, 20, 23, 25, 19, 27, 0, 14, 13, 11, 12, 15,]


    # 获取每个领土所在的大洲
    territory_to_continent = {}
    continents = {
        "north_america": [6, 1, 5, 0, 4, 8, 7, 3, 2],
        "europe": [9, 10, 11, 12, 13, 14, 15],
        "asia": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
        "south_america": [28, 29, 30, 31],
        "africa": [32, 33, 34, 35, 36, 37],
        "australia": [40, 39, 38, 41]
    }
    for continent, territories in continents.items():
        for territory in territories:
            territory_to_continent[territory] = continent

    # 计算每个我方领土的威胁评级
    threat_ratings = {territory: threat_count(game, territory, 2, 0.25) for territory in border_territories}

    # 选择放置兵力的领土
    # 通过周围的威胁来均匀放置兵力，运用priority list的顺序对他们进行一次检测，如果当前territory的兵力<=周围的威胁总和，就放置兵力
    priority_list = []
    if glb["claim_mode"] == "africa":
        priority_list = priority_africa
    elif glb["claim_mode"] == "australia":
        priority_list = priority_aus
    elif glb["claim_mode"] == "south_america":
        priority_list = priority_south_america
    elif glb["claim_mode"] == "europe":
        priority_list = priority_europe
    elif glb["claim_mode"] == "north_america":
        priority_list = priority_north_america
    else:
        priority_list = priority_asia

    # 选择放置兵力的领土
    placement = None
    for territory in priority_list:
        adjustment = 0.8
        if territory in border_territories and game.state.territories[territory].troops <= threat_ratings[territory] + adjustment:
            print("threat rating", threat_ratings[territory], flush=True)
            placement = territory
            break

    if placement is None:
        # 如果没有与主要攻占策略相关的领土，选择威胁评级最高的领土放置兵力
        placement = max(threat_ratings, key=threat_ratings.get)

    return game.move_place_initial_troop(query, placement)


# 卡面兑换
# + 威胁评级 （n步之内是否有很大量的兵？如果有的话兑卡防御，没有的话hold (因为卡值会增加)
#

def handle_redeem_cards(game: Game, bot_state: BotState, query: QueryRedeemCards) -> MoveRedeemCards:
    """After the claiming and placing initial troops phases are over, you can redeem any
    cards you have at the start of each turn, or after killing another player."""

    # We will always redeem the minimum number of card sets we can until the 12th card set has been redeemed.
    # This is just an arbitrary choice to try and save our cards for the late game.

    # We always have to redeem enough cards to reduce our card count below five.
    card_sets: list[Tuple[CardModel, CardModel, CardModel]] = []
    cards_remaining = game.state.me.cards.copy()

    while len(cards_remaining) >= 5:
        card_set = game.state.get_card_set(cards_remaining)
        # According to the pigeonhole principle, we should always be able to make a set
        # of cards if we have at least 5 cards.
        assert card_set != None
        card_sets.append(card_set)
        cards_remaining = [card for card in cards_remaining if card not in card_set]

    # Remember we can't redeem any more than the required number of card sets if 
    # we have just eliminated a player.
    if game.state.card_sets_redeemed > 0 and query.cause == "turn_started":
        card_set = game.state.get_card_set(cards_remaining)
        while card_set != None:
            card_sets.append(card_set)
            cards_remaining = [card for card in cards_remaining if card not in card_set]
            card_set = game.state.get_card_set(cards_remaining)

    return game.move_redeem_cards(query, [(x[0].card_id, x[1].card_id, x[2].card_id) for x in card_sets])

# 回合内兵力分布
#
# def handle_distribute_troops(game: Game, bot_state: BotState, query: QueryDistributeTroops) -> MoveDistributeTroops:
#     """After you redeem cards (you may have chosen to not redeem any), you need to distribute
#     all the troops you have available across your territories. This can happen at the start of
#     your turn or after killing another player.
#     """

#     total_troops = game.state.me.troops_remaining
#     distributions = defaultdict(lambda: 0)
#     my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
#     border_territories = game.state.get_all_border_territories(my_territories)

#     if len(game.state.me.must_place_territory_bonus) != 0:
#         assert total_troops >= 2
#         distributions[game.state.me.must_place_territory_bonus[0]] += 2
#         total_troops -= 2

#     weakest_players = sorted(game.state.players.values(), key=lambda x: sum(
#         [game.state.territories[y].troops for y in game.state.get_territories_owned_by(x.player_id)]
#     ))

#     for player in weakest_players:
#         bordering_enemy_territories = set(game.state.get_all_adjacent_territories(my_territories)) & set(game.state.get_territories_owned_by(player.player_id))
#         if len(bordering_enemy_territories) > 0:
#             selected_territory = list(set(game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])) & set(my_territories))[0]
#             distributions[selected_territory] += total_troops
#             break

#     return game.move_distribute_troops(query, distributions)

def update_elimination_target(game: Game, my_territories: list, border_territories: list, glb: dict) -> None:
    """Search for a player to eliminate. If a player can be eliminated, return the player_id and the territory to attack from."""

    for player in game.state.players.values():
        pid = player.player_id
        if pid == game.state.me.player_id or not player.alive:
            glb["elimination_difficulties"][pid] = float("inf")  # skip self
            continue
        
        enemy_territories = game.state.get_territories_owned_by(player.player_id)
        enemy_border_territories = set(game.state.get_all_border_territories(enemy_territories))

        # check all the enemy territories, sum to glb["elimination_difficulties"] dict and sort it
        # mark these territories in glb["elimination_zone"] list, so we can use it in the future

        difficulty = 0
        for territory in enemy_border_territories:
            difficulty += game.state.territories[territory].troops + 1
        
        glb["elimination_difficulties"][pid] = difficulty

    glb["elimination_difficulties"] = dict(sorted(glb["elimination_difficulties"].items(), key=lambda x: x[1]))


def mark_elimination_zone(game: Game, my_territories: list, border_territories: list, glb: dict) -> None:

    def find_connected_components(territories: set) -> list:
        """Find connected components in the given territories."""
        visited = set()
        components = []

        def dfs(territory, component):
            stack = [territory]
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    component.append(current)
                    adjacent = set(game.state.map.get_adjacent_to(current))
                    stack.extend(adjacent.intersection(territories))
        
        for territory in territories:
            if territory not in visited:
                component = []
                dfs(territory, component)
                components.append(component)
        
        return components

    # 从最容易消灭的玩家到最难的玩家（跳过自己）
    sorted_players = sorted(glb["elimination_difficulties"].items(), key=lambda x: x[1])
    
    for pid, difficulty in sorted_players:
        if difficulty == float("inf"):
            continue  # skip self and eliminated players
        
        enemy_territories = set(game.state.get_territories_owned_by(pid))
        enemy_border_territories = set(game.state.get_all_border_territories(enemy_territories))
        
        for my_territory in border_territories:
            adjacent_territories = game.state.map.get_adjacent_to(my_territory)
            if enemy_border_territories.intersection(adjacent_territories):
                # Mark these territories in the elimination zone
                tmp = find_connected_components(enemy_territories)
                if len(tmp) > 1:
                    break
                c = 0
                for i in tmp:
                    glb["continents"]["elimination_zone_" + str(c)] = tmp[c]
                    c += 1
                return

# attack_mode = "", "conquer_continent", "harrass_weakest", "try_eliminate", "try_escape"

# need to check for difficulty on conquering continent

def calculate_continent_troops(game: Game, continent: List[int], my_territories: set) -> int:
    """Calculate the total enemy troops in a given continent including 1 troop for each territory to hold."""
    total_enemy_troops = sum(game.state.territories[t].troops + 1 for t in continent if t not in my_territories)
    return total_enemy_troops

def update_conquer_continent_difficulties(game: Game, glb: dict) -> None:
    """Calculate the conquer difficulties for all continents and update glb, then sort the dictionary by difficulty."""
    my_territories = set(game.state.get_territories_owned_by(game.state.me.player_id))
    continents = glb["continents"]
    conquer_continent_difficulties = glb["conquer_continent_difficulties"]

    # Calculate difficulties
    for continent_key, continent in continents.items():
        print(continent_key, continent, flush=True)
        total_enemy_troops = calculate_continent_troops(game, continent, my_territories)
        adjustment = 0
        if continent_key == "south_asia":
            adjustment = 5
        if continent_key == "south_america":
            adjustment = -1
        if continent_key == "north_asia":
            adjustment = 5
        if continent_key == "asia":
            adjustment = 2
        if continent_key == "australia":
            adjustment = 0
        if continent_key == "north_america":
            adjustment = 3
        if continent_key[:15] == "elimination_zone":
            adjustment = 0
        conquer_continent_difficulties[continent_key] = total_enemy_troops + adjustment

    # Sort the dictionary by difficulty
    sorted_difficulties = dict(sorted(conquer_continent_difficulties.items(), key=lambda item: item[1], reverse=True))
    glb["conquer_continent_difficulties"] = sorted_difficulties


def handle_distribute_troops(game: Game, bot_state: BotState, query: QueryDistributeTroops, glb: dict) -> MoveDistributeTroops:

    # reset dicts

    glb["conquer_continent_difficulties"] = {
            "north_america": 0,
            "europe": 0,
            "asia": 0,
            "south_america": 0,
            "africa": 0,
            "australia": 0
        }
    

    glb["attack_mode"] = ""

    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    border_territories = game.state.get_all_border_territories(my_territories)
    threat_ratings = {territory: threat_count(game, territory, 1, 1) for territory in border_territories}
    # sorted_border_territories = sorted(threat_ratings, key=threat_ratings.get)

    total_troops = game.state.me.troops_remaining
    distributions = defaultdict(lambda: 0)
    if len(game.state.me.must_place_territory_bonus) != 0:
        assert total_troops >= 2
        distributions[game.state.me.must_place_territory_bonus[0]] += 2
        total_troops -= 2
    
    # we look for the weakest player to eliminate, if we can't eliminate, we will try to conquer a continent
    # for each *component* in the elimination_zone, we try find my border territory with max troops adjacent to it, and generate a list
    # of territories to attack from for each component, then we will see if we can distribute our remaining troops accordingly to the sum of the troops in the component and make every
    # attacker have more troops than the target component, if we can't, we will go to test for conquering a continent
    
    update_conquer_continent_difficulties(game, glb)
    update_elimination_target(game, my_territories, border_territories, glb)
    mark_elimination_zone(game, my_territories, border_territories, glb)
    
    # 处理消灭目标
    # additional_troops_needed = {}
    # for component in glb["elimination_zone"]:
    #     total_enemy_troops = sum(game.state.territories[t].troops for t in component)
    #     adjacent_territories = set(game.state.get_all_adjacent_territories(component)) & set(border_territories)
        
    #     if adjacent_territories:
    #         strongest_adjacent_territory = max(adjacent_territories, key=lambda t: game.state.territories[t].troops)
    #         troops_needed = total_enemy_troops - game.state.territories[strongest_adjacent_territory].troops + 1
    #         if troops_needed > 0:
    #             additional_troops_needed[strongest_adjacent_territory] = troops_needed
    # print(total_troops, additional_troops_needed, flush=True)
    # if additional_troops_needed and sum(additional_troops_needed.values()) <= total_troops:
    #     glb["attack_mode"] = "eliminate"
    #     for territory, troops in additional_troops_needed.items():
    #         distributions[territory] += troops
    #     total_troops -= sum(additional_troops_needed.values())

    #     while total_troops > 0:
    #         for territory in additional_troops_needed:
    #             if total_troops <= 0:
    #                 break
    #             distributions[territory] += 1
    #             total_troops -= 1

    #     return game.move_distribute_troops(query, distributions)
    

    
    difficulties = glb["conquer_continent_difficulties"]
    difficulties = dict(sorted(difficulties.items(), key=lambda x: x[1]))
    print(difficulties, flush=True)

    for continent, difficulty in difficulties.items():

        continent_member = glb["continents"][continent]
        #adjacent_territories = set(game.state.get_all_adjacent_territories(continent_member)+[t for t in glb["continents"][continent] if t in my_territories]) & set(border_territories)
        unconquered_t_in_target_continent = set(continent_member) - set(my_territories)
        adjacent_territories = set(game.state.get_all_adjacent_territories(unconquered_t_in_target_continent)) & set(border_territories)

        if adjacent_territories:
            strongest_adjacent_territory = max(adjacent_territories, key=lambda t: game.state.territories[t].troops)
            if game.state.territories[strongest_adjacent_territory].troops + total_troops >= difficulty and difficulty != 0:
                distributions[strongest_adjacent_territory] += total_troops
                print(f"try conquer continent: {continent}, difficulty: {difficulty}, round: {len(game.state.recording)}",  flush=True)
                glb["attack_mode"] = "conquer_continent"
                return game.move_distribute_troops(query, distributions)

    
    glb["attack_mode"] = "harrass_weakest"

    # for player in weakest_players:
    #     tt = game.state.get_territories_owned_by(player.player_id)
    #     bordering_enemy_territories = set(game.state.get_all_adjacent_territories(my_territories)) & set(game.state.get_territories_owned_by(player.player_id))
    #     if len(bordering_enemy_territories) > 0:
    #         selected_territory = list(set(game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])) & set(my_territories))[0]
    #         if (sum(game.state.territories[t].troops for t in tt) + len(game.state.get_territories_owned_by(weakest_players[0]))) * 1 < total_troops + game.state.territories[selected_territory].troops:
    #             distributions[selected_territory] += total_troops
    #             return game.move_distribute_troops(query, distributions)

    # 计算分配比例
    total_threat = sum(threat_ratings.values())
    if total_threat > 0:
        distribution_ratios = {territory: threat / total_threat for territory, threat in threat_ratings.items()}
    else:
        distribution_ratios = {territory: 1 / len(border_territories) for territory in border_territories}

    troops_to_allocate = total_troops
    for territory, ratio in distribution_ratios.items():
        troops_to_place = int(total_troops * ratio)
        distributions[territory] += troops_to_place
        troops_to_allocate -= troops_to_place

    # 处理剩余的部队（由于舍入可能会有剩余）
    if troops_to_allocate > 0:
        for territory in sorted(threat_ratings, key=threat_ratings.get, reverse=True):
            if troops_to_allocate <= 0:
                break
            distributions[territory] += 1
            troops_to_allocate -= 1

    return game.move_distribute_troops(query, distributions)

# 进攻策略
# + 是否进攻？ 如果损失不大，进攻拿卡
# + 进攻优先级： 一波推 > 占领完整大陆 > 破坏完整大陆 > 其他
# + 优先级计算加入 est. battle cost?


# # ?有必要吗？ 我不好说
# def simulate_attack(attacker_dice: int, defender_dice: int) -> Tuple:
#     """Simulate a single attack round based on Risk dice rules."""
#     attacker_rolls = sorted([np.random.randint(1, 7) for _ in range(attacker_dice)], reverse=True)
#     defender_rolls = sorted([np.random.randint(1, 7) for _ in range(defender_dice)], reverse=True)
#     attacker_losses = 0
#     defender_losses = 0

#     for a, d in zip(attacker_rolls, defender_rolls):
#         if a > d:
#             defender_losses += 1
#         else:
#             attacker_losses += 1

#     return attacker_losses, defender_losses

# def estimate_attack_probability(attacker_troops: int, defender_troops: int, simulations: int = 1000) -> float:
#     """Estimate the probability of attacker winning the battle using simulations."""
#     attacker_wins = 0
    # for _ in range(simulations):
    #     attacker = attacker_troops
    #     defender = defender_troops

    #     while attacker > 1 and defender > 0:
    #         attacker_dice = min(attacker - 1, 3)
    #         defender_dice = min(defender, 2)
    #         attacker_losses, defender_losses = simulate_attack(attacker_dice, defender_dice)
    #         attacker -= attacker_losses
    #         defender -= defender_losses

    #     if defender == 0:
    #         attacker_wins += 1

    # return attacker_wins / simulations


def handle_attack(game: Game, bot_state: BotState, query: QueryAttack, glb: dict) -> Union[MoveAttack, MoveAttackPass]:
    """After the troop phase of your turn, you may attack any number of times until you decide to 
    stop attacking (by passing). After a successful attack, you may move troops into the conquered 
    territory. If you eliminated a player you will get a move to redeem cards and then distribute troops."""

    # reset dicts

    glb["conquer_continent_difficulties"] = {
            "north_america": 0,
            "europe": 0,
            "asia": 0,
            "south_america": 0,
            "africa": 0,
            "australia": 0
        }
    
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    border_territories = game.state.get_all_border_territories(my_territories)

    update_elimination_target(game, my_territories, border_territories, glb)
    mark_elimination_zone(game, my_territories, border_territories, glb)
    update_conquer_continent_difficulties(game, glb)
    print(f"attack_mode: {glb['attack_mode']}, round: {len(game.state.recording)}",  flush=True)

    # 3. 检测周围威胁

    
    # bordering_enemy_territories = game.state.get_all_adjacent_territories(my_territories)
    # threat_ratings = {territory: threat_count(game, territory, 3, 0.2) for territory in bordering_enemy_territories}
    
    # harrass_weakest
    def attack_check(t, territories: list[int]) -> Optional[MoveAttack]:
        territories = sorted(territories, key=lambda x: game.state.territories[x].troops)

        conquer_continent_difficulties = glb["conquer_continent_difficulties"]
        conquer_continent_difficulties = dict(sorted(conquer_continent_difficulties.items(), key=lambda x: x[1]))

        for target_continent, difficulty in conquer_continent_difficulties.items():
            target_range = glb["continents"][target_continent]
            unconquered_t_in_target_continent = set(target_range) - set(my_territories)
            attacker_list = list(set(game.state.get_all_adjacent_territories(unconquered_t_in_target_continent)) & set(border_territories))
            attacker_list = sorted(attacker_list, key=lambda x: game.state.territories[x].troops, reverse=True)
            for attacker_t in attacker_list:
                if attacker_t not in my_territories:
                    continue
                attacker_troops = game.state.territories[attacker_t].troops
                target_range = sorted(target_range, key=lambda x: game.state.territories[x].troops)
                for target in target_range:
                    if target not in game.state.map.get_adjacent_to(attacker_t):
                        continue
                    if target not in my_territories and game.state.territories[target].troops <= attacker_troops and attacker_troops >= 3:
                        return game.move_attack(query, attacker_t, target, min(3, game.state.territories[attacker_t].troops - 1))

        # for candidate_target in glb["attack_priority_list"][t]:
        #     if game.state.territories[t].troops < 3:
        #         break
        #     if candidate_target in tmp and game.state.territories[t].troops >= game.state.territories[candidate_target].troops + 2:
        #         return game.move_attack(query, t, candidate_target, min(3, game.state.territories[t].troops - 1))

        return None
    
    if glb["attack_mode"] == "":
        return game.move_attack_pass(query)
                

    # 如果有conquer_continent的目标，我们优先攻击这个目标
    if glb["attack_mode"] == "conquer_continent":
        
        conquer_continent_difficulties = glb["conquer_continent_difficulties"]
        print(conquer_continent_difficulties, flush=True)

        for target_continent, difficulty in conquer_continent_difficulties.items():
            target_range = glb["continents"][target_continent]
            print("target_continent: ", target_continent, flush=True)
            unconquered_t_in_target_continent = set(target_range) - set(my_territories)
            attacker_list = list(set(game.state.get_all_adjacent_territories(unconquered_t_in_target_continent)) & set(border_territories))
            #attacker_list = game.state.get_all_adjacent_territories(glb["continents"][target_continent]) + [t for t in glb["continents"][target_continent] if t in my_territories]
            print(attacker_list, flush=True)
            attacker_list = sorted(attacker_list, key=lambda x: game.state.territories[x].troops, reverse=True)
            
            for attacker_t in attacker_list:
                if attacker_t not in my_territories:
                    continue
                attacker_troops = game.state.territories[attacker_t].troops
                for target in glb["attack_priority_list"][attacker_t]:
                    if target not in target_range or attacker_troops <= difficulty:
                        continue
                    # print(f"attack: {attacker_t} -> {target}, troops: {attacker_troops} -> {game.state.territories[target].troops}, round: {len(game.state.recording)}", flush=True)
                    # print (target not in my_territories)
                    # print (game.state.territories[target].troops < attacker_troops)
                    # print (attacker_troops >= 3)
                    if target not in my_territories and game.state.territories[target].troops <= attacker_troops and attacker_troops >= 3:
                        return game.move_attack(query, attacker_t, target, min(3, game.state.territories[attacker_t].troops - 1))
                    
    else:
        ts = sorted(border_territories, key=lambda x: game.state.territories[x].troops, reverse=True)
        for t in ts:
            move = attack_check(t, list(set(game.state.map.get_adjacent_to(t)) - set(my_territories)))
            if move != None:
                return move

    # if glb["attack_mode"] == "eliminate":
    #     update_elimination_target(game, my_territories, border_territories, glb)
    #     mark_elimination_zone(game, my_territories, border_territories, glb)

    #     for component in glb["elimination_zone"]:
    #         attacker_list = list(set(game.state.get_all_adjacent_territories(component)) & set(border_territories))
    #         attacker_list = sorted(attacker_list, key=lambda x: game.state.territories[x].troops, reverse=True)
            
    #         for attacker_t in attacker_list:
    #             attacker_troops = game.state.territories[attacker_t].troops
    #             if attacker_troops <= sum(game.state.territories[t].troops for t in component) + 100:
    #                 break

    #             for target in glb["attack_priority_list"].get(attacker_t, []):
    #                 if target in my_territories:
    #                     continue
    #                 if target in component and attacker_troops >= game.state.territories[target].troops + 1:
    #                     return game.move_attack(query, attacker_t, target, min(3, game.state.territories[attacker_t].troops - 1))
                    
    #     glb["attack_mode"] = "harrass_weakest"          
    
    
    
    # 4. 根据走线攻击
    # 5. 如果威胁太大，阻止这次被检测的区域的攻击。
    # 6. 直到所有区域都威胁太大，我们交出move_attack_pass

    return game.move_attack_pass(query)

# 进攻后兵力移动
def handle_troops_after_attack(game: Game, bot_state: BotState, query: QueryTroopsAfterAttack, glb) -> MoveTroopsAfterAttack:
    """After conquering a territory in an attack, you must move troops to the new territory."""

    my_territories = set(game.state.get_territories_owned_by(game.state.me.player_id))
    border_territories = game.state.get_all_border_territories(my_territories)
    
    
    # First we need to get the record that describes the attack, and then the move that specifies
    # which territory was the attacking territory.
    record_attack = cast(RecordAttack, game.state.recording[query.record_attack_id])
    move_attack = cast(MoveAttack, game.state.recording[record_attack.move_attack_id])

    attacking_territory = move_attack.attacking_territory
    attacking_territory_troops = game.state.territories[attacking_territory].troops
    conquered_territory = move_attack.defending_territory
    attacking_troops = move_attack.attacking_troops

    
    
    if glb["attack_mode"] == "harrass_weakest":
        glb["attack_mode"] = "conquer_continent"
        return game.move_troops_after_attack(query, min(attacking_territory_troops - 1, 3))
    
    # TODO: 检查是否所有相邻的区域都是自己的，如果是的话我们尝试只留1个兵力，否则的话我们根据周围的敌人数量来决定留下多少兵力？
    adjacent_territories = set(game.state.map.get_adjacent_to(conquered_territory))
    we_own_all_adj = adjacent_territories.issubset(my_territories) # all(adj in my_territories for adj in adjacent_territories)
    enemy_territories = adjacent_territories.difference(my_territories)
    enemy_powers = sum(game.state.territories[enemy_territory].troops for enemy_territory in enemy_territories)

    if glb["attack_mode"] == "conquer_continent" or glb["attack_mode"] == "eliminate":
        update_elimination_target(game, my_territories, border_territories, glb)
        mark_elimination_zone(game, my_territories, border_territories, glb)
        update_conquer_continent_difficulties(game, glb)

        troops_to_move = max(attacking_territory_troops - 1, attacking_troops)
        if we_own_all_adj:
            troops_to_move = min(3, attacking_territory_troops - 1)
        elif threat_count(game, attacking_territory, 1, 0.2) >= 4:
            troops_to_move = max(attacking_territory_troops - 2, attacking_troops)
        return game.move_troops_after_attack(query, troops_to_move)
    else:
        troops_to_move = max(attacking_territory_troops - max(1, floor(enemy_powers*0.8)), attacking_troops)
    
    return game.move_troops_after_attack(query, troops_to_move)

# 可以忽略
def handle_defend(game: Game, bot_state: BotState, query: QueryDefend) -> MoveDefend:
    """If you are being attacked by another player, you must choose how many troops to defend with."""

    # We will always defend with the most troops that we can.

    # First we need to get the record that describes the attack we are defending against.
    move_attack = cast(MoveAttack, game.state.recording[query.move_attack_id])
    defending_territory = move_attack.defending_territory
    
    # We can only defend with up to 2 troops, and no more than we have stationed on the defending
    # territory.
    defending_troops = min(game.state.territories[defending_territory].troops, 2)
    return game.move_defend(query, defending_troops)


def handle_fortify(game: Game, bot_state: BotState, query: QueryFortify) -> Union[MoveFortify, MoveFortifyPass]:
    """At the end of your turn, after you have finished attacking, you may move a number of troops between
    any two of your territories (they must be adjacent)."""

    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    total_troops_per_player = {}
    for player in game.state.players.values():
        total_troops_per_player[player.player_id] = sum(game.state.territories[x].troops for x in game.state.get_territories_owned_by(player.player_id))

    most_powerful_player = max(total_troops_per_player.items(), key=lambda x: x[1])[0]
    
    # 获取所有边界领土和非边界领土
    border_territories = game.state.get_all_border_territories(my_territories)
    non_border_territories = [t for t in my_territories if t not in border_territories]

    threat_ratings = {territory: threat_count(game, territory, 1, 1) - game.state.territories[territory].troops for territory in my_territories}
    weakest_border_territories = sorted(threat_ratings, key=threat_ratings.get)

    # 找到兵力最多的非边界领土
    if non_border_territories:
        strongest_non_border_territory = max(non_border_territories, key=lambda x: game.state.territories[x].troops)
        if game.state.territories[strongest_non_border_territory].troops > 1:
            # 尝试寻找最短路径
            # try adjacent territories first, move to the weakest border territory adjacent to the strongest non-border territory
            # list adj and sort them first
            adj = game.state.map.get_adjacent_to(strongest_non_border_territory)
            adj = sorted(adj, key=lambda x: game.state.territories[x].troops)
            for t in adj:
                if t in border_territories:
                    return game.move_fortify(query, strongest_non_border_territory, t, game.state.territories[strongest_non_border_territory].troops - 1)

            path = find_shortest_path_from_vertex_to_set(game, strongest_non_border_territory, set(border_territories))
            if len(path) > 1:
                next_step = path[1]
                return game.move_fortify(query, strongest_non_border_territory, next_step, game.state.territories[strongest_non_border_territory].troops - 1)
    
    # 寻找兵力最多的边界领土
    # if border_territories:
    #     most_troops_territory = max(border_territories, key=lambda x: game.state.territories[x].troops)

    #     shortest_path = find_shortest_path_from_vertex_to_set(game, most_troops_territory, set(game.state.get_territories_owned_by(most_powerful_player)))

    #     if len(shortest_path) > 1 and game.state.territories[most_troops_territory].troops > 1:
    #         return game.move_fortify(query, shortest_path[0], shortest_path[1], game.state.territories[most_troops_territory].troops - 1)
    
    return game.move_fortify_pass(query)


def find_shortest_path_from_vertex_to_set(game: Game, source: int, target_set: set[int]) -> list[int]:
    """Used in move_fortify() to find the shortest path from the source to any target in the target_set, ensuring the path contains only our territories."""
    print("target:", target_set, " source: ", source, flush=True)

    # We perform a BFS search from our source vertex, stopping at the first member of the target_set we find.
    queue = deque([source])
    parent = {source: None}
    seen = {source}

    while queue:
        current = queue.pop()
        if current in target_set:
            # Found a target, reconstruct the path
            path = []
            while current is not None:
                path.append(current)
                current = parent[current]
            return path[::-1]

        for neighbor in game.state.map.get_adjacent_to(current):
            if neighbor not in seen and neighbor in game.state.get_territories_owned_by(game.state.me.player_id):
                seen.add(neighbor)
                parent[neighbor] = current
                queue.appendleft(neighbor)

    return []


if __name__ == "__main__":
    main()



# archive

#TODO: use the threat rating to determine: if we are attacking for more control / cards from others or defending due to a high incoming threat, and distribute troops accordingly
# def handle_distribute_troops(game: Game, bot_state: BotState, query: QueryDistributeTroops) -> MoveDistributeTroops:
#     """After you redeem cards (you may have chosen to not redeem any), you need to distribute
#     all the troops you have available across your territories. This can happen at the start of
#     your turn or after killing another player.
#     """

#     # We will distribute troops across our border territories.
#     total_troops = game.state.me.troops_remaining
#     distributions = defaultdict(lambda: 0)
#     border_territories = game.state.get_all_border_territories(
#         game.state.get_territories_owned_by(game.state.me.player_id)
#     )

#     # We need to remember we have to place our matching territory bonus
#     # if we have one.
#     if len(game.state.me.must_place_territory_bonus) != 0:
#         assert total_troops >= 2
#         distributions[game.state.me.must_place_territory_bonus[0]] += 2
#         total_troops -= 2

    
#     if len(game.state.recording) < 800:
#         my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
#         weakest_players = sorted(game.state.players.values(), key=lambda x: sum(
#             [game.state.territories[y].troops for y in game.state.get_territories_owned_by(x.player_id)]
#         ))

#         for player in weakest_players:
#             bordering_enemy_territories = set(game.state.get_all_adjacent_territories(my_territories)) & set(game.state.get_territories_owned_by(player.player_id))
#             if len(bordering_enemy_territories) > 0:
#                 # print("my territories", [game.state.map.get_vertex_name(x) for x in my_territories])
#                 # print("bordering enemies", [game.state.map.get_vertex_name(x) for x in bordering_enemy_territories])
#                 # print("adjacent to target", [game.state.map.get_vertex_name(x) for x in game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])])
#                 selected_territory = list(set(game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])) & set(my_territories))[0]
#                 distributions[selected_territory] += total_troops
#                 break

#     else:
#         troops_per_territory = total_troops // len(border_territories)
#         leftover_troops = total_troops % len(border_territories)
#         for territory in border_territories:
#             distributions[territory] += troops_per_territory
    
#         # The leftover troops will be put some territory (we don't care)
#         distributions[border_territories[0]] += leftover_troops


#     return game.move_distribute_troops(query, distributions)

