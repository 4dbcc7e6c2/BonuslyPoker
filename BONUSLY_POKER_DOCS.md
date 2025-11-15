# Bonusly Poker App – Documentation

This document explains the structure and behavior of the Bonusly Poker App.  
It describes each class, method, and important concept, without including the code itself.  
Use this as a reference when maintaining, extending, or understanding the program.

---

# Table of Contents
1. [Overview](#overview)  
2. [PixelHeadingRenderer](#pixelheadingrenderer)  
3. [Player](#player)  
4. [Game](#game)  
   - [Recording Rounds](#recording-rounds)  
   - [Determining a Winner](#determining-a-winner)  
   - [Summaries](#summaries)  
5. [BonuslyPokerApp](#bonuslypokerapp)  
   - [Game Setup](#game-setup)  
   - [Settlements](#settlements)  
   - [Saving Session Data](#saving-session-data)  
   - [Running the App](#running-the-app)  
6. [main() Entry Point](#main-entry-point)

---

# Overview

**Bonusly Poker App** is a command-line application for tracking a poker-style game where players “bet” units of Bonusly rather than chips or money.

The app supports:

- Multiple players  
- Recording each player's actions per round  
- Automatic pot tracking  
- Per-game and per-session net result computation  
- Suggested settlement transfers  
- Optional JSON export of the session  
- Optional ASCII/pixel-art “banner headings”

---

# PixelHeadingRenderer

## Purpose
Renders a randomly styled ASCII/pixel-art heading at the top of the terminal.  
Used at the start of the application session.

## Key Behavior
- Optionally clears the terminal window.  
- Uses the `pyfiglet` library (if installed) to render stylized ASCII text; otherwise falls back to a simple `== text ==`.  
- Converts ASCII art into block-character “pixel art.”  
- Randomly varies font and block characters for novel headings each run.  
- Optionally draws a border around the pixel-art output.

---

# Player

## Purpose
Represents an individual participant in a Bonusly Poker game.

## Stored Information
- **name** – Player’s display name.  
- **starting_stack** – Maximum Bonusly the player can distribute in a game.  
- **stack** – Bonusly remaining after bets.  
- **bets** – List of `(round_number, amount)` entries.  
- **actions** – List of `(round_number, action)` entries.

## Methods

### `record_action(round_number, action, amount)`
Records a single action (e.g., "fold", "call", "bet") for the player:

- Logs the bet and action.
- Reduces player's remaining stack.

### `total_bet` property
Returns total Bonusly the player has contributed to the pot.

### `to_dict()`
Returns a JSON-friendly dictionary encoding the player's entire state.

---

# Game

## Purpose
Tracks the complete state of a single Bonusly Poker game.

This includes:

- Player list and configured roles (Dealer, Big Blind, Small Blind)  
- Round number  
- Pot size  
- Global action history  
- Winner and net results  

## Game Attributes
- **players** – List of `Player` objects  
- **dealer**, **big_blind**, **small_blind** – Role assignments  
- **pot** – Integer value of current pot  
- **round** – Current betting round number  
- **history** – Chronological list of action dictionaries  
- **winner** – Name of winning player  
- **net_results** – Mapping of player → net Bonusly gain/loss

---

## Recording Rounds

### `record_round(input_func, print_func)`
Records a complete betting round, where each player takes exactly one turn.

During the process:

- Asks each player for their action.  
- If the action requires betting (bet, raise, call, all-in), collects and validates the bet amount.  
- Updates:
  - Player actions
  - Player stacks
  - Game pot
  - Global history log
- Moves to next round after all players have acted.

---

## Determining a Winner

### `set_winner(winner_name)`
Sets the game’s winner and computes net results.

Net results:

- **Winner**: `+pot - total_bet`  
- **Others**: `-total_bet`

Ensures `winner_name` matches a known player.

---

## Summaries

### `summarise(print_func)`
Prints a human-readable summary, including:

- Dealer and blind assignments  
- Total pot  
- Per-player contributions and remaining stacks  
- Winner and per-game net results  
- Chronological action history  

### `to_dict()`
Serializes the entire game state into a structured dictionary suitable for JSON.

---

# BonuslyPokerApp

## Purpose
Provides the full interactive user interface for running a Bonusly Poker session, handling:

- Game setup  
- Round recording  
- Winner assignment  
- Session-wide summaries  
- Suggested settlements  
- JSON export  

## Initialization
The class can take custom `input_func` and `print_func` functions for testing or custom UI layers.  
Defaults to `input` and `print`.

---

## Game Setup

### `_setup_game()`
Handles interactive setup for a new game:

On the *first game* in a session, it asks:

- Number of players  
- Names (in table order)  
- Per-game Bonusly limits (starting stacks)  

These per-player configurations are **cached** so subsequent games reuse them.

Then it:

- Displays a Bonusly→chip mapping (“unit chip value”).  
- Prompts for dealer, big blind, and small blind (validated).  
- Creates and returns a fully initialized `Game` instance.

---

## Settlements

### `_calculate_settlements(net_totals)`
Given per-player net totals over the entire session:

- Identifies debtors and creditors.
- Computes a list of suggested transfers to settle all totals to zero.
- Uses a simple greedy algorithm.

Returns entries like:

```json
{"from": "<debtor>", "to": "<creditor>", "amount": 50}
```

---

## Saving Session Data

### `_save_session_json(session_data)`
Prompts user for a filename (defaults to `bonusly_poker_results.json`) and saves session data as nicely formatted JSON.

---

## Running the App

### `run()`
Controls the full interactive flow:

1. Renders pixel-art heading  
2. Repeatedly:
   - Sets up a new game  
   - Records one or more rounds  
   - Prompts for a winner  
   - Summarizes the game  
   - Asks whether to play another game  

3. After all games:
   - Aggregates net totals across games  
   - Computes settlements  
   - Displays session summary  
   - Saves the full session as JSON  

---

# main() Entry Point

### `main()`
A simple convenience function:

- Instantiates `BonuslyPokerApp`
- Calls its `.run()` method  
- Allows running the script via:

```bash
python bonusly_poker.py
```
