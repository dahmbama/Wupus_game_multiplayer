# This class is encabsulating the game logic, mechanics and rules, should be comperhansive
# It sets the rules, initiates the state, places the hazards and checks for endgame and winning conditions 
import random
from player import Player
import time
import threading
GRID_SIZE = 4   # minimzed from 5*5 as instructed to keep it simple
class WumpusGame:
    TIME_LIMIT = 180  # 3 minutes is the game length, maybe should be shorter 
    games = {}  # Dictionary to manage multiple game instances
    game_locks = {}  # To manage locks for each game for thread safety

    @classmethod
    def create_new_game(cls, game_id):
        with threading.Lock():
            if game_id in cls.games:
                raise ValueError(f"Game ID {game_id} already exists.")
            cls.games[game_id] = WumpusGame(game_id)
            cls.game_locks[game_id] = threading.Lock()
        return game_id  # Return the game_id of the newly created game

    @classmethod
    def get_game(cls, game_id):
        """Retrieve an existing game instance by its ID."""
        return cls.games.get(game_id)

    def end_game(self):
        # End game logic
        self.game_over = True
        # Additional logic to determine the winner or other end-game scenarios
        # ...
        # Cleanup the game
        WumpusGame.cleanup_game(self.game_id)

    @classmethod
    def cleanup_game(cls, game_id):
        # Cleanup logic for a finished game
        with cls.game_locks[game_id]:
            del cls.games[game_id]
            del cls.game_locks[game_id]

    def __init__(self, game_id):
        self.game_id = game_id
        self.start_time = time.time()
        self.grid = self.init_grid()
        self.players = []   # Should be two
        self.wumpuses = []  # Initialize the list for Wumpuses
        self.pits = []      # Initialize the list for Pits
        self.game_started = False
        #self.place_players()    # Corners
        self.place_hazards('PIT', 2)  # Assuming 2 pits, should not be adjacent on in corners
        self.place_hazards('W', 2)    # Assuming 2 Wumpuses, should not be adjacent on in corners
        self.game_over = False
        self.winner = None
        self.start_GAME = False

    def add_player(self, player_id, name):
        with self.game_locks[self.game_id]:
            if any(p.player_id == player_id for p in self.players):
                raise ValueError(f"Player ID {player_id} already exists in game {self.game_id}.")
            if len(self.players) >= 2:
                raise ValueError("Maximum number of players reached.")

            # Determine the start position for the new player
            start_position = self.determine_start_position()
            player = Player(player_id, name, start_position=start_position)
            self.players.append(player)
            self.grid[start_position[0]][start_position[1]] = 'P'

            self.check_start_conditions()

    def determine_start_position(self):
        """Determine the start position for a new player."""
        # Implement logic to determine where the new player should start
        # Example: (0, 0) for the first player, (GRID_SIZE-1, GRID_SIZE-1) for the second
        if len(self.players) == 0:
            return (0, 0)
        elif len(self.players) == 1:
            return (GRID_SIZE-1, GRID_SIZE-1)
        else:
            raise ValueError("No available positions for new player.")

    def check_start_conditions(self):
        """Check if the game meets the conditions to start."""
        if len(self.players) == 2 and not self.game_started:
            self.place_treasure_equidistant()
            self.start_game()
            self.start_GAME = True
        else:
            self.start_GAME = False

    def start_game(self):
        """Start the game."""
        self.game_started = True

    def get_player_pov_game_state(self, player_id):
        """Return the game state from the perspective of the specified player."""
        player = next(p for p in self.players if p.player_id == player_id)
        pov_grid = [['?' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if (x, y) in player.visited:
                    # Map the grid content to the specified naming convention
                    grid_content = self.grid[x][y]
                    if 'P' in grid_content:
                        pov_grid[x][y] = 'P'
                    elif 'T' in grid_content:
                        pov_grid[x][y] = 'T'
                    elif 'PIT' in grid_content:
                        pov_grid[x][y] = 'PIT'
                    elif 'W' in grid_content:
                        pov_grid[x][y] = 'W'
                    else:
                        pov_grid[x][y] = 'V'  # V for visited

                    # Add adjacent cues
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            if 'B' in self.grid[nx][ny] and pov_grid[nx][ny] == '?':
                                pov_grid[nx][ny] = 'B'  # Breeze
                            elif 'S' in self.grid[nx][ny] and pov_grid[nx][ny] == '?':
                                pov_grid[nx][ny] = 'S'  # Stench

        return {
            'pov_grid': pov_grid,
            'player_data': player.to_dict(),
            'game_over': self.game_over,
            'winner': self.winner,
            'time_left': self.get_time_left()
        }

    def init_grid(self):
        """Initialize an empty grid."""
        return [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def place_hazards(self, item, count):
        placed = 0
        while placed < count:
            x, y = self.random_position()
            if self.grid[x][y] == '':
                self.grid[x][y] = item
                placed += 1
                if item == 'PIT':
                    self.pits.append((x, y))
                elif item == 'W':
                    self.wumpuses.append((x, y))

    def is_reachable(self, start, end):
        """Check if 'end' is reachable from 'start' without passing through hazards. Use BFS"""
        queue = [start]
        visited = set()
        while queue:
            position = queue.pop(0)
            if position == end:
                return True
            if position not in visited:
                visited.add(position)
                x, y = position
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_position = (x + dx, y + dy)
                    if self.is_valid_position(new_position) and not self.is_hazard_position(new_position):
                        queue.append(new_position)
        return False

    def is_valid_position(self, position):
        """Check if a position is within the grid bounds."""
        x, y = position
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

    def is_hazard_position(self, position):
        """Check if a position contains a hazard (Pit or Wumpus)."""
        return position in self.wumpuses or position in self.pits

    def place_treasure_equidistant(self):
        """Place the treasure in a location equidistant from all players and accessible."""
        possible_positions = []
        player_positions = [player.position for player in self.players]
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if self.grid[x][y] == '':
                    distances = [abs(x - px) + abs(y - py) for px, py in player_positions]
                    if max(distances) == min(distances):
                        if all(self.is_reachable((px, py), (x, y)) for px, py in player_positions):
                            possible_positions.append((x, y))
        self.treasure_position = random.choice(possible_positions) if possible_positions else (0, 0)
        self.grid[self.treasure_position[0]][self.treasure_position[1]] = 'T'

    def get_game_state(self):
        """Return the current game state."""
        return {
            'grid': self.grid,
            'players': [player.__dict__ for player in self.players],
            'treasure_position': self.treasure_position,
            'wumpuses': self.wumpuses,
            'pits': self.pits,
            'game_over': self.game_over,
            'winner': self.winner,
            'time_left': self.get_time_left()
        }

    def random_position(self):
        """Generate a random position within the grid."""
        return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)

    def move_player(self, player_id, new_position):
        """Move a player to a new position and update the game state."""
        if self.is_time_up():
            self.game_over = True
            return
        player = next((p for p in self.players if p.player_id == player_id), None)
        if player and player.is_valid_move(new_position):
            player.update_position(new_position)
            self.check_interactions(player)
            self.update_cues(player)

    def check_interactions(self, player):
        """Check for interactions with treasure, Wumpuses, or pits."""
        if player.position == self.treasure_position:
            self.game_over = True
            self.winner = player.player_id
        elif player.position in self.wumpuses or player.position in self.pits:
            player.set_status(False)
            if all(not p.is_alive for p in self.players):
                self.game_over = True

    def update_cues(self, player):
        x, y = player.position
        cues = {'glare': False, 'stench': False, 'breeze': False}
        adjacent_positions = [(x + dx, y + dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]]
        for pos in adjacent_positions:
            if pos == self.treasure_position:
                cues['glare'] = True
            if pos in self.wumpuses:
                cues['stench'] = True
            if pos in self.pits:
                cues['breeze'] = True
        player.update_environmental_cues(cues)


    def is_game_over(self):
        """Check if the game is over."""
        return self.game_over
    def is_time_up(self):
       """Check if the game time limit has been reached."""
       return (time.time() - self.start_time) >= WumpusGame.TIME_LIMIT
    def get_time_left(self):
        """Return the time left in the game."""
        return WumpusGame.TIME_LIMIT - (time.time() - self.start_time)