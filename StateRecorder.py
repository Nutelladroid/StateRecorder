import time
import numpy as np
import os

from rlbot.agents.base_script import BaseScript
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket

from Utils.game_state import GameState
from Utils.physics_object import PhysicsObject
from Utils.player_data import PlayerData

# Settings
tick_skip = 120  # Record every 120 ticks
min_ball_height = 300 #only record states when player0 and ball are above min_ball_height
max_distance = 350 #only record states when player0 and ball are closer than max_distance
height_and_distance_check = False #Enable the height and distance condition, disable for continuous recording


class StateRecorder(BaseScript):
    def __init__(self):
        super().__init__("State Recorder")
        self.game_state = GameState(self.get_field_info(), tick_skip)
        self.ticks = tick_skip
        self.state_data = []
        self.num_players = 0
        self.team_size = 0
        self.existing_states_loaded = False  # Flag to track if existing states have been loaded
        self.num_existing_states = 0  # Keep track of the number of existing states

    def start(self):
        while True:
            # Wait for a packet
            packet = self.wait_game_tick_packet()

            if not packet.game_info.is_round_active:
                self.reset_game_state(packet)
                continue

            self.ticks += 1
            if self.ticks < tick_skip:
                continue
            self.ticks = 0

            self.game_state.decode(packet)
            self.reset_game_state(packet)

            self.num_players = len(self.game_state.players)
            self.team_size = self.num_players // 2

            # Load existing states from the file, if any
            if not self.existing_states_loaded:
                self.load_existing_states()

            # Check if player 0 and the ball are above the minimum height and within the maximum distance
            player_pos = self.game_state.players[0].car_data.position
            ball_pos = self.game_state.ball.position
            distance = np.linalg.norm(player_pos - ball_pos)
            if height_and_distance_check:
                if player_pos[2] > min_ball_height and ball_pos[2] > min_ball_height and distance < max_distance:
                    # Record the game state
                    self.record_state()
            else:
                # Record the game state regardless of height and distance
                self.record_state()

            # Save the recorded state data to a .h file every 120 ticks
            self.save_state_to_file()

    def record_state(self):
        state = []
        state.extend(self.game_state.ball.position)
        state.extend(self.game_state.ball.linear_velocity)
        state.extend(self.game_state.ball.angular_velocity)

        for player in self.game_state.players:
            state.extend(player.car_data.position)
            state.extend(player.car_data.euler_angles())
            state.extend(player.car_data.linear_velocity)
            state.extend(player.car_data.angular_velocity)
            state.append(player.boost_amount)

        self.state_data.append(state)

    def reset_game_state(self, packet):
        self.game_state.decode(packet)

    def load_existing_states(self):
        if self.existing_states_loaded:
            return  # Existing states have already been loaded, so skip this

        # Load the number of existing states from the appropriate .h file
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"custom_{self.team_size}v{self.team_size}.h")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                lines = f.readlines()
                if lines:
                    num_states = None
                    for line in lines:
                        if line.startswith(f"static const size_t NumCustomStates{self.team_size} ="):
                            num_states = int(line.split(" = ")[1].strip().strip(";"))
                            break
                    if num_states is not None:
                        self.num_existing_states = num_states
                        print(f"Found {num_states} existing states in {file_path}")
                    else:
                        print(f"No existing states found in {file_path}")
        else:
            print(f"No existing file found at {file_path}")

        self.existing_states_loaded = True  # Set the flag to indicate that existing states have been loaded

    def save_state_to_file(self):
        num_states = len(self.state_data)
        if num_states == 0:
            return  # Don't save if no states have been recorded

        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"custom_{self.team_size}v{self.team_size}.h")

        # Check if the file has been loaded successfully
        if self.num_players == 0 or self.team_size == 0:
            print(f"Skipping save_state_to_file() as the game state has not been loaded yet.")
            return

        try:
            # Check if the file exists, and write the header if it doesn't
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    if self.team_size == 1:
                        f.write(f"static const size_t NumCustomStates{self.team_size} = 1;\n")
                        f.write("static const float customStates1[1][35] = {\n")
                    elif self.team_size == 2:
                        f.write(f"static const size_t NumCustomStates{self.team_size} = 1;\n")
                        f.write("static const float customStates2[1][61] = {\n")
                    elif self.team_size == 3:
                        f.write(f"static const size_t NumCustomStates{self.team_size} = 1;\n")
                        f.write("static const float customStates3[1][87] = {\n")
                    else:
                        raise ValueError(f"Unsupported team size: {self.team_size}")
            else:
                # Load the existing number of states
                self.load_existing_states()

            # Append the state data to the file
            with open(file_path, "r") as f:
                lines = f.readlines()

            # Remove the closing "};" from the last line
            lines[-1] = lines[-1].rstrip(" };\n")

            with open(file_path, "w") as f:
                # Update the first line with the correct number of states
                lines[0] = f"static const size_t NumCustomStates{self.team_size} = {self.num_existing_states + 1};\n"

                # Update the second line with the correct array size
                if self.team_size == 1:
                    lines[1] = f"static const float customStates1[{self.num_existing_states + 1}][35] = {{\n"
                elif self.team_size == 2:
                    lines[1] = f"static const float customStates2[{self.num_existing_states + 1}][61] = {{\n"
                elif self.team_size == 3:
                    lines[1] = f"static const float customStates3[{self.num_existing_states + 1}][87] = {{\n"

                f.writelines(lines)
                f.write("    {" + ", ".join(["{:.6g}".format(x) for x in self.state_data[-1]]) + "},\n")
                f.write("};\n")

            self.num_existing_states += 1
            print(f"{self.num_existing_states} states currently saved in custom_{self.team_size}v{self.team_size}.h")
            self.state_data.clear()  # Clear the state_data list after saving
        except Exception as e:
            print(f"Error saving state to file: {e}")


if __name__ == "__main__":
    state_recorder = StateRecorder()
    state_recorder.start()
