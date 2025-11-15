import os
import random
import json
from typing import List, Tuple, Dict, Callable, Optional

# Optional: use pyfiglet if available for nicer ASCII art
try:
    from pyfiglet import Figlet
except ImportError:
    Figlet = None


class PixelHeadingRenderer:
    """Render a simple ASCII-art heading using pyfiglet if available."""

    @staticmethod
    def render(text: str = "Bonusly Poker App") -> None:
        """Display a plain ASCII-art heading.

        Uses pyfiglet if available to render a large ASCII banner. If
        pyfiglet is not installed, falls back to a simple text line.
        """

        # Clear the terminal so the heading appears at the top (optional)
        os.system("cls" if os.name == "nt" else "clear")

        if Figlet is not None:
            # Use a small set of consistent fonts
            possible_fonts = [
                "big",
                "slant",
                "standard",
                "banner3-D",
            ]
            fig = Figlet(font=random.choice(possible_fonts))
            banner = fig.renderText(text)
            print(banner)
        else:
            # Simple fallback if pyfiglet isn't installed
            print("\n========================")
            print(f"  {text}")
            print("========================\n")


class Player:

    def __init__(self, name: str, starting_stack: int) -> None:
        self.name: str = name
        self.starting_stack: int = starting_stack
        self.stack: int = starting_stack
        self.bets: List[Tuple[int, int]] = []
        self.actions: List[Tuple[int, str]] = []
        # True if this player has, at least once in this game, chosen to
        # proceed with a bet that pushed them below their starting Bonusly.
        self.went_negative_override: bool = False

    def record_action(self, round_number: int, action: str, amount: int) -> None:
        self.bets.append((round_number, amount))
        self.actions.append((round_number, action))
        self.stack -= amount

    @property
    def total_bet(self) -> int:
        return sum(amount for _, amount in self.bets)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "starting_stack": self.starting_stack,
            "ending_stack": self.stack,
            "total_bet": self.total_bet,
            "bets": self.bets,
            "actions": self.actions,
            "went_negative_override": self.went_negative_override,
        }


class Game:

    def __init__(
        self,
        players: List[Player],
        dealer: str,
        big_blind: str,
        small_blind: str,
        base_unit: int,
        chip_denoms: List[int],
    ) -> None:
        self.players: List[Player] = players
        self.dealer: str = dealer
        self.big_blind: str = big_blind
        self.small_blind: str = small_blind
        # 1-unit chip corresponds to this many Bonusly points
        self.base_unit: int = base_unit
        # Available chip denominations (in "units", e.g. [1, 5, 25, 100])
        self.chip_denoms: List[int] = chip_denoms
        self.pot: int = 0
        self.round: int = 1
        self.history: List[Dict[str, object]] = []
        self.winner: Optional[str] = None
        self.net_results: Dict[str, int] = {}

    def record_round(
        self,
        input_func: Callable[[str], str] = input,
        print_func: Callable[[str], None] = print,
    ) -> None:

        round_no = self.round
        print_func(f"\n--- Recording actions for round {round_no} ---")

        for player in self.players:
            print_func(f"\nIt's {player.name}'s turn.")
            action = input_func(
                "What did they do? (fold/check/call/bet/raise/all-in/other): "
            ).strip().lower()

            amount_bonusly = 0
            if action in ("bet", "raise", "all-in", "call"):
                while True:
                    print_func(
                        f"Enter chip counts for {player.name} using denominations "
                        f"{self.chip_denoms} (these will be converted to Bonusly)."
                    )
                    total_units = 0
                    for denom in self.chip_denoms:
                        while True:
                            count_str = input_func(
                                f"  How many {denom}-value chips? (0 if none): "
                            ).strip()
                            if not count_str:
                                count_str = "0"
                            try:
                                count = int(count_str)
                                if count < 0:
                                    print_func("  Count cannot be negative.")
                                    continue
                                total_units += count * denom
                                break
                            except ValueError:
                                print_func("  Please enter a whole number.")
                    amount_bonusly = total_units * self.base_unit

                    # Check whether this bet would push the player below their starting
                    # Bonusly (i.e. into a negative effective balance).
                    projected_total_bet = player.total_bet + amount_bonusly
                    if projected_total_bet > player.starting_stack:
                        red = "\033[91m"
                        reset = "\033[0m"
                        print_func(
                            f"{red}Warning: this bet would put {player.name} below their "
                            f"starting Bonusly ({projected_total_bet} > "
                            f"{player.starting_stack}).{reset}"
                        )
                        confirm = input_func(
                            "Proceed with this bet anyway? (y/n): "
                        ).strip().lower()
                        if confirm != "y":
                            print_func("Re-enter chip counts for this action.")
                            continue
                        # User chose to proceed despite going below starting Bonusly.
                        player.went_negative_override = True

                    break

            # Update player and pot state (amount_bonusly will be 0 for non-betting actions)
            player.record_action(round_no, action, amount_bonusly)
            self.pot += amount_bonusly

            # Append to global history
            self.history.append(
                {
                    "round": round_no,
                    "player": player.name,
                    "action": action,
                    "amount": amount_bonusly,
                    "pot_after": self.pot,
                }
            )

            print_func(
                f"Recorded: {player.name} {action} for {amount_bonusly} Bonusly. "
                f"Pot is now {self.pot}."
            )

        # Move to the next round once each player has taken a turn
        self.round += 1

    def set_winner(self, winner_name: str) -> None:

        if winner_name not in [p.name for p in self.players]:
            raise ValueError(f"Unknown winner name: {winner_name!r}")

        self.winner = winner_name
        self.net_results = {}

        for player in self.players:
            net = -player.total_bet
            if player.name == winner_name:
                net += self.pot
            self.net_results[player.name] = net

    def summarise(self, print_func: Callable[[str], None] = print) -> None:

        print_func("\n=== Game Summary ===")
        print_func(f"Dealer: {self.dealer}")
        print_func(f"Small blind: {self.small_blind}")
        print_func(f"Big blind: {self.big_blind}")
        print_func(f"Total pot: {self.pot}")

        print_func("\nPlayer details:")
        for player in self.players:
            print_func(
                f"- {player.name}: bet {player.total_bet} total, "
                f"stack remaining {player.stack} (starting {player.starting_stack})"
            )

        if self.winner is not None:
            print_func(f"\nWinner: {self.winner}")
            print_func("Net results (this game):")
            for name, net in self.net_results.items():
                print_func(f"  {name}: {net:+d}")

        print_func("\nAction history (in order):")
        for entry in self.history:
            print_func(
                f"Round {entry['round']} - {entry['player']} {entry['action']} "
                f"{entry['amount']} (pot after: {entry['pot_after']})"
            )

    def to_dict(self) -> Dict[str, object]:
        """Serialize the entire game into a JSON-friendly dict."""

        return {
            "dealer": self.dealer,
            "big_blind": self.big_blind,
            "small_blind": self.small_blind,
            "pot": self.pot,
            "rounds_played": self.round - 1,
            "winner": self.winner,
            "players": [p.to_dict() for p in self.players],
            "history": self.history,
            "net_results": self.net_results,
            "base_unit": self.base_unit,
            "chip_denoms": self.chip_denoms,
        }


class BonuslyPokerApp:

    def __init__(
        self,
        input_func: Callable[[str], str] = input,
        print_func: Callable[[str], None] = print,
    ) -> None:

        self.input: Callable[[str], str] = input_func
        self.print: Callable[[str], None] = print_func
        self.games: List[Game] = []
        # Cached per-session player configuration: list of (name, starting_stack)
        self.player_configs: Optional[List[Tuple[str, int]]] = None

    def _setup_game(self) -> Game:

        print_fn = self.print
        input_fn = self.input

        print_fn("\n=== Setup Bonusly Poker Game ===")

        # On the first game, collect player names and per-game Bonusly limits
        if self.player_configs is None:
            while True:
                try:
                    num_players = int(
                        input_fn("Please specify the number of people playing: ")
                    )
                    if num_players < 2:
                        print_fn("You need at least 2 players.")
                        continue
                    break
                except ValueError:
                    print_fn("Please enter a valid number.")

            player_configs: List[Tuple[str, int]] = []
            for i in range(num_players):
                name = input_fn(
                    f"Please specify user name #{i + 1} in playing order: "
                )
                while True:
                    try:
                        stack = int(
                            input_fn(
                                f"Total Bonusly {name} can distribute in a single game: "
                            )
                        )
                        if stack <= 0:
                            print_fn("Starting Bonusly must be positive.")
                            continue
                        break
                    except ValueError:
                        print_fn("Please enter a valid integer amount.")
                player_configs.append((name, stack))

            self.player_configs = player_configs
        else:
            player_configs = self.player_configs
            print_fn("Reusing player configuration from earlier in the session:")
            for name, stack in player_configs:
                print_fn(f"- {name}: {stack} Bonusly per game")

        # Compute and display a chip mapping based on the lowest starting Bonusly
        min_stack = min(stack for _, stack in player_configs)

        # First attempt: make a 100-value chip equal to 25% of the lowest stack.
        # That means:
        #   chip_100_value = 0.25 * min_stack
        #   chip_100_value = 100 * base_unit  ->  base_unit = (0.25 * min_stack) / 100
        chip_100_value = int(min_stack * 0.25)
        base_unit = chip_100_value // 100  # 1-unit chip = this many Bonusly

        # If that would make a 1-unit chip less than 1 Bonusly, fall back to the
        # original mapping of roughly 100 unit chips for the lowest stack.
        if base_unit < 1:
            base_unit = max(1, min_stack // 100)  # 1 unit chip = this many Bonusly
            mapping_note = (
                "~100 unit chips for the lowest starting stack (fallback mapping)."
            )
        else:
            mapping_note = (
                "100-unit chip is ~25% of the lowest starting stack."
            )

        chip_denoms = [1, 5, 25, 100]

        print_fn("\n=== Bonusly to Poker Chip Mapping ===")
        print_fn(f"Lowest starting Bonusly: {min_stack}")
        print_fn(f"Using 1-unit chip = {base_unit} Bonusly ({mapping_note})")
        print_fn("Chip denominations:")
        for d in chip_denoms:
            print_fn(f"  Chip {d}: {d * base_unit} Bonusly")
        print_fn("======================================")

        player_names = [name for name, _ in player_configs]

        # Create Player objects with the configured starting stacks
        players: List[Player] = [
            Player(name=name, starting_stack=stack) for name, stack in player_configs
        ]

        def choose_role(prompt: str) -> str:
            """Prompt until a valid player name is chosen for a role."""

            while True:
                name = input_fn(prompt)
                if name in player_names:
                    return name
                print_fn("That name is not in the list of players, please try again.")

        dealer = choose_role("Please specify which user is the Dealer: ")
        big_blind = choose_role("Please specify which user is the Big Blind: ")
        small_blind = choose_role("Please specify which user is the Small Blind: ")

        return Game(
            players=players,
            dealer=dealer,
            big_blind=big_blind,
            small_blind=small_blind,
            base_unit=base_unit,
            chip_denoms=chip_denoms,
        )

    @staticmethod
    def _calculate_settlements(net_totals: Dict[str, int]) -> List[Dict[str, object]]:

        debtors: List[Tuple[str, int]] = [
            (name, -net) for name, net in net_totals.items() if net < 0
        ]
        creditors: List[Tuple[str, int]] = [
            (name, net) for name, net in net_totals.items() if net > 0
        ]

        settlements: List[Dict[str, object]] = []

        # Simple greedy settlement algorithm
        i = 0
        j = 0
        while i < len(debtors) and j < len(creditors):
            debtor_name, debt_amt = debtors[i]
            creditor_name, cred_amt = creditors[j]

            amount = min(debt_amt, cred_amt)
            settlements.append({"from": debtor_name, "to": creditor_name, "amount": amount})

            debt_amt -= amount
            cred_amt -= amount

            if debt_amt == 0:
                i += 1
            else:
                debtors[i] = (debtor_name, debt_amt)

            if cred_amt == 0:
                j += 1
            else:
                creditors[j] = (creditor_name, cred_amt)

        return settlements

    def _save_session_json(
        self,
        session_data: Dict[str, object],
    ) -> None:
        """Prompt for a filename and save the session data as JSON."""

        filename = self.input(
            "\nEnter JSON filename to save results "
            "(blank for 'bonusly_poker_results.json'): "
        ).strip()
        if not filename:
            filename = "bonusly_poker_results.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            self.print(f"Session data saved to {filename}")
        except OSError as exc:
            self.print(f"Failed to save session data: {exc}")

    def run(self) -> None:
        """Run the Bonusly Poker App interactive session.

        This is the high-level entry point of the application. It will:

        1. Render the pixel-art heading using
           :class:`PixelHeadingRenderer`.
        2. Repeatedly:

           a. Call :meth:`_setup_game` to build a new :class:`Game`.
           b. Record one or more betting rounds via
              :meth:`Game.record_round`.
           c. Prompt for the winner of the game and compute per-player
              net results.
           d. Display a summary for that game.
           e. Ask whether to play another game.

        3. Once the user declines to play another game, aggregate the
           net results across all games, compute suggested settlement
           transfers, display them, and save full session details to a
           JSON file.

        The method does not return anything; it orchestrates the overall
        flow of the command-line application via user input and
        terminal output.
        """

        PixelHeadingRenderer.render("Bonusly Poker App")

        # Outer loop: multiple games in a session
        while True:
            game = self._setup_game()
            self.games.append(game)

            # Inner loop: multiple rounds within a single game
            while True:
                game.record_round(input_func=self.input, print_func=self.print)
                cont_round = self.input(
                    "\nRecord another round for this game? (y/n): "
                ).strip().lower()
                if cont_round != "y":
                    break

            # Decide winner and compute per-game nets
            while True:
                winner_name = self.input(
                    "\nWho won this game? (enter player name): "
                ).strip()
                try:
                    game.set_winner(winner_name)
                    break
                except ValueError as exc:
                    self.print(str(exc))

            game.summarise(print_func=self.print)

            cont_game = self.input("\nPlay another game? (y/n): ").strip().lower()
            if cont_game != "y":
                break

        # Aggregate results across all games
        self.print("\n=== Session Summary Across All Games ===")

        net_totals: Dict[str, int] = {}
        for game in self.games:
            for name, net in game.net_results.items():
                net_totals[name] = net_totals.get(name, 0) + net

        if not net_totals:
            self.print("No games with winners were recorded. Nothing to settle.")
            return

        self.print("\nNet results across all games:")
        for name, net in net_totals.items():
            self.print(f"  {name}: {net:+d}")

        settlements = self._calculate_settlements(net_totals)

        if settlements:
            self.print("\nSuggested Bonusly transfers to settle up:")
            for s in settlements:
                self.print(
                    f"  {s['from']} -> {s['to']}: {s['amount']} Bonusly"
                )
        else:
            self.print("\nNo settlements required; everyone is even.")

        # Build JSON-serializable session structure
        session_data: Dict[str, object] = {
            "games": [g.to_dict() for g in self.games],
            "net_totals": net_totals,
            "settlements": settlements,
        }

        # Persist to disk
        self._save_session_json(session_data)


def main() -> None:
    app = BonuslyPokerApp()
    app.run()

if __name__ == "__main__":
    main()