# State Recorder

## Description

Script for RLBot which records states.

![Logo](https://github.com/Nutelladroid/StateRecorder/blob/main/logo.png?raw=true)

## How to use

**Add the script to RLBot**

Add the cfg file to RLBot. Remember to toggle State Recorder in the script section once added.

**Settings**

Check the settings:

```
tick_skip = 120  # Record every 120 ticks (120 ticks = 1s)
min_ball_height = 300  # Only record states when player0 and ball are above min_ball_height
max_distance = 350  # Only record states when player0 and ball are closer than max_distance
height_and_distance_check = False  # Enable the height and distance condition, disable for continuous recording every tick_skip
```

`height_and_distance_check` is disabled by default, but it's good for recording air dribbles from player0.

**Run Game**

Once everything is set, start a match in 1v1, 2v2, or 3v3 (no other game modes are supported yet). It will write to the file `custom_1v1.h`, `custom_2v2.h`, or `custom_3v3.h` depending on the game mode.

It can continue recording from an old file, but it's recommended to make a backup first. You can also leave the match and open a replay of the same game mode, and it will continue to record states from that replay.

## Acknowledgments

This project uses code from:

- JPK314/rlgym-compat (27 April 2024)
- RLBot/RLBot (27 April 2024)