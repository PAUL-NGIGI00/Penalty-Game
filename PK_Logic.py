"""
Game logic for the penalty shootout: the core rules/state plus saving results.
"""
 
import random
import csv
from datetime import datetime
 
DIRECTIONS = ["left", "center", "right"]
TOTAL_SHOTS = 5
CSV_FILE = "match_history.csv"
 
 
class PenaltyShootoutGame:
    """Class handling the penalty shootout game logic."""
 
    def __init__(self) -> None:
        """Initialize the game."""
        self.shots_taken = 0
        self.goals_scored = 0
        self.total_shots = TOTAL_SHOTS
 
    def take_shot(self, direction: str):
        """
        Handle a penalty shot attempt.
 
        Args:
            direction (str): The direction the player chooses to shoot
                ("left", "center", or "right").
 
        Returns:
            tuple[bool, str]: (scored, keeper_direction) — whether the
            shot was a goal, and which way the keeper dove.
        """
        keeper_direction = random.choice(DIRECTIONS)
        self.shots_taken += 1
 
        scored = direction != keeper_direction
        if scored:
            self.goals_scored += 1
 
        return scored, keeper_direction
 
    @property
    def is_over(self) -> bool:
        """Whether all shots for this game have been taken."""
        return self.shots_taken >= self.total_shots
 
 
def save_result(goals: int, total: int) -> None:
    """
    Save the match result to a CSV file.
 
    Args:
        goals (int): Number of goals scored.
        total (int): Total number of shots.
    """
    try:
        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), goals, total])
    except Exception as e:
        print(f"Error saving match result: {e}")