"""
Pygame rendering, animation, and the app/state machine for the penalty
shootout.
 
Controls:
    LEFT ARROW / A       - shoot left
    UP / W / S / DOWN    - shoot center
    RIGHT ARROW / D      - shoot right
    (Mouse click on the three goal buttons also works.)
    R                    - restart after the game ends
    ESC                  - quit
"""
 
import sys
import math
 
import pygame
 
from PK_Logic import PenaltyShootoutGame, save_result, DIRECTIONS
 
# Config
WIDTH, HEIGHT = 900, 650
FPS = 60
 
HEADER_H = 130   
 
GRASS_GREEN = (46, 125, 50)
GRASS_GREEN_DARK = (39, 110, 44)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
SKY_BLUE = (135, 206, 250)
GOLD = (255, 215, 0)
RED = (220, 60, 60)
BLUE = (60, 100, 220)
GRAY = (90, 90, 90)
SKIN = (235, 195, 155)
 
# Goal geometry 
GOAL_TOP = HEADER_H + 20
GOAL_BOTTOM = GOAL_TOP + 170
GOAL_LEFT = 240
GOAL_RIGHT = 660
ZONE_WIDTH = (GOAL_RIGHT - GOAL_LEFT) // 3
 
SPOT = (WIDTH // 2, GOAL_BOTTOM + 220)  # penalty spot position
 
 
def zone_center_x(direction):
    idx = DIRECTIONS.index(direction)
    return GOAL_LEFT + ZONE_WIDTH * idx + ZONE_WIDTH // 2
 
 
# Drawing 
def draw_field(surface):
    surface.fill(SKY_BLUE, (0, 0, WIDTH, HEADER_H))
    surface.fill(GRASS_GREEN, (0, HEADER_H, WIDTH, HEIGHT - HEADER_H))
 
    # mow stripes
    stripe_h = 30
    y = HEADER_H
    toggle = False
    while y < HEIGHT:
        if toggle:
            pygame.draw.rect(surface, GRASS_GREEN_DARK, (0, y, WIDTH, stripe_h))
        y += stripe_h
        toggle = not toggle
 
    # penalty arc / box lines
    pygame.draw.rect(surface, WHITE, (GOAL_LEFT - 60, GOAL_TOP + 5, (GOAL_RIGHT - GOAL_LEFT) + 120, 330), 3)
    pygame.draw.circle(surface, WHITE, SPOT, 5)
 
    # goal posts
    post_w = 8
    pygame.draw.rect(surface, WHITE, (GOAL_LEFT - post_w, GOAL_TOP, post_w, GOAL_BOTTOM - GOAL_TOP))
    pygame.draw.rect(surface, WHITE, (GOAL_RIGHT, GOAL_TOP, post_w, GOAL_BOTTOM - GOAL_TOP))
    pygame.draw.rect(surface, WHITE, (GOAL_LEFT - post_w, GOAL_TOP - 8, (GOAL_RIGHT - GOAL_LEFT) + post_w * 2, 8))
 
    # net 
    for gx in range(GOAL_LEFT, GOAL_RIGHT + 1, 15):
        pygame.draw.line(surface, (220, 220, 220), (gx, GOAL_TOP), (gx, GOAL_BOTTOM), 1)
    for gy in range(GOAL_TOP, GOAL_BOTTOM + 1, 15):
        pygame.draw.line(surface, (220, 220, 220), (GOAL_LEFT, gy), (GOAL_RIGHT, gy), 1)
 
    # zone dividers 
    for i in (1, 2):
        x = GOAL_LEFT + ZONE_WIDTH * i
        pygame.draw.line(surface, (255, 255, 255, 40), (x, GOAL_TOP), (x, GOAL_BOTTOM + 40), 1)
 
 
def draw_keeper(surface, x, y, dive_progress, direction):
    """Draws a simple keeper figure, optionally diving toward `direction`."""
    target_x = zone_center_x(direction)
    cur_x = x + (target_x - x) * dive_progress
    lean = (target_x - x) * dive_progress * 0.15
    tilt = dive_progress * (30 if direction == "right" else -30 if direction == "left" else 0)
 
    body_h = 70
    cur_y = y - abs(math.sin(dive_progress * math.pi / 2)) * 10
 
    # arms out when diving
    arm_spread = 25 + dive_progress * 30
 
    keeper_surf = pygame.Surface((140, 140), pygame.SRCALPHA)
    cx, cy = 70, 70
    # torso
    pygame.draw.line(keeper_surf, (255, 200, 0), (cx, cy - body_h // 2), (cx, cy + body_h // 2), 16)
    # arms
    pygame.draw.line(keeper_surf, SKIN, (cx, cy - 15), (cx - arm_spread, cy - 35), 8)
    pygame.draw.line(keeper_surf, SKIN, (cx, cy - 15), (cx + arm_spread, cy - 35), 8)
    # legs
    pygame.draw.line(keeper_surf, BLACK, (cx, cy + body_h // 2), (cx - 18, cy + body_h // 2 + 25), 10)
    pygame.draw.line(keeper_surf, BLACK, (cx, cy + body_h // 2), (cx + 18, cy + body_h // 2 + 25), 10)
    # head
    pygame.draw.circle(keeper_surf, SKIN, (cx, cy - body_h // 2 - 12), 14)
 
    rotated = pygame.transform.rotate(keeper_surf, -tilt)
    rect = rotated.get_rect(center=(cur_x + lean, cur_y))
    surface.blit(rotated, rect)
 
 
def draw_ball(surface, pos, radius=14, spin=0):
    ball_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    c = radius + 2
    pygame.draw.circle(ball_surf, WHITE, (c, c), radius)
    pygame.draw.circle(ball_surf, BLACK, (c, c), radius, 2)
    # soccer ball 
    pygame.draw.polygon(
        ball_surf, BLACK,
        [(c + radius * 0.5 * math.cos(math.radians(a + spin)),
          c + radius * 0.5 * math.sin(math.radians(a + spin))) for a in (90, 162, 234, 306, 18)]
    )
    surface.blit(ball_surf, (pos[0] - c, pos[1] - c))
 
 
def ease_out(t):
    return 1 - (1 - t) ** 3
 
 
_FONT_CACHE = {}
 
 
def get_font(name, size, bold=True):
    key = (name, size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(name, size, bold=bold)
    return _FONT_CACHE[key]
 
 
def draw_fitted_text(surface, text, center, max_width, color, max_size=48, min_size=18, bold=True):
    """center"""
    size = max_size
    font = get_font("arial", size, bold)
    surf = font.render(text, True, color)
    while surf.get_width() > max_width and size > min_size:
        size -= 2
        font = get_font("arial", size, bold)
        surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)
    return rect
 
 
# Main Game class 
class PenaltyShootoutGUI:
    STATE_AIM = "aim"
    STATE_ANIM = "anim"
    STATE_RESULT = "result"
    STATE_GAMEOVER = "gameover"
 
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Penalty Shootout")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = get_font("arial", 22, bold=False)
 
        self.game = PenaltyShootoutGame()
        self.state = self.STATE_AIM
        self.message = "Choose your shot: LEFT / CENTER / RIGHT"
        self.sub_message = ""
        self.anim_t = 0.0
        self.anim_duration = 0.7
        self.shot_direction = None
        self.keeper_direction = "center"
        self.last_result_scored = None
        self.saved_this_game = False
        self.result_timer = 0.0
        self.result_delay = 1.4  
 
        self.buttons = self._make_buttons()
 
    def _make_buttons(self):
        btn_w, btn_h = 140, 50
        gap = 30
        total_w = btn_w * 3 + gap * 2
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT - 70
        rects = {}
        for i, d in enumerate(DIRECTIONS):
            rects[d] = pygame.Rect(start_x + i * (btn_w + gap), y, btn_w, btn_h)
        return rects
 
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
 
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if self.state == self.STATE_AIM:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.take_shot("left")
                    elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_s, pygame.K_DOWN):
                        self.take_shot("center")
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.take_shot("right")
                elif self.state == self.STATE_GAMEOVER and event.key == pygame.K_r:
                    self.restart()
                elif self.state == self.STATE_RESULT:
                    self.continue_to_next_shot()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.state == self.STATE_AIM:
                    for d, rect in self.buttons.items():
                        if rect.collidepoint(mx, my):
                            self.take_shot(d)
                elif self.state == self.STATE_GAMEOVER:
                    restart_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 70, 180, 50)
                    if restart_rect.collidepoint(mx, my):
                        self.restart()
                elif self.state == self.STATE_RESULT:
                    self.continue_to_next_shot()
 
    def take_shot(self, direction):
        scored, keeper_dir = self.game.take_shot(direction)
        self.shot_direction = direction
        self.keeper_direction = keeper_dir
        self.last_result_scored = scored
        self.anim_t = 0.0
        self.state = self.STATE_ANIM
 
    def update(self, dt):
        if self.state == self.STATE_ANIM:
            self.anim_t += dt / self.anim_duration
            if self.anim_t >= 1.0:
                self.anim_t = 1.0
                self.finish_animation()
        elif self.state == self.STATE_RESULT:
            self.result_timer += dt
            if self.result_timer >= self.result_delay:
                self.continue_to_next_shot()
 
    def finish_animation(self):
        if self.last_result_scored:
            self.message = f"GOAL! Keeper dove {self.keeper_direction}."
        else:
            self.message = f"SAVED! Keeper dove {self.keeper_direction}."
        self.sub_message = f"Score: {self.game.goals_scored}/{self.game.shots_taken}"
 
        if self.game.is_over:
            if not self.saved_this_game:
                save_result(self.game.goals_scored, self.game.total_shots)
                self.saved_this_game = True
            self.state = self.STATE_GAMEOVER
            if self.game.goals_scored > self.game.total_shots // 2:
                self.message = "YOU WIN!"
                self.sub_message = f"Final score: {self.game.goals_scored}/{self.game.total_shots}"
            else:
                self.message = "GAME OVER"
                self.sub_message = f"Final score: {self.game.goals_scored}/{self.game.total_shots}  Better luck next time!"
        else:
            self.state = self.STATE_RESULT
            self.result_timer = 0.0
 
    def continue_to_next_shot(self):
        """Move from the result screen back to aiming for the next shot."""
        if self.state != self.STATE_RESULT:
            return
        self.state = self.STATE_AIM
        self.message = "Choose your shot: LEFT / CENTER / RIGHT"
        self.sub_message = f"Score so far: {self.game.goals_scored}/{self.game.shots_taken}"
 
    def restart(self):
        self.game = PenaltyShootoutGame()
        self.state = self.STATE_AIM
        self.message = "Choose your shot: LEFT / CENTER / RIGHT"
        self.sub_message = ""
        self.saved_this_game = False
 
    def draw(self):
        draw_field(self.screen)
 
        keeper_y = GOAL_TOP + (GOAL_BOTTOM - GOAL_TOP) // 2 + 10
        keeper_x = WIDTH // 2
 
        if self.state == self.STATE_ANIM:
            t = ease_out(min(self.anim_t, 1.0))
            ball_x = SPOT[0] + (zone_center_x(self.shot_direction) - SPOT[0]) * t
            ball_y = SPOT[1] + (GOAL_TOP + 40 - SPOT[1]) * t
            dive_t = min(t * 1.4, 1.0)
            draw_keeper(self.screen, keeper_x, keeper_y, dive_t, self.keeper_direction)
            draw_ball(self.screen, (ball_x, ball_y), spin=self.anim_t * 720)
        else:
            dive_t = 1.0 if self.state in (self.STATE_RESULT, self.STATE_GAMEOVER) else 0.0
            kdir = self.keeper_direction if dive_t else "center"
            draw_keeper(self.screen, keeper_x, keeper_y, dive_t, kdir)
            draw_ball(self.screen, SPOT)
 
        # Scoreboard 
        score_text = self.font_small.render(
            f"Shot {min(self.game.shots_taken + (1 if self.state == self.STATE_AIM else 0), self.game.total_shots)}/{self.game.total_shots}   "
            f"Goals: {self.game.goals_scored}",
            True, WHITE
        )
        self.screen.blit(score_text, (16, 12))
 
        # Message 
        draw_fitted_text(
            self.screen, self.message, (WIDTH // 2, 65),
            max_width=WIDTH - 40, color=GOLD if "WIN" in self.message else WHITE,
            max_size=44, min_size=20
        )
 
        if self.sub_message:
            draw_fitted_text(
                self.screen, self.sub_message, (WIDTH // 2, 105),
                max_width=WIDTH - 40, color=WHITE,
                max_size=22, min_size=14, bold=False
            )
 
        # Buttons 
        if self.state == self.STATE_AIM:
            mx, my = pygame.mouse.get_pos()
            for d, rect in self.buttons.items():
                hovered = rect.collidepoint(mx, my)
                color = BLUE if not hovered else (90, 130, 250)
                pygame.draw.rect(self.screen, color, rect, border_radius=10)
                pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=10)
                label = self.font_small.render(d.upper(), True, WHITE)
                self.screen.blit(label, label.get_rect(center=rect.center))
 
        if self.state == self.STATE_GAMEOVER:
            restart_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 70, 180, 50)
            pygame.draw.rect(self.screen, RED, restart_rect, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, restart_rect, 2, border_radius=10)
            label = self.font_small.render("RESTART (R)", True, WHITE)
            self.screen.blit(label, label.get_rect(center=restart_rect.center))
 
 
def start_game():
    """Entry point used by PK_Main.py."""
    app = PenaltyShootoutGUI()
    app.run()