import sys
import stddraw
import math

CANVAS_W = 900
CANVAS_H = 700

WORLD_W = 100.0
WORLD_H = 100.0
GROUND_Y = 8.0

FPS = 60
FRAME_MS = 1000 // FPS

TITLE = "title"
PLAYING = "playing"
GAME_OVER = "game_over"

GAME_OVER_DELAY = 180

BACKGROUND_COLOR = stddraw.BLACK
HUD_COLOR = stddraw.WHITE
PLAYER_COLOR = stddraw.BLUE
MISSILE_COLOR = stddraw.RED
ENEMY_COLOR = stddraw.GREEN
GROUND_COLOR = stddraw.DARK_GRAY


def clamp(value, low, high):
    return max(low, min(high, value))


def rects_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 <= bx2 and ax2 >= bx1 and ay1 <= by2 and ay2 >= by1


class Shooter:
    def __init__(self):
        self.x = WORLD_W / 2
        self.y = GROUND_Y + 3.5

        self.body_half_w = 4.0
        self.body_half_h = 2.0

        self.move_speed = 1.0
        self.move_dir = 0

        self.turret_angle = 90.0
        self.turret_min = 0.0
        self.turret_max = 180.0
        self.turret_rotate_speed = 2.5
        self.turret_rotate_dir = 0

        self.turret_length = 6.0

        self.shot_cooldown_frames = 15
        self.cooldown = 0

    def update(self):
        self.x += self.move_dir * self.move_speed
        self.x = clamp(self.x, self.body_half_w, WORLD_W - self.body_half_w)

        self.turret_angle += self.turret_rotate_dir * self.turret_rotate_speed
        self.turret_angle = clamp(self.turret_angle, self.turret_min, self.turret_max)

        if self.cooldown > 0:
            self.cooldown -= 1

    def can_fire(self):
        return self.cooldown == 0

    def fire(self):
        if not self.can_fire():
            return None

        angle_rad = math.radians(self.turret_angle)
        tip_x = self.x + math.cos(angle_rad) * self.turret_length
        tip_y = self.y + math.sin(angle_rad) * self.turret_length

        missile_speed = 2.4
        vx = math.cos(angle_rad) * missile_speed
        vy = math.sin(angle_rad) * missile_speed

        self.cooldown = self.shot_cooldown_frames
        return Missile(tip_x, tip_y, vx, vy)

    def bounds(self):
        return (
            self.x - self.body_half_w,
            self.y - self.body_half_h,
            self.x + self.body_half_w,
            self.y + self.body_half_h,
        )

    def draw(self):
        stddraw.setPenColor(PLAYER_COLOR)

        body_w = self.body_half_w * 2
        body_h = self.body_half_h * 2

        stddraw.filledRectangle(self.x - self.body_half_w,self.y - self.body_half_h, body_w, body_h)
        stddraw.filledCircle(self.x, self.y + 1.2, 1.4)

        angle_rad = math.radians(self.turret_angle)
        x2 = self.x + math.cos(angle_rad) * self.turret_length
        y2 = self.y + math.sin(angle_rad) * self.turret_length

        stddraw.setPenRadius(0.5)
        stddraw.line(self.x, self.y, x2, y2)
        stddraw.setPenRadius()


class Missile:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.half_w = 0.4
        self.half_h = 1.0
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.x < 0 or self.x > WORLD_W or self.y < 0 or self.y > WORLD_H:
            self.active = False

    def bounds(self):
        return (
            self.x - self.half_w,
            self.y - self.half_h,
            self.x + self.half_w,
            self.y + self.half_h,
        )

    def draw(self):
        stddraw.setPenColor(MISSILE_COLOR)
        stddraw.filledRectangle(self.x - self.half_w, self.y - self.half_h, self.half_w * 2, self.half_h * 2)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.half_w = 2.4
        self.half_h = 1.8
        self.alive = True

    def bounds(self):
        return (
            self.x - self.half_w,
            self.y - self.half_h,
            self.x + self.half_w,
            self.y + self.half_h,
        )

    def draw(self):
        if not self.alive:
            return

        stddraw.setPenColor(ENEMY_COLOR)

        body_w = self.half_w * 2
        body_h = self.half_h * 2

        stddraw.filledRectangle(self.x - self.half_w,self.y - self.half_h, body_w, body_h)

        stddraw.setPenColor(stddraw.BLACK)
        stddraw.filledCircle(self.x - 0.8, self.y + 0.3, 0.35)
        stddraw.filledCircle(self.x + 0.8, self.y + 0.3, 0.35)

        stddraw.setPenColor(ENEMY_COLOR)
        stddraw.setPenRadius(0.003)
        stddraw.line(self.x - 1.2, self.y + 1.8, self.x - 1.8, self.y + 3.0)
        stddraw.line(self.x + 1.2, self.y + 1.8, self.x + 1.8, self.y + 3.0)
        stddraw.setPenRadius()


class EnemyGrid:
    def __init__(self, rows=4, cols=8):
        self.enemies = []
        self.rows = rows
        self.cols = cols

        self.direction = 1
        self.speed = 0.22
        self.drop_amount = 2.8

        start_x = 14.0
        start_y = 82.0
        gap_x = 9.0
        gap_y = 7.0

        for r in range(rows):
            for c in range(cols):
                x = start_x + c * gap_x
                y = start_y - r * gap_y
                self.enemies.append(Enemy(x, y))

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    def all_destroyed(self):
        return len(self.alive_enemies()) == 0

    def update(self):
        alive = self.alive_enemies()
        if not alive:
            return

        hit_edge = False
        for enemy in alive:
            next_x = enemy.x + self.direction * self.speed
            if (next_x + enemy.half_w >= WORLD_W) or (next_x - enemy.half_w <= 0):
                hit_edge = True
                break

        if hit_edge:
            self.direction *= -1
            for enemy in alive:
                enemy.y -= self.drop_amount
        else:
            for enemy in alive:
                enemy.x += self.direction * self.speed

    def reached_ground(self):
        for enemy in self.alive_enemies():
            if enemy.y - enemy.half_h <= GROUND_Y:
                return True
        return False

    def touches_shooter(self, shooter):
        sb = shooter.bounds()
        for enemy in self.alive_enemies():
            if rects_intersect(enemy.bounds(), sb):
                return True
        return False

    def draw(self):
        for enemy in self.enemies:
            enemy.draw()


class Game:
    def __init__(self):
        stddraw.setCanvasSize(CANVAS_W, CANVAS_H)
        stddraw.setXscale(0, WORLD_W)
        stddraw.setYscale(0, WORLD_H)

        self.state = TITLE
        self.score = 0
        self.game_over_timer = 0
        self.winner_text = ""
        self.shooter = None
        self.missiles = []
        self.enemy_grid = None

        self.reset_world()

    def reset_world(self):
        self.score = 0
        self.shooter = Shooter()
        self.missiles = []
        self.enemy_grid = EnemyGrid(rows=4, cols=8)
        self.game_over_timer = 0
        self.winner_text = ""

    def typed_keys(self):
        while stddraw.hasNextKeyTyped():
            key = stddraw.nextKeyTyped()

            if key in ("q", "Q"):
                sys.exit(0)

            if self.state == TITLE:
                if key == " ":
                    self.reset_world()
                    self.state = PLAYING

            elif self.state == PLAYING:
                if key in ("a", "A"):
                    self.shooter.move_dir = -1
                elif key in ("d", "D"):
                    self.shooter.move_dir = 1
                elif key in ("s", "S"):
                    self.shooter.move_dir = 0
                elif key in ("j", "J"):
                    self.shooter.turret_rotate_dir = 1
                elif key in ("l", "L"):
                    self.shooter.turret_rotate_dir = -1
                elif key in ("k", "K"):
                    self.shooter.turret_rotate_dir = 0
                elif key == " ":
                    missile = self.shooter.fire()
                    if missile is not None:
                        self.missiles.append(missile)

            elif self.state == GAME_OVER:
                pass

    def update_playing(self):
        self.shooter.update()
        self.enemy_grid.update()

        for missile in self.missiles:
            missile.update()

        self.missiles = [m for m in self.missiles if m.active]

        for missile in self.missiles:
            if not missile.active:
                continue

            mb = missile.bounds()
            for enemy in self.enemy_grid.alive_enemies():
                if rects_intersect(mb, enemy.bounds()):
                    missile.active = False
                    enemy.alive = False
                    self.score += 10
                    break

        self.missiles = [m for m in self.missiles if m.active]

        if self.enemy_grid.all_destroyed():
            self.state = GAME_OVER
            self.winner_text = "You Win!"
            self.game_over_timer = GAME_OVER_DELAY
            return

        if self.enemy_grid.reached_ground() or self.enemy_grid.touches_shooter(self.shooter):
            self.state = GAME_OVER
            self.winner_text = "Enemies Win!"
            self.game_over_timer = GAME_OVER_DELAY
            return

    def update_game_over(self):
        self.game_over_timer -= 1
        if self.game_over_timer <= 0:
            self.reset_world()
            self.state = TITLE

    def update(self):
        if self.state == PLAYING:
            self.update_playing()
        elif self.state == GAME_OVER:
            self.update_game_over()

    def draw_background(self):
        stddraw.clear(BACKGROUND_COLOR)

        stddraw.setPenColor(GROUND_COLOR)
        stddraw.filledRectangle(0,0, WORLD_W, GROUND_Y)

        stddraw.setPenColor(stddraw.GRAY)
        stars = [
            (8, 95), (15, 88), (28, 92), (37, 97), (50, 91),
            (63, 94), (72, 89), (84, 96), (92, 90), (12, 75),
            (44, 80), (68, 78), (24, 68)
        ]
        for x, y in stars:
            stddraw.point(x, y)

    def draw_hud(self):
        stddraw.setPenColor(HUD_COLOR)
        stddraw.text(10, 97, f"Score: {self.score}")
        stddraw.text(90, 97, "Q to quit")

    def draw_title_screen(self):
        self.draw_background()

        stddraw.setPenColor(stddraw.WHITE)
        stddraw.text(WORLD_W / 2, 78, "Cosmic Conquistadors")
        stddraw.text(WORLD_W / 2, 70, "Welcome")
        stddraw.text(WORLD_W / 2, 58, "Controls")
        stddraw.text(WORLD_W / 2, 52, "A / D = move left / right")
        stddraw.text(WORLD_W / 2, 48, "S = stop moving")
        stddraw.text(WORLD_W / 2, 44, "J / L = rotate turret left / right")
        stddraw.text(WORLD_W / 2, 40, "K = stop turret rotation")
        stddraw.text(WORLD_W / 2, 36, "SPACE = start / shoot")
        stddraw.text(WORLD_W / 2, 32, "Q = quit")
        stddraw.text(WORLD_W / 2, 20, "Press SPACE to begin")

    def draw_playing(self):
        self.draw_background()
        self.draw_hud()
        self.enemy_grid.draw()
        for missile in self.missiles:
            missile.draw()
        self.shooter.draw()

    def draw_game_over(self):
        self.draw_background()
        self.draw_hud()
        self.enemy_grid.draw()
        for missile in self.missiles:
            missile.draw()
        self.shooter.draw()

        stddraw.setPenColor(stddraw.WHITE)
        stddraw.text(WORLD_W / 2, 58, "GAME OVER")
        stddraw.text(WORLD_W / 2, 52, self.winner_text)
        stddraw.text(WORLD_W / 2, 46, f"Final Score: {self.score}")
        stddraw.text(WORLD_W / 2, 38, "Restarting soon...")

    def draw(self):
        if self.state == TITLE:
            self.draw_title_screen()
        elif self.state == PLAYING:
            self.draw_playing()
        elif self.state == GAME_OVER:
            self.draw_game_over()

        stddraw.show(FRAME_MS)


    def run(self):
        while True:
            self.typed_keys()
            self.update()
            self.draw()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
