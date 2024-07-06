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
    
    # 0: normal attack, move all the troops - 1 to the new territory; 1: split attack: move the minimum amount of troop possible to let the original attack territory attack another adjacent territory once again
    attack_move_flag = [0]

    # conquer the continent; 2: attack the weakest player to try eliminate
    # 进攻策略
    # + 是否进攻？ 如果损失不大，进攻拿卡
    # + 进攻优先级： 一波推 > 占领完整大陆 > 破坏完整大陆 > 其他
    
    # 在部署兵力阶段判断我们的进攻模式。
    # 部署模式第一轮我们可以直接判断需要部署兵力的所有格子以及相对应的兵力数量 -> 在第一轮产生一个队列并在之后的query执行

    # 进攻模式汇总: no_attack, conquer_continent, attack_weakest, harrass_continent
    attackmode = ["no_attack"]

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
    europe = [10, 9, 15, 11, 12, 13, 14]
    asia = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    south_america = [30, 31, 29, 28]
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
    priority_south_america = [30, 31, 29, 28, 2, 3, 36, 8, 7, 1, 6, 0, 4, 5, 21, 20, 37, 32, 33, 34, 13, 15, 35, 11, 10, 9, 12, 14, 24, 18, 22, 19, 23, 25, 17, 27, 26, 40, 39, 38, 41]
    priority_europe = [10, 9, 15, 11, 12, 13, 14, 4, 26, 16, 22, 7, 6, 5, 34, 36, 0, 1, 3, 2, 8, 32, 33, 37, 35, 30, 29, 31, 28, 18, 21, 20, 23, 17, 19, 24, 25, 27, 38, 40, 39, 41]

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

        if not is_continent_contested(europe):
            for territory in europe:
                if territory in unclaimed_territories:
                    claim_mode[0] = "europe"
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
        elif claim_mode[0] == "europe":
            for territory in priority_europe:
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
    
    # unreachable code
    a_random_unclaimed_territory = random.choice(unclaimed_territories)
    return game.move_claim_territory(query, a_random_unclaimed_territory)


# # 初始兵力布置
# def handle_place_initial_troop(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
#     """After all the territories have been claimed, you can place a single troop on one
#     of your territories each turn until each player runs out of troops."""
    
#     # We will place troops along the territories on our border.
#     border_territories = game.state.get_all_border_territories(
#         game.state.get_territories_owned_by(game.state.me.player_id)
#     )

#     # We will place a troop in the border territory with the least troops currently
#     # on it. This should give us close to an equal distribution.
#     border_territory_models = [game.state.territories[x] for x in border_territories]
#     min_troops_territory = min(border_territory_models, key=lambda x: x.troops)

#     return game.move_place_initial_troop(query, min_troops_territory.territory_id)

def handle_place_initial_troop(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
    """After all the territories have been claimed, you can place a single troop on one
    of your territories each turn until each player runs out of troops."""
    
    # 计算大洲优先级
    continent_priorities = calculate_continent_priority(game)
    continent_priority_map = {continent: priority for continent, priority in continent_priorities}

    # 获取所有边界领土
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    border_territories = game.state.get_all_border_territories(my_territories)

    # 获取每个领土所在的大洲
    territory_to_continent = {}
    continents = {
        "north_america": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "europe": [9, 10, 11, 12, 13, 14, 15],
        "asia": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
        "south_america": [28, 29, 30, 31],
        "africa": [32, 33, 34, 35, 36, 37],
        "australia": [40, 39, 38, 41]
    }
    for continent, territories in continents.items():
        for territory in territories:
            territory_to_continent[territory] = continent

    # 筛选边界领土并计算优先级
    border_territory_priorities = []
    for territory in border_territories:
        continent = territory_to_continent[territory]
        priority = continent_priority_map[continent]
        border_territory_priorities.append((territory, priority))

    # 按优先级排序边界领土
    border_territory_priorities.sort(key=lambda x: x[1], reverse=True)

    # 在优先级最高的边界领土上布置部队
    border_territory_ids = [territory for territory, priority in border_territory_priorities]
    min_troops_territory = min(border_territory_ids, key=lambda x: game.state.territories[x].troops)

    return game.move_place_initial_troop(query, min_troops_territory)


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
    if len(game.state.recording) < 4000:
        troops_per_territory = total_troops // len(border_territories)
        leftover_troops = total_troops % len(border_territories)
        for territory in border_territories:
            distributions[territory] += troops_per_territory
    
        # The leftover troops will be put some territory (we don't care)
        distributions[border_territories[0]] += leftover_troops
    
    else:
        my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
        weakest_players = sorted(game.state.players.values(), key=lambda x: sum(
            [game.state.territories[y].troops for y in game.state.get_territories_owned_by(x.player_id)]
        ))

        for player in weakest_players:
            bordering_enemy_territories = set(game.state.get_all_adjacent_territories(my_territories)) & set(game.state.get_territories_owned_by(player.player_id))
            if len(bordering_enemy_territories) > 0:
                # print("my territories", [game.state.map.get_vertex_name(x) for x in my_territories])
                # print("bordering enemies", [game.state.map.get_vertex_name(x) for x in bordering_enemy_territories])
                # print("adjacent to target", [game.state.map.get_vertex_name(x) for x in game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])])
                selected_territory = list(set(game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])) & set(my_territories))[0]
                distributions[selected_territory] += total_troops
                break


    return game.move_distribute_troops(query, distributions)

# 大洲优先级计算
def calculate_continent_priority(game: Game) -> list[Tuple[str, float]]:
    # 计算每个大洲的优先级，并按优先级排序返回
    continent_bonus = {
        "north_america": 5,
        "europe": 5,
        "asia": 7,
        "south_america": 2,
        "africa": 3,
        "australia": 2
    }
    
    continents = {
        "north_america": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "europe": [9, 10, 11, 12, 13, 14, 15],
        "asia": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
        "south_america": [28, 29, 30, 31],
        "africa": [32, 33, 34, 35, 36, 37],
        "australia": [40, 39, 38, 41]
    }

    control_difficulty = {
        "north_america": 1,
        "europe": 1.2,
        "asia": 1.5,
        "south_america": 0.8,
        "africa": 1.1,
        "australia": 0.5
    }

    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    all_territories = set(range(42)) # ^_^
    enemy_territories = all_territories - set(my_territories)
    
    continent_priorities = []

    for continent, territories in continents.items():
        total_territories = len(territories)
        owned_territories = len(set(territories) & set(my_territories))
        enemy_territories_count = len(set(territories) & enemy_territories)

        # 如果我们已经完全占领了该大洲，将优先级设置为最低
        if owned_territories == total_territories:
            priority_score = float('-inf')  # 优先级最低
        else:
            priority_score = (
                continent_bonus[continent] * 20 / control_difficulty[continent]
                + owned_territories * 10
                - enemy_territories_count * 20
            )
        continent_priorities.append((continent, priority_score))

    # 按优先级排序大洲
    continent_priorities.sort(key=lambda x: x[1], reverse=True)
    
    return continent_priorities

def calculate_continent_forces(game: Game) -> dict[str, Tuple[int, int]]:
    # 计算每个大洲中敌方的总兵力和我方的总兵力 tuple: (我方兵力, 敌方兵力)
    continents = {
        "north_america": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "europe": [9, 10, 11, 12, 13, 14, 15],
        "asia": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
        "south_america": [28, 29, 30, 31],
        "africa": [32, 33, 34, 35, 36, 37],
        "australia": [40, 39, 38, 41]
    }

    my_territories = set(game.state.get_territories_owned_by(game.state.me.player_id))
    forces = {}

    for continent, territories in continents.items():
        my_forces = sum(game.state.territories[t].troops for t in territories if t in my_territories)
        enemy_forces = sum(game.state.territories[t].troops for t in territories if t not in my_territories)
        forces[continent] = (my_forces, enemy_forces)
    
    return forces

def adjust_priority_based_on_forces(priorities: list[Tuple[str, float]], forces: dict[str, Tuple[int, int]]) -> list[Tuple[str, float]]:
    # 根据兵力调整大洲的优先级
    adjusted_priorities = []

    # TODO: 调整优先级
    for continent, priority in priorities:
        my_forces, enemy_forces = forces[continent]
        force_diff = my_forces - enemy_forces
        adjusted_priority = priority + force_diff * 0.1
        adjusted_priorities.append((continent, adjusted_priority))

    # 按调整后的优先级排序
    adjusted_priorities.sort(key=lambda x: x[1], reverse=True)
    
    return adjusted_priorities

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
                threshhold = 2
                bound = 1
                if len(game.state.recording) < 450: pass
                elif len(game.state.recording) < 1700: threshhold = 4
                elif len(game.state.recording) < 3000: threshhold = 6
                else:
                    threshhold = -2
                    bound = 2
                if game.state.territories[candidate_attacker].troops - game.state.territories[candidate_target].troops >= threshhold and game.state.territories[candidate_attacker].troops > bound:
                    return game.move_attack(query, candidate_attacker, candidate_target, min(3, game.state.territories[candidate_attacker].troops - 1))
                    # return game.move_attack(query, candidate_attacker, candidate_target, game.state.territories[candidate_target].troops)

    strongest_territories = sorted(my_territories, key=lambda x: game.state.territories[x].troops, reverse=True)
    for territory in strongest_territories:
        move = attack_weakest(list(set(game.state.map.get_adjacent_to(territory)) - set(my_territories)))
        if move != None:
            return move

    return game.move_attack_pass(query)

# 进攻后兵力移动
def handle_troops_after_attack(game: Game, bot_state: BotState, query: QueryTroopsAfterAttack) -> MoveTroopsAfterAttack:
    """After conquering a territory in an attack, you must move troops to the new territory."""

    my_territories = set(game.state.get_territories_owned_by(game.state.me.player_id))
    
    # First we need to get the record that describes the attack, and then the move that specifies
    # which territory was the attacking territory.
    record_attack = cast(RecordAttack, game.state.recording[query.record_attack_id])
    move_attack = cast(MoveAttack, game.state.recording[record_attack.move_attack_id])

    attacking_territory = move_attack.attacking_territory
    attacking_territory_troops = game.state.territories[attacking_territory].troops
    conquered_territory = move_attack.defending_territory
    attacking_troops = move_attack.attacking_troops

    # TODO: 检查是否所有相邻的区域都是自己的，如果是的话我们尝试只留1个兵力，否则的话我们根据周围的敌人数量来决定留下多少兵力？
    adjacent_territories = set(game.state.map.get_adjacent_to(conquered_territory))
    we_own_all_adj = adjacent_territories.issubset(my_territories) # all(adj in my_territories for adj in adjacent_territories)
    enemy_territories = adjacent_territories.difference(my_territories)
    enemy_powers = sum(game.state.territories[enemy_territory].troops for enemy_territory in enemy_territories)


    # 有问题，暂时弃用。
    # if all_adjacent_owned:
    #     troops_to_move = attacking_troops - 1
    # else:
    #     max_adjacent_enemy_troops = max(
    #         (game.state.territories[adj].troops for adj in adjacent_territories if adj not in my_territories), 
    #         default=1
    #     )
    #     troops_to_move = max(1, min(attacking_troops - 1, max_adjacent_enemy_troops + 1))

    # troops_to_move = attacking_territory_troops - 1

    if we_own_all_adj:
        troops_to_move = max(attacking_territory_troops - 1, attacking_troops)
    else:
        troops_to_move = max(attacking_territory_troops - max(1, floor(enemy_powers*0.8)), attacking_troops)
    
    # troops_to_move = max(
    #     min(3, attacking_troops),
    #     attacking_territory_troops // 2
    # )

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



def find_max_gap_border_territory(game: Game, border_territories: list[int], my_territories: set[int]) -> int:
    """找到与周围部队差距最大的边界区域。"""
    max_gap = -1
    target_territory = None

    for territory in border_territories:
        adjacent_territories = game.state.map.get_adjacent_to(territory)
        my_adjacent_troops = sum(game.state.territories[adj].troops for adj in adjacent_territories if adj in my_territories)
        enemy_adjacent_troops = sum(game.state.territories[adj].troops for adj in adjacent_territories if adj not in my_territories)
        gap = enemy_adjacent_troops - my_adjacent_troops

        if gap > max_gap:
            max_gap = gap
            target_territory = territory

    return target_territory


def handle_fortify(game: Game, bot_state: BotState, query: QueryFortify) -> Union[MoveFortify, MoveFortifyPass]:
    """At the end of your turn, after you have finished attacking, you may move a number of troops between
    any two of your territories (they must be adjacent)."""

    

    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    total_troops_per_player = {}
    for player in game.state.players.values():
        total_troops_per_player[player.player_id] = sum([game.state.territories[x].troops for x in game.state.get_territories_owned_by(player.player_id)])

    least_powerful_player = min(total_troops_per_player.items(), key=lambda x: x[1])[0]
    
    # 获取所有边界领土和非边界领土
    border_territories = game.state.get_all_border_territories(my_territories)
    non_border_territories = [t for t in my_territories if t not in border_territories]

    # 找到兵力最多的非边界领土
    if non_border_territories:
        strongest_non_border_territory = max(non_border_territories, key=lambda x: game.state.territories[x].troops)
        if game.state.territories[strongest_non_border_territory].troops > 1:
            # 寻找最薄弱的边界领土
            weakest_border_territory = min(border_territories, key=lambda x: game.state.territories[x].troops)
            if weakest_border_territory:
                # 寻找从最强非边界领土到最薄弱边界领土的最短路径
                path = find_shortest_path_from_vertex_to_set(game, strongest_non_border_territory, {weakest_border_territory})
                if len(path) > 1:
                    next_step = path[1]
                    # print("fortify - try: non_border to border", strongest_non_border_territory, next_step, game.state.territories[strongest_non_border_territory].troops - 1)
                    return game.move_fortify(query, strongest_non_border_territory, next_step, game.state.territories[strongest_non_border_territory].troops - 1)
    
    # 寻找兵力最多的边界领土
    most_troops_territory = max(border_territories, key=lambda x: game.state.territories[x].troops)

    # 使用自定义函数寻找从兵力最多的边界领土到最弱敌方领土的最短路径
    shortest_path = find_shortest_path_from_vertex_to_set(game, most_troops_territory, set(game.state.get_territories_owned_by(least_powerful_player)))

    if len(shortest_path) > 1 and game.state.territories[most_troops_territory].troops > 1:
        print("fortify", shortest_path[0], shortest_path[1])
        return game.move_fortify(query, shortest_path[0], shortest_path[1], game.state.territories[most_troops_territory].troops // 2)
    
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

