from io import TextIOWrapper
import math
import random
from signal import SIGALRM, alarm, signal
from time import time
from typing import Any, Callable, Literal, ParamSpec, Type, TypeVar, Union, final

from pydantic import BaseModel, ValidationError

from engine.config.ioconfig import CORE_DIRECTORY, CUMULATIVE_TIMEOUT_SECONDS, MAX_CHARACTERS_READ, READ_CHUNK_SIZE, TIMEOUT_SECONDS
from engine.exceptions import BrokenPipeException, CumulativeTimeoutException, PlayerException, InvalidResponseException, TimeoutException
from engine.game.player import Player
from engine.game.state import State
from engine.queries.base_query import BaseQuery
from engine.queries.query_claim_territory import QueryClaimTerritory
from engine.queries.query_defend import QueryDefend
from engine.queries.query_place_initial_troop import QueryPlaceInitialTroop
from engine.queries.query_attack import QueryAttack
from engine.queries.query_distribute_troops import QueryDistributeTroops
from engine.queries.query_redeem_cards import QueryRedeemCards
from engine.queries.query_fortify import QueryFortifyTerritory
from engine.queries.query_troops_after_attack import QueryTroopsAfterAttack
from engine.records.moves.move_claim_territory import MoveClaimTerritory
from engine.records.moves.move_claim_territory import MoveClaimTerritory
from engine.records.moves.move_defend import MoveDefend
from engine.records.moves.move_place_initial_troop import MovePlaceInitialTroop
from engine.records.moves.move_distribute_troops import MoveDistributeTroops
from engine.records.moves.move_redeem_cards import MoveRedeemCards
from engine.records.moves.move_fortify import MoveFortify
from engine.records.moves.move_attack import MoveAttack
from engine.records.record_start_game import RecordStartGame

P = ParamSpec("P")
T1 = TypeVar("T1")
def handle_sigpipe(fn: Callable[P, T1]) -> Callable[P, T1]:
    """Decorator to trigger ban if the player closes the from_engine pipe.
    """

    def dfn(*args: P.args, **kwargs: P.kwargs) -> T1:
        self: 'PlayerConnection' = args[0] # type: ignore
        try:
            result = fn(*args, **kwargs)
        except BrokenPipeError:
            raise BrokenPipeException(self.player_id, "You closed 'from_engine.pipe'.")

        return result
    
    return dfn


def handle_invalid(fn: Callable[P, T1]) -> Callable[P, T1]:
    """Decorator to trigger ban if the player sends an invalid, but syntactically correct message.
    """

    def dfn(*args: P.args, **kwargs: P.kwargs) -> T1:
        self: 'PlayerConnection' = args[0] # type: ignore
        try:
            result = fn(*args, **kwargs)
        except ValidationError as e:
            raise InvalidResponseException(self.player_id, "You sent an invalid message to the game engine: \n" + e.json(indent=2))

        return result
    
    return dfn
    

def time_limited(error_message: str = "You took too long to respond."):
    """Decorator to trigger ban if the player takes too long to respond.
    """

    def dfn1(fn: Callable[P, T1]):
        def dfn2(*args: P.args, **kwargs: P.kwargs) -> T1:
            self: 'PlayerConnection' = args[0]  # type: ignore
            def on_timeout_alarm(*_):
                raise TimeoutException(self.player_id, error_message)
            signal(SIGALRM, on_timeout_alarm)

            alarm(TIMEOUT_SECONDS)
            start = time()

            result = fn(*args, **kwargs)

            end = time()
            alarm(0) 

            self._cumulative_time += end - start
            if self._cumulative_time > CUMULATIVE_TIMEOUT_SECONDS:
                raise CumulativeTimeoutException(self.player_id, error_message)
            
            return result

        return dfn2
    
    return dfn1


T2 = TypeVar("T2", bound=BaseModel)
@final
class PlayerConnection():

    def __init__(self, player_id: int):
        self.player_id: int = player_id
        self._to_engine_pipe: TextIOWrapper
        self._from_engine_pipe: TextIOWrapper
        self._cumulative_time: float = 0
        self._record_update_watermark: int = 0

        self._open_pipes()

    @time_limited("You didn't open 'to_engine' for writing or 'from_engine.pipe' for reading in time.")
    def _open_pipes(self):
        self._to_engine_pipe = open(f"{CORE_DIRECTORY}/submission{self.player_id}/io/to_engine.pipe", "r")
        self._from_engine_pipe = open(f"{CORE_DIRECTORY}/submission{self.player_id}/io/from_engine.pipe", "w")


    def _send(self, data: str):
        self._from_engine_pipe.write(str(len(data)) + ",")
        self._from_engine_pipe.write(data)
        self._from_engine_pipe.flush()


    def _receive(self) -> str:

        # Read size of message.
        buffer = bytearray()
        while len(buffer) < math.floor(math.log10(MAX_CHARACTERS_READ)) + 1 and (len(buffer) == 0 or buffer[-1] != ord(",")):
            buffer.extend(self._to_engine_pipe.read(1).encode())

        if buffer[-1] == ord(","):
            size = int(buffer[0:-1].decode())
        else:
            raise InvalidResponseException(player_id=self.player_id, error_message="Malformed message size on message written to 'to_engine.pipe'.")
        
        if size > MAX_CHARACTERS_READ:
            raise InvalidResponseException(player_id=self.player_id, error_message=f"Message size too long for message written to 'to_engine.pipe', {size} > {MAX_CHARACTERS_READ}.")
        
        # Read message.
        buffer = bytearray()
        while len(buffer) < size:
            buffer.extend(bytearray(self._to_engine_pipe.read((size - len(buffer)) % READ_CHUNK_SIZE).encode()))

        return buffer.decode()


    @handle_invalid
    @handle_sigpipe
    @time_limited()
    def _query_move(self, query: BaseQuery, response: Type[T2], state: State) -> T2:
        self._send(query.model_dump_json())

        _response = self._receive()
        return response.model_validate_json(_response, context={"state": state, "player": self.player_id, "query": query})

    def _get_record_update_dict(self, state: State):
        if self._record_update_watermark >= len(state.recording):
            raise RuntimeError("Record update watermark out of sync with state, did you try to send two queries without committing the first?")
        result = dict([(i, x.get_censored(self.player_id)) for i, x in enumerate(state.recording[self._record_update_watermark:])])
        self._record_update_watermark = len(state.recording)
        return result

    def query_claim_territory(self, state: State) -> MoveClaimTerritory:
        query = QueryClaimTerritory(update=self._get_record_update_dict(state))
        return self._query_move(query, MoveClaimTerritory, state)


    def query_place_initial_troop(self, state: State) -> MovePlaceInitialTroop:
        query = QueryPlaceInitialTroop(update=self._get_record_update_dict(state))
        return self._query_move(query, MovePlaceInitialTroop, state)


    def query_attack(self, state: State) -> MoveAttack:
        query = QueryAttack(update=self._get_record_update_dict(state))
        return self._query_move(query, MoveAttack, state)


    def query_defend(self, state: State, move_attack_id: int) -> MoveDefend:
        query = QueryDefend(move_attack_id=move_attack_id, update=self._get_record_update_dict(state))
        return self._query_move(query, MoveDefend, state)
    

    def query_troops_after_attack(self, state: State, record_attack_id: int) -> MoveDefend:
        query = QueryTroopsAfterAttack(record_attack_id=record_attack_id, update=self._get_record_update_dict(state))
        return self._query_move(query, MoveDefend, state)
        

    def query_distribute_troops(self, state: State, cause: Union[Literal["turn_started"], Literal["player_eliminated"]]) -> MoveDistributeTroops:
        query = QueryDistributeTroops(cause=cause, update=self._get_record_update_dict(state))
        return self._query_move(query, MoveDistributeTroops, state) 
    

    def query_redeem_cards(self, state: State, cause: Union[Literal["turn_started"], Literal["player_eliminated"]]) -> MoveRedeemCards:
        query = QueryRedeemCards(cause=cause, update=self._get_record_update_dict(state))
        return self._query_move(query, MoveRedeemCards, state) 
    

    def query_fortify(self, state: State) -> MoveFortify:
        query = QueryFortifyTerritory(update=self._get_record_update_dict(state))
        return self._query_move(query, MoveFortify, state) 


if __name__ == "__main__":
    state = State()
    connection = PlayerConnection(player_id=0)
    players = [Player.factory(0, 25)]

    turn_order = [x for x in range(5)]
    random.shuffle(turn_order)
    record_turn_order = RecordStartGame(turn_order=turn_order, players=[player.get_public() for player in players])
    state.commit(record_turn_order)

    try:
        response = connection.query_claim_territory(state)
        state.commit(response)
        print(state.territories)
    except PlayerException as e:
        raise e