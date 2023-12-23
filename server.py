import uuid
import time

def generate_unique_id():
    return str(uuid.uuid4())

from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO

from threading import Lock

from wumpus_game import WumpusGame
from player import Player
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
game_instances = {}
game_instance_lock = Lock()
PLAYERS_TO_START = 2  # Define minimum number of players to start a game

@socketio.on('connect')
def handle_connect():
    print(f"Client {request.sid} connected")


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    # Handle client disconnection logic here...
    for game_instance_id, game_instance in game_instances.items():
        for player in game_instance.players:
            if id(player) == request.sid:
                game_instance.players.remove(player)
                break

@socketio.on('move')
def handle_move(data):
    try:
        player_id = data['player_id']
        new_position = data['new_position']
        print(f"Client {player_id} requests move to {new_position}")
        # Find the game instance that the player belongs to
        game_instance_id = None
        for id, instance in game_instances.items():
            if player_id in [p.player_id for p in instance.players]:
                game_instance_id = id
                break
        if game_instance_id:
            # Handle move logic and emit updates to clients in the same game instance
            WumpusGame.get_game(game_instance_id).move_player(player_id, tuple(new_position))
            game_state = WumpusGame.get_game(game_instance_id).get_player_pov_game_state(player_id)
            for player in WumpusGame.get_game(game_instance_id).players:
                socketio.emit('move_update', {"message": "Move successful", "new_state": game_state, "game_id": game_instance_id}, room=player.player_id)
        else:
            raise Exception("Player not found in any game instance")
    
    except Exception as e:
        print(str(e))
        socketio.emit('move_error', {"error": str(e)})

def find_available_game_instance():
    for game_instance_id, game_instance in game_instances.items():
        if len(game_instance.players) == 1 and not game_instance.game_over:
            return game_instance_id
    return None

@socketio.on('play_game')
def handle_play_game():
    print(f"Client {request.sid} requests play game")
    find = find_available_game_instance()

    #player = Player(player_id, "Player Name")
    if find==None:
        game_instance_id = generate_unique_id()
        WumpusGame.create_new_game(game_instance_id)
        game_instance = WumpusGame.get_game(game_instance_id)
        game_instances[game_instance_id] = game_instance
    else:
        game_instance_id = find
    

    if game_instance_id:
        game_instance = game_instances[game_instance_id]
        player_id = request.sid
        player_name = "Name"
        game_instance.add_player(player_id, player_name)
        if game_instance.start_GAME:
            # game_instance.start_game()
            for player in game_instance.players:
                socketio.emit('game_started', {"message": "Game has started", "game_id": game_instance_id, "player_id": player.player_id}, room=player.player_id)
    else:
        new_game_id = generate_unique_id()
        WumpusGame.create_new_game(new_game_id)
        game_instances[new_game_id] = WumpusGame.get_game(new_game_id)
        game_instance = game_instances[new_game_id]
        game_instance.add_player(player_id, player_name)
        # If it's a new game instance, no need to emit 'game_started' yet
        socketio.emit('waiting_for_opponent', {"message": "Waiting for opponent"}, room=player_id)

@socketio.on('game_state')
def handle_game_state(data):
    try:
        player_id = data['player_id']
        game_instance_id = None
        for id, instance in game_instances.items():

            if player_id in [p.player_id for p in instance.players]:
                game_instance_id = id
                break
        if game_instance_id:
            game_state = WumpusGame.get_game(game_instance_id).get_player_pov_game_state(player_id)
            socketio.emit('game_state_update', game_state, room=player_id)
        else:
            raise Exception("Player not found in any game instance")
    
    except Exception as e:
        socketio.emit('game_state_error', {"error": str(e)})

@app.route('/')
@app.route('/mainmenu.html')
def main_menu():
    return render_template('mainmenu.html')

@app.route('/game')
def game():
    return render_template('index.html')  # Added ".html"


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
