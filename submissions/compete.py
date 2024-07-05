from collections import defaultdict, deque
import random
from typing import Optional, Tuple, Union, cast
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

# We will store our enemy in the bot state.
class BotState():
    def __init__(self):
        self.enemy: Optional[int] = None


def main():
    
    # Get the game object, which will connect you to the engine and
    # track the state of the game.
    game = Game()
    bot_state = BotState()
    
    # 0: normal attack, move all the troops - 1 to the new territory; 1: split attack: move the minimum amount of troop possible to let the original attack territory attack another adjacent territory once again
    attackflag = 0

    # attackmode = 0: normal attack; 1: conquer the continent; 2: attack the weakest player to try eliminate
    attackmode = 0

    claim_mode = ["australia"]
    claim_round = 0
   
    # Respond to the engine's queries with your moves.
    while True:
        claim_round += 1
        # Get the engine's query (this will block until you receive a query).
        query = game.get_next_query()

        # Based on the type of query, respond with the correct move.
        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryClaimTerritory() as q:
                    return handle_claim_territory(game, bot_state, q, claim_round, claim_mode)

                case QueryPlaceInitialTroop() as q:
                    return handle_place_initial_troop(game, bot_state, q)

                case QueryRedeemCards() as q:
                    return handle_redeem_cards(game, bot_state, q)

                case QueryDistributeTroops() as q:
                    return handle_distribute_troops(game, bot_state, q)

                case QueryAttack() as q:
                    return handle_attack(game, bot_state, q)

                case QueryTroopsAfterAttack() as q:
                    return handle_troops_after_attack(game, bot_state, q)

                case QueryDefend() as q:
                    return handle_defend(game, bot_state, q)

                case QueryFortify() as q:
                    return handle_fortify(game, bot_state, q)
        
        # Send the move to the engine.
        game.send_move(choose_move(query))

# 初始占地盘
def handle_claim_territory(game: Game, bot_state: BotState, query: QueryClaimTerritory, claim_round: int, claim_mode: list[str]) -> MoveClaimTerritory:
    """At the start of the game, you can claim a single unclaimed territory every turn 
    until all the territories have been claimed by players."""

    unclaimed_territories = game.state.get_territories_owned_by(None)
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    
    north_america = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    europe = [9, 10, 11, 12, 13, 14, 15]
    asia = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    south_america = [29, 30, 31, 28]
    africa = [32, 33, 34, 35, 36, 37]
    aus = [40, 39, 38, 41]
    
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

    priority_aus = [40, 39, 38, 41, 24, 18, 17, 22, 19, 23, 20, 16, 13, 15, 14, 25, 27, 21, 0, 2, 7, 1, 3, 4, 5, 26, 8, 6, 10, 9, 12, 11, 30, 31, 29, 28, 35, 32, 37, 34, 33, 36]
    priority_south_america = [29, 30, 31, 28, 2, 3, 36, 8, 6, 37, 32, 33, 34, 35, 7, 1, 11, 10, 9, 12, 4, 5, 0, 13, 15, 14, 24, 18, 22, 19, 23, 20, 25, 17, 27, 21, 26, 40, 39, 38, 41]

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

    if claim_round == 1:
        if not is_continent_contested(aus):
            for territory in aus:
                if territory in unclaimed_territories:
                    claim_mode[0] = "australia"
                    return game.move_claim_territory(query, territory)
            
        if not is_continent_contested(south_america):
            for territory in south_america:
                if territory in unclaimed_territories:
                    claim_mode[0] = "south_america"
                    return game.move_claim_territory(query, territory)
        claim_mode[0] = "in_group"
        max_weight_territory = max(unclaimed_territories, key=lambda t: bfs_weight(t))
    else:
        if claim_mode[0] == "australia":
            for territory in priority_aus:
                if territory in unclaimed_territories:
                    return game.move_claim_territory(query, territory)
        elif claim_mode[0] == "south_america":
            for territory in priority_south_america:
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

    for territory in priority_aus:
        if territory in unclaimed_territories:
            return game.move_claim_territory(query, territory)

    return game.move_claim_territory(query)


# 初始兵力布置
def handle_place_initial_troop(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
    """After all the territories have been claimed, you can place a single troop on one
    of your territories each turn until each player runs out of troops."""
    
    # We will place troops along the territories on our border.
    border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )

    # We will place a troop in the border territory with the least troops currently
    # on it. This should give us close to an equal distribution.
    border_territory_models = [game.state.territories[x] for x in border_territories]
    min_troops_territory = min(border_territory_models, key=lambda x: x.troops)

    return game.move_place_initial_troop(query, min_troops_territory.territory_id)

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
    if game.state.card_sets_redeemed > 12 and query.cause == "turn_started":
        card_set = game.state.get_card_set(cards_remaining)
        while card_set != None:
            card_sets.append(card_set)
            cards_remaining = [card for card in cards_remaining if card not in card_set]
            card_set = game.state.get_card_set(cards_remaining)

    return game.move_redeem_cards(query, [(x[0].card_id, x[1].card_id, x[2].card_id) for x in card_sets])

# 回合内兵力分布
#

def handle_distribute_troops(game: Game, bot_state: BotState, query: QueryDistributeTroops) -> MoveDistributeTroops:
    """After you redeem cards (you may have chosen to not redeem any), you need to distribute
    all the troops you have available across your territories. This can happen at the start of
    your turn or after killing another player.
    """

    # We will distribute troops across our border territories.
    total_troops = game.state.me.troops_remaining
    distributions = defaultdict(lambda: 0)
    border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )

    # We need to remember we have to place our matching territory bonus
    # if we have one.
    if len(game.state.me.must_place_territory_bonus) != 0:
        assert total_troops >= 2
        distributions[game.state.me.must_place_territory_bonus[0]] += 2
        total_troops -= 2


    # # We will equally distribute across border territories in the early game,
    # # but start doomstacking in the late game.
    # if len(game.state.recording) < 4000:
    #     troops_per_territory = total_troops // len(border_territories)
    #     leftover_troops = total_troops % len(border_territories)
    #     for territory in border_territories:
    #         distributions[territory] += troops_per_territory
    
    #     # The leftover troops will be put some territory (we don't care)
    #     distributions[border_territories[0]] += leftover_troops
    
    # else:
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    weakest_players = sorted(game.state.players.values(), key=lambda x: sum(
        [game.state.territories[y].troops for y in game.state.get_territories_owned_by(x.player_id)]
    ))

    for player in weakest_players:
        bordering_enemy_territories = set(game.state.get_all_adjacent_territories(my_territories)) & set(game.state.get_territories_owned_by(player.player_id))
        if len(bordering_enemy_territories) > 0:
            print("my territories", [game.state.map.get_vertex_name(x) for x in my_territories])
            print("bordering enemies", [game.state.map.get_vertex_name(x) for x in bordering_enemy_territories])
            print("adjacent to target", [game.state.map.get_vertex_name(x) for x in game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])])
            selected_territory = list(set(game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])) & set(my_territories))[0]
            distributions[selected_territory] += total_troops
            break


    return game.move_distribute_troops(query, distributions)

# 进攻策略
# + 是否进攻？ 如果损失不大，进攻拿卡
# + 进攻优先级： 一波推 > 占领完整大陆 > 破坏完整大陆 > 其他
# + 优先级计算加入 est. battle cost?
#

def handle_attack(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    """After the troop phase of your turn, you may attack any number of times until you decide to
    stop attacking (by passing). After a successful attack, you may move troops into the conquered
    territory. If you eliminated a player you will get a move to redeem cards and then distribute troops."""
    
    # We will attack someone.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    bordering_territories = game.state.get_all_adjacent_territories(my_territories)

    def attack_weakest(territories: list[int]) -> Optional[MoveAttack]:
        # We will attack the weakest territory from the list.
        territories = sorted(territories, key=lambda x: game.state.territories[x].troops)
        for candidate_target in territories:
            candidate_attackers = sorted(list(set(game.state.map.get_adjacent_to(candidate_target)) & set(my_territories)), key=lambda x: game.state.territories[x].troops, reverse=True)
            for candidate_attacker in candidate_attackers:
                threshhold = 2 if len(game.state.recording) < 600 else 5
                if game.state.territories[candidate_attacker].troops - game.state.territories[candidate_target].troops >= threshhold:
                    return game.move_attack(query, candidate_attacker, candidate_target, min(3, game.state.territories[candidate_attacker].troops - 1))


    # if len(game.state.recording) < 4000:
    #     # We will check if anyone attacked us in the last round.
    #     new_records = game.state.recording[game.state.new_records:]
    #     enemy = None
    #     for record in new_records:
    #         match record:
    #             case MoveAttack() as r:
    #                 if r.defending_territory in set(my_territories):
    #                     enemy = r.move_by_player

    #     # If we don't have an enemy yet, or we feel angry, this player will become our enemy.
    #     if enemy != None:
    #         if bot_state.enemy == None or random.random() < 0.05:
    #             bot_state.enemy = enemy
        
    #     # If we have no enemy, we will pick the player with the weakest territory bordering us, and make them our enemy.
    #     else:
    #         weakest_territory = min(bordering_territories, key=lambda x: game.state.territories[x].troops)
    #         bot_state.enemy = game.state.territories[weakest_territory].occupier
            
    #     # We will attack their weakest territory that gives us a favourable battle if possible.
    #     enemy_territories = list(set(bordering_territories) & set(game.state.get_territories_owned_by(enemy)))
    #     move = attack_weakest(enemy_territories)
    #     if move != None:
    #         return move
        
    #     # Otherwise we will attack anyone most of the time.
    #     if random.random() < 0.8:
    #         move = attack_weakest(bordering_territories)
    #         if move != None:
    #             return move

    # In the late game, we will attack anyone adjacent to our strongest territories (hopefully our doomstack).
    # else:
    strongest_territories = sorted(my_territories, key=lambda x: game.state.territories[x].troops, reverse=True)
    for territory in strongest_territories:
        move = attack_weakest(list(set(game.state.map.get_adjacent_to(territory)) - set(my_territories)))
        if move != None:
            return move

    return game.move_attack_pass(query)



def handle_troops_after_attack(game: Game, bot_state: BotState, query: QueryTroopsAfterAttack) -> MoveTroopsAfterAttack:
    """After conquering a territory in an attack, you must move troops to the new territory."""

    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    
    # First we need to get the record that describes the attack, and then the move that specifies
    # which territory was the attacking territory.
    record_attack = cast(RecordAttack, game.state.recording[query.record_attack_id])
    move_attack = cast(MoveAttack, game.state.recording[record_attack.move_attack_id])

    attacking_territory = move_attack.attacking_territory
    conquered_territory = move_attack.defending_territory

    # TODO: 检查是否所有相邻的区域都是自己的，如果是的话我们尝试只留1个兵力，否则的话我们根据周围的敌人数量来决定留下多少兵力？
    adjacent_territories = game.state.map.get_adjacent_to(conquered_territory)
    all_adjacent_owned = all(adj in my_territories for adj in adjacent_territories)

    attacking_troops = game.state.territories[attacking_territory].troops

    # 有问题，暂时弃用。
    # if all_adjacent_owned:
    #     troops_to_move = attacking_troops - 1
    # else:
    #     max_adjacent_enemy_troops = max(
    #         (game.state.territories[adj].troops for adj in adjacent_territories if adj not in my_territories), 
    #         default=1
    #     )
    #     troops_to_move = max(1, min(attacking_troops - 1, max_adjacent_enemy_troops + 1))

    troops_to_move = attacking_troops - 1

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


    # We will always fortify towards the most powerful player (player with most troops on the map) to defend against them.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)

    #查找自己的所有区域 -> 找到自己的区域强度顺序 -> 将自己的第二强的区域的troop移动到最强的，但是同时考虑区域边界，适当的为区域的边界增加权重以应对敌人


    total_troops_per_player = {}
    for player in game.state.players.values():
        total_troops_per_player[player.player_id] = sum([game.state.territories[x].troops for x in game.state.get_territories_owned_by(player.player_id)])

    most_powerful_player = max(total_troops_per_player.items(), key=lambda x: x[1])[0]
    
    # Otherwise we will find the shortest path between our territory with the most troops
    # and any of the most powerful player's territories and fortify along that path.
    border_territories = game.state.get_all_border_territories(my_territories)
    sorted_territories = sorted(my_territories, key=lambda x: game.state.territories[x].troops, reverse=True)

    # Prioritize border territories
    border_sorted_territories = [t for t in sorted_territories if t in border_territories]
    non_border_sorted_territories = [t for t in sorted_territories if t not in border_territories]


    strongest_territory = sorted_territories[0]
    second_strongest_territory = sorted_territories[1] if len(sorted_territories) > 1 else None
    
    if border_sorted_territories:
        strongest_border_territory = border_sorted_territories[0]
    else:
        strongest_border_territory = None

    if strongest_border_territory:
        # 优先将非边界区域的部队移动到最强的边界区域
        for territory in non_border_sorted_territories:
            if game.state.territories[territory].troops > 1:
                for neighbor in game.state.map.get_adjacent_to(territory):
                    if neighbor in border_territories:
                        troops_to_move = game.state.territories[territory].troops - 1
                        return game.move_fortify(query, territory, neighbor, troops_to_move)

        # 其次将其他边界区域的部队移动到最强的边界区域？？ 
        for territory in border_sorted_territories[1:]:
            if game.state.territories[territory].troops > 1 and game.state.map.is_adjacent(territory, strongest_border_territory):
                troops_to_move = game.state.territories[territory].troops - 1
                return game.move_fortify(query, territory, strongest_border_territory, troops_to_move)
        #后面再改吧 >_<

    return game.move_fortify_pass(query)



def find_shortest_path_from_vertex_to_set(game: Game, source: int, target_set: set[int]) -> list[int]:
    """Used in move_fortify()."""

    # We perform a BFS search from our source vertex, stopping at the first member of the target_set we find.
    queue = deque()
    queue.appendleft(source)

    current = queue.pop()
    parent = {}
    seen = {current: True}

    while len(queue) != 0:
        if current in target_set:
            break

        for neighbour in game.state.map.get_adjacent_to(current):
            if neighbour not in seen:
                seen[neighbour] = True
                parent[neighbour] = current
                queue.appendleft(neighbour)

        current = queue.pop()

    path = []
    while current in parent:
        path.append(current)
        current = parent[current]

    return path[::-1]

if __name__ == "__main__":
    main()



# def create_map():
#     vertices = {
#         "ALASKA": 0,
#         "ALBERTA": 1,
#         "CENTRAL_AMERICA": 2,
#         "EASTERN_US": 3,
#         "GREENLAND": 4,
#         "NORTHWEST_TERRITORY": 5,
#         "ONTARIO": 6,
#         "QUEBEC": 7,
#         "WESTERN_US": 8,
#         "GREAT_BRITAIN": 9,
#         "ICELAND": 10,
#         "NORTHERN_EUROPE": 11,
#         "SCANDINAVIA": 12,
#         "SOUTHERN_EUROPE": 13,
#         "UKRAINE": 14,
#         "WESTERN_EUROPE": 15,
#         "AFGHANISTAN": 16,
#         "CHINA": 17,
#         "INDIA": 18,
#         "IRKUTSK": 19,
#         "JAPAN": 20,
#         "KAMCHATKA": 21,
#         "MIDDLE_EAST": 22,
#         "MONGOLIA": 23,
#         "SIAM": 24,
#         "SIBERIA": 25,
#         "URAL": 26,
#         "YAKUTSK": 27,
#         "ARGENTINA": 28,
#         "BRAZIL": 29,
#         "VENEZUELA": 30,
#         "PERU": 31,
#         "CONGO": 32,
#         "EAST_AFRICA": 33,
#         "EGYPT": 34,
#         "MADAGASCAR": 35,
#         "NORTH_AFRICA": 36,
#         "SOUTH_AFRICA": 37,
#         "EASTERN_AUSTRALIA": 38,
#         "NEW_GUINEA": 39,
#         "INDONESIA": 40,
#         "WESTERN_AUSTRALIA": 41,
#     }

#     continents = {
#         0 : [
#                 vertices["ALASKA"],
#                 vertices["ALBERTA"],
#                 vertices["CENTRAL_AMERICA"],
#                 vertices["EASTERN_US"],
#                 vertices["GREENLAND"],
#                 vertices["NORTHWEST_TERRITORY"],
#                 vertices["ONTARIO"],
#                 vertices["QUEBEC"],
#                 vertices["WESTERN_US"]
#             ],
#         1 : [
#                 vertices["GREAT_BRITAIN"],
#                 vertices["ICELAND"],
#                 vertices["NORTHERN_EUROPE"],
#                 vertices["SCANDINAVIA"],
#                 vertices["SOUTHERN_EUROPE"],
#                 vertices["UKRAINE"],
#                 vertices["WESTERN_EUROPE"],
#             ],
#         2 : [
#                 vertices["AFGHANISTAN"],
#                 vertices["CHINA"],
#                 vertices["INDIA"],
#                 vertices["IRKUTSK"],
#                 vertices["JAPAN"],
#                 vertices["KAMCHATKA"],
#                 vertices["MIDDLE_EAST"],
#                 vertices["MONGOLIA"],
#                 vertices["SIAM"],
#                 vertices["SIBERIA"],
#                 vertices["URAL"],
#                 vertices["YAKUTSK"],
#             ],
#         3: [
#                 vertices["ARGENTINA"],
#                 vertices["BRAZIL"],
#                 vertices["VENEZUELA"],
#                 vertices["PERU"],
#             ],
#         4: [
#                 vertices["CONGO"],
#                 vertices["EAST_AFRICA"],
#                 vertices["EGYPT"],
#                 vertices["MADAGASCAR"],
#                 vertices["NORTH_AFRICA"],
#                 vertices["SOUTH_AFRICA"]
#             ],
#         5: [
#                 vertices["EASTERN_AUSTRALIA"],
#                 vertices["NEW_GUINEA"],
#                 vertices["INDONESIA"],
#                 vertices["WESTERN_AUSTRALIA"],
#             ],
#     }

#     continent_bonuses = {
#         0 : 5,
#         1 : 5,
#         2 : 7,
#         3 : 2,
#         4 : 3,
#         5 : 2,
#     }

#     edges = {
#         vertices["ALASKA"]: [
#             vertices["ALBERTA"],
#             vertices["NORTHWEST_TERRITORY"],
#             vertices["KAMCHATKA"],
#         ],
#         vertices["ALBERTA"]: [
#             vertices["ONTARIO"],
#             vertices["NORTHWEST_TERRITORY"],
#             vertices["ALASKA"],
#             vertices["WESTERN_US"],
#         ],
#         vertices["CENTRAL_AMERICA"]: [
#             vertices["EASTERN_US"],
#             vertices["WESTERN_US"],
#             vertices["VENEZUELA"],
#         ],
#         vertices["EASTERN_US"]: [
#             vertices["QUEBEC"],
#             vertices["ONTARIO"],
#             vertices["WESTERN_US"],
#             vertices["CENTRAL_AMERICA"],
#         ],
#         vertices["GREENLAND"]: [
#             vertices["NORTHWEST_TERRITORY"],
#             vertices["ONTARIO"],
#             vertices["QUEBEC"],
#             vertices["ICELAND"],
#         ],
#         vertices["NORTHWEST_TERRITORY"]: [
#             vertices["GREENLAND"],
#             vertices["ALASKA"],
#             vertices["ALBERTA"],
#             vertices["ONTARIO"],
#         ],
#         vertices["ONTARIO"]: [
#             vertices["QUEBEC"],
#             vertices["GREENLAND"],
#             vertices["NORTHWEST_TERRITORY"],
#             vertices["ALBERTA"],
#             vertices["WESTERN_US"],
#             vertices["EASTERN_US"],
#         ],
#         vertices["QUEBEC"]: [
#             vertices["GREENLAND"],
#             vertices["ONTARIO"],
#             vertices["EASTERN_US"],
#         ],
#         vertices["WESTERN_US"]: [
#             vertices["EASTERN_US"],
#             vertices["ONTARIO"],
#             vertices["ALBERTA"],
#             vertices["CENTRAL_AMERICA"],
#         ],
#         vertices["GREAT_BRITAIN"]: [
#             vertices["NORTHERN_EUROPE"],
#             vertices["SCANDINAVIA"],
#             vertices["ICELAND"],
#             vertices["WESTERN_EUROPE"],
#         ],
#         vertices["ICELAND"]: [
#             vertices["SCANDINAVIA"],
#             vertices["GREENLAND"],
#             vertices["GREAT_BRITAIN"],
#         ],
#         vertices["NORTHERN_EUROPE"]: [
#             vertices["UKRAINE"],
#             vertices["SCANDINAVIA"],
#             vertices["GREAT_BRITAIN"],
#             vertices["WESTERN_EUROPE"],
#             vertices["SOUTHERN_EUROPE"],
#         ],
#         vertices["SCANDINAVIA"]: [
#             vertices["UKRAINE"],
#             vertices["ICELAND"],
#             vertices["GREAT_BRITAIN"],
#             vertices["NORTHERN_EUROPE"],
#         ],
#         vertices["SOUTHERN_EUROPE"]: [
#             vertices["MIDDLE_EAST"],
#             vertices["UKRAINE"],
#             vertices["NORTHERN_EUROPE"],
#             vertices["WESTERN_EUROPE"],
#             vertices["NORTH_AFRICA"],
#             vertices["EGYPT"],
#         ],
#         vertices["UKRAINE"]: [
#             vertices["AFGHANISTAN"],
#             vertices["URAL"],
#             vertices["SCANDINAVIA"],
#             vertices["NORTHERN_EUROPE"],
#             vertices["SOUTHERN_EUROPE"],
#             vertices["MIDDLE_EAST"],
#         ],
#         vertices["WESTERN_EUROPE"]: [
#             vertices["SOUTHERN_EUROPE"],
#             vertices["NORTHERN_EUROPE"],
#             vertices["GREAT_BRITAIN"],
#             vertices["NORTH_AFRICA"],
#         ],
#         vertices["AFGHANISTAN"]: [
#             vertices["CHINA"],
#             vertices["URAL"],
#             vertices["UKRAINE"],
#             vertices["MIDDLE_EAST"],
#             vertices["INDIA"],
#         ],
#         vertices["CHINA"]: [
#             vertices["MONGOLIA"],
#             vertices["SIBERIA"],
#             vertices["URAL"],
#             vertices["AFGHANISTAN"],
#             vertices["INDIA"],
#             vertices["SIAM"],
#         ],
#         vertices["INDIA"]: [
#             vertices["SIAM"],
#             vertices["CHINA"],
#             vertices["AFGHANISTAN"],
#             vertices["MIDDLE_EAST"],
#         ],
#         vertices["IRKUTSK"]: [
#             vertices["KAMCHATKA"],
#             vertices["YAKUTSK"],
#             vertices["SIBERIA"],
#             vertices["MONGOLIA"],
#         ],
#         vertices["JAPAN"]: [
#             vertices["KAMCHATKA"],
#             vertices["MONGOLIA"],
#         ],
#         vertices["KAMCHATKA"]: [
#             vertices["ALASKA"],
#             vertices["YAKUTSK"],
#             vertices["IRKUTSK"],
#             vertices["MONGOLIA"],
#             vertices["JAPAN"],
#         ],
#         vertices["MIDDLE_EAST"]: [
#             vertices["INDIA"],
#             vertices["AFGHANISTAN"],
#             vertices["UKRAINE"],
#             vertices["SOUTHERN_EUROPE"],
#             vertices["EGYPT"],
#             vertices["EAST_AFRICA"],
#         ],
#         vertices["MONGOLIA"]: [
#             vertices["JAPAN"],
#             vertices["KAMCHATKA"],
#             vertices["IRKUTSK"],
#             vertices["SIBERIA"],
#             vertices["CHINA"],
#         ],
#         vertices["SIAM"]: [
#             vertices["CHINA"],
#             vertices["INDIA"],
#             vertices["INDONESIA"],
#         ],
#         vertices["SIBERIA"]: [
#             vertices["YAKUTSK"],
#             vertices["URAL"],
#             vertices["CHINA"],
#             vertices["MONGOLIA"],
#             vertices["IRKUTSK"],
#         ],
#         vertices["URAL"]: [
#             vertices["SIBERIA"],
#             vertices["UKRAINE"],
#             vertices["AFGHANISTAN"],
#             vertices["CHINA"],
#         ],
#         vertices["YAKUTSK"]: [
#             vertices["KAMCHATKA"],
#             vertices["SIBERIA"],
#             vertices["IRKUTSK"],
#         ],
#         vertices["ARGENTINA"]: [
#             vertices["BRAZIL"],
#             vertices["PERU"],
#         ],
#         vertices["BRAZIL"]: [
#             vertices["NORTH_AFRICA"],
#             vertices["VENEZUELA"],
#             vertices["PERU"],
#             vertices["ARGENTINA"],
#         ],
#         vertices["VENEZUELA"]: [
#             vertices["CENTRAL_AMERICA"],
#             vertices["PERU"],
#             vertices["BRAZIL"],
#         ],
#         vertices["PERU"]: [
#             vertices["BRAZIL"],
#             vertices["VENEZUELA"],
#             vertices["ARGENTINA"],
#         ],
#         vertices["CONGO"]: [
#             vertices["EAST_AFRICA"],
#             vertices["NORTH_AFRICA"],
#             vertices["SOUTH_AFRICA"],
#         ],
#         vertices["EAST_AFRICA"]: [
#             vertices["MIDDLE_EAST"],
#             vertices["EGYPT"],
#             vertices["NORTH_AFRICA"],
#             vertices["CONGO"],
#             vertices["SOUTH_AFRICA"],
#             vertices["MADAGASCAR"],
#         ],
#         vertices["EGYPT"]: [
#             vertices["MIDDLE_EAST"],
#             vertices["SOUTHERN_EUROPE"],
#             vertices["NORTH_AFRICA"],
#             vertices["EAST_AFRICA"],
#         ],
#         vertices["MADAGASCAR"]: [
#             vertices["EAST_AFRICA"],
#             vertices["SOUTH_AFRICA"],
#         ],
#         vertices["NORTH_AFRICA"]: [
#             vertices["EAST_AFRICA"],
#             vertices["EGYPT"],
#             vertices["SOUTHERN_EUROPE"],
#             vertices["WESTERN_EUROPE"],
#             vertices["BRAZIL"],
#             vertices["CONGO"],
#         ],
#         vertices["SOUTH_AFRICA"]: [
#             vertices["MADAGASCAR"],
#             vertices["EAST_AFRICA"],
#             vertices["CONGO"],
#         ],
#         vertices["EASTERN_AUSTRALIA"]: [
#             vertices["NEW_GUINEA"],
#             vertices["WESTERN_AUSTRALIA"],
#         ],
#         vertices["NEW_GUINEA"]: [
#             vertices["INDONESIA"],
#             vertices["WESTERN_AUSTRALIA"],
#             vertices["EASTERN_AUSTRALIA"],
#         ],
#         vertices["INDONESIA"]: [
#             vertices["NEW_GUINEA"],
#             vertices["SIAM"],
#             vertices["WESTERN_AUSTRALIA"],
#         ],
#         vertices["WESTERN_AUSTRALIA"]: [
#             vertices["EASTERN_AUSTRALIA"],
#             vertices["NEW_GUINEA"],
#             vertices["INDONESIA"],
#         ],
#     }

#     return Map(vertices=vertices, edges=edges, continents=continents, continent_bonuses=continent_bonuses)