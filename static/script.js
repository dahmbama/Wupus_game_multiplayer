// Store the current player position (initially set to box 7)
const adjacent_list = {1: [2, 5],
              2: [1, 3, 6],
              3: [2, 4, 7],
              4: [3, 8],
              5: [1, 6, 9],
              6: [2, 5, 7, 10],
              7: [3, 6, 8, 11],
              8: [4, 7, 12],
              9: [5, 10, 13],
              10: [6, 9, 11, 14],
              11: [7, 10, 12, 15],
              12: [8, 11, 16],
              13: [9, 14],
              14: [10, 13, 15],
              15: [11, 14, 16],
              16: [12, 15]};

const socket = io('http://192.168.4.121:5000');
let currentPlayerId; // Variable to store the current player's ID
let game_id;
let player_position;
let other_player_position;
let is_alive = true;
socket.on('player_id', (data) => {
    currentPlayerId = data.player_id;
    console.log("Received Player ID: ", currentPlayerId);
    // Now you can use currentPlayerId in your game logic
});
socket.on('connect', () => {
    console.log('Connected to the server');    
});


// Handle disconnect event
socket.on('disconnect', () => {
    console.log('Disconnected from the server');
    // Handle disconnection logic...
});

function handleGridClick(event) {
    if (is_alive) {
        const clickedItem = event.target;

        const clickedItemId = parseInt(clickedItem.id.split('grid-item')[1], 10); 
        if (adjacent_list[player_position + 1].includes(clickedItemId + 1)) {
            const moveData = {
                player_id: currentPlayerId,
                new_position: [Math.floor(clickedItemId / 4), clickedItemId % 4]
            };
            socket.emit('move', moveData);
        }
    }
    else {
        alert("You can't move because you are dead")
    }
    
}


function updateGrid(new_state, position) {
    if (new_state.player_data.player_id == currentPlayerId) {
        previos_box = document.getElementById('grid-item' + player_position + '-player');
        effect_box = document.getElementById('grid-item' + (position[0] * 4 + position[1]) + '-effects');
        let effects = "";
        if (new_state.player_data.environmental_cues.breeze){
            effects += "Breeze ";
        }
        if (new_state.player_data.environmental_cues.stench){
            effects += "Stench ";
        }
        if (new_state.player_data.environmental_cues.glare){
            effects += "Glare ";
        }
        if (effect_box.innerHTML == ""){
            effect_box.innerHTML = effects;
        }
        console.log('grid-item' + player_position + '-player');
        previos_box.innerHTML = '';
        new_box = document.getElementById('grid-item' + (position[0] * 4 + position[1]) + '-player');
        new_box.innerHTML = 'You';
    }
    else {
        previos_box = document.getElementById('grid-item' + other_player_position + '-player');
        previos_box.innerHTML = '';
        new_box = document.getElementById('grid-item' + (position[0] * 4 + position[1]) + '-player');
        new_box.innerHTML = 'Player';
    }
}

// Handle move update event
socket.on('move_update', (data) => {
    console.log('Move successful', data.new_state);
    if (data.new_state.player_data.player_id == currentPlayerId) {
        console.log('Move successful', data.new_state);
        // Update your game UI based on the new state...
        if (data.new_state.game_over) {
            alert('YOU WIN!');
        }
        if (!data.new_state.player_data.is_alive) {
            alert('YOU LOSE!');
            is_alive = false;
            updateGrid(data.new_state, data.new_state.player_data.position);
        }
    }
    // Update your game UI based on the new state...
    if (data.new_state.player_data.player_id == currentPlayerId) {
        updateGrid(data.new_state, data.new_state.player_data.position);
        position = data.new_state.player_data.position;
        player_position = position[0] * 4 + position[1];
    }
    else{
        updateGrid(data.new_state, data.new_state.player_data.position);
        position = data.new_state.player_data.position;
        other_player_position = position[0] * 4 + position[1];
    }
});

// Handle move error event
socket.on('move_error', (error) => {
    console.error('Move error', error.error);
    // Handle error feedback...
});

// Example of requesting the game state
// socket.emit('game_state');

// Handle game state update event
socket.on('game_state_update', (data) => {
    // Update your game UI based on the new state...
    if (data.player_data.player_id == currentPlayerId) {
        console.log('you player', data);
        player_position = data.player_data.position;
        // player2_position = data.players[1].position;
        player_position = player_position[0] * 4 + player_position[1];
        // player2_position = player2_position[0] * 4 + player2_position[1];
        player_box = document.getElementById('grid-item' + player_position + '-player');
        // player2_box = document.getElementById('grid-item' + player2_position + '-player');
        player_box.innerHTML = 'You';
        // player2_box.innerHTML = 'P2';
    }
    else {
        console.log('other_player', data);
        other_player_position = data.player_data.position;
        // player2_position = data.players[1].position;
        other_player_position = other_player_position[0] * 4 + other_player_position[1];
        // player2_position = player2_position[0] * 4 + player2_position[1];
        player_box = document.getElementById('grid-item' + other_player_position + '-player');
        // player2_box = document.getElementById('grid-item' + player2_position + '-player');
        player_box.innerHTML = 'Player';
    }
});

// Handle game state error event
socket.on('game_state_error', (error) => {
    console.error('Game state error', error.error);
    // Handle error feedback...
});

socket.on('player_joined', (data) => {
    console.log(data.message);
    // Update the UI to reflect that a new player has joined.
});

socket.on('waiting_for_opponent', (data) => {
    console.log(data.message);
    // Update the UI to show that the player is waiting for an opponent.
});

socket.on('join_error', (error) => {
    console.error(error.error);
    // Display an error message to the user.
});


socket.on('game_state_update', (data) => {
    updateGrid(data.new_state); // Example function to update the UI based on the new game state
});

document.getElementById('startGameBtn').addEventListener('click', function() {
    console.log("Start Game button clicked. Emitting 'play_game' event.");
    socket.emit('play_game');
});

socket.on('game_started', (data) => {
    console.log(data);
       // Here, you can request the player ID and the game state
    // socket.emit('request_player_id');
    currentPlayerId = data.player_id
    console.log("Requesting player ID and game state.");
    socket.emit('game_state', {player_id: currentPlayerId});
});
