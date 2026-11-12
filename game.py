import pygame
import math
import random

# ============================================================
# КОНСТАНТЫ ФИЗИКИ (СИ)
# ============================================================
FPS = 60
GRAVITY_MS2 = 9.81

BOUNCE_DAMPING = 0.75
BACKBOARD_ELASTICITY = 0.6
RIM_ELASTICITY = 0.55
FRICTION_AIR = 0.9999
FRICTION_GROUND = 0.9

# --- Геометрия корта (метры) ---
COURT_LENGTH_M = 28.0
HOOP_HEIGHT_M = 3.05
HOOP_FROM_BASELINE_M = 1.575
HOOP_RIM_DIAMETER_M = 0.45
BALL_DIAMETER_M = 0.24
BB_BOTTOM_M = 2.90
BB_TOP_M = 3.95
BB_BACK_FROM_BASELINE_M = 1.20
BB_THICK_M = 0.15
FT_LINE_FROM_BASELINE_M = 5.8
THREE_PT_DIST_M = 6.75
PAINT_DEPTH_M = 5.8

MARGIN_TOP_PX = 40
FLOOR_Y_RATIO = 0.70          # пол на 70% высоты экрана
FLOOR_MIN_BOTTOM_SPACE = 140  # минимум px под нижнюю панель UI

DEFAULT_WIDTH, DEFAULT_HEIGHT = 1200, 620
MIN_WIDTH, MIN_HEIGHT = 700, 400

# --- Игровые дефолты ---
DEFAULT_LAUNCH_HEIGHT_M = 2.5
START_X_M = 20.0
DEFAULT_SPEED = 8.3
DEFAULT_ANGLE = 45.0

SHOT_TIMEOUT_FRAMES = 1800
SIMULATE_MAX_STEPS = 1800

# --- Пиксель-арт зал ---
PA_BASE_W = 320
PA_BASE_H = 180
PA_WALL_CUTOFF = 114        # только стена + свет

# --- Цвета ---
C_BG = (10, 14, 22)
C_FLOOR_BASE = (185, 145, 95)
C_FLOOR_SEAM = (120, 85, 50)
C_PAINT_AREA = (150, 95, 60)
C_PAINT_BORDER = (235, 225, 200)
C_KEY_LINE = (240, 235, 210)
C_HOOP_RIM_NORMAL = (255, 80, 20)
C_HOOP_SCORE = (0, 220, 0)
C_HOOP_TARGET = (255, 210, 60)
C_BALL = (255, 140, 40)
C_TRAIL_PREDICT = (100, 160, 255)
C_TRAIL_WILL_SCORE = (60, 220, 120)
C_TRAIL_ACTUAL = (255, 80, 80)
C_TEXT = (0, 0, 0)
C_BACKBOARD_COLOR = (200, 200, 210)


# ============================================================
# ПИКСЕЛЬ-АРТ СЦЕНА ЗАЛА (интеграция внешнего проекта)
# ============================================================
def _pa_wall(surf):
    pygame.draw.rect(surf, (28, 30, 38), (0, 0, PA_BASE_W, 12))
    for y in range(12, 112):
        t = (y - 12) / 100
        pygame.draw.line(surf, (int(55 + t * 25),
                                int(58 + t * 25),
                                int(72 + t * 25)),
                         (0, y), (PA_BASE_W, y))
    pygame.draw.rect(surf, (150, 40, 40), (0, 78, PA_BASE_W, 4))
    pygame.draw.rect(surf, (45, 42, 48), (0, 108, PA_BASE_W, 5))
    pygame.draw.rect(surf, (30, 28, 33), (0, 112, PA_BASE_W, 2))


def _pa_floor(surf):
    for y in range(114, PA_BASE_H):
        t = (y - 114) / 66
        pygame.draw.line(surf, (int(155 + t * 35),
                                int(110 + t * 25),
                                int(65 + t * 20)),
                         (0, y), (PA_BASE_W, y))
    for y in range(120, PA_BASE_H, 12):
        pygame.draw.line(surf, (135, 95, 58), (0, y), (PA_BASE_W, y))
    pygame.draw.rect(surf, (175, 50, 50), (0, 148, PA_BASE_W, 3))
    pygame.draw.rect(surf, (230, 210, 180), (0, 152, PA_BASE_W, 1))


def _pa_lights(surf):
    for lx in [60, 160, 260]:
        pygame.draw.rect(surf, (60, 60, 70), (lx - 12, 4, 24, 6))
        pygame.draw.rect(surf, (80, 80, 90), (lx - 12, 4, 24, 2))
        pygame.draw.rect(surf, (255, 245, 200), (lx - 10, 7, 20, 2))
        pygame.draw.rect(surf, (255, 255, 230), (lx - 8, 8, 16, 1))


def _pa_lighting(surf, t=0):
    dark = pygame.Surface((PA_BASE_W, PA_BASE_H), pygame.SRCALPHA)
    dark.fill((10, 10, 20, 55))
    surf.blit(dark, (0, 0))
    for i, lx in enumerate([60, 160, 260]):
        flicker = 1.0 + 0.06 * math.sin(t * 0.05 + i * 1.7)
        glow = pygame.Surface((PA_BASE_W, PA_BASE_H))
        glow.fill((0, 0, 0))
        for r in range(70, 0, -2):
            intensity = int(28 * (1 - r / 70) * flicker)
            if intensity < 1:
                continue
            color = (intensity, int(intensity * 0.85), int(intensity * 0.55))
            pygame.draw.circle(glow, color, (lx, 12), r)
        surf.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)


def _pa_door(surf, x, y, w, h):
    pygame.draw.rect(surf, (50, 40, 35), (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(surf, (70, 55, 45), (x, y, w, h))
    pygame.draw.rect(surf, (85, 65, 50), (x + 3, y + 3, w - 6, h // 2 - 4))
    pygame.draw.rect(surf, (85, 65, 50), (x + 3, y + h // 2 + 1, w - 6,
                                          h // 2 - 4))
    pygame.draw.rect(surf, (100, 78, 60), (x + 5, y + 5, w - 10, h // 2 - 8))
    pygame.draw.rect(surf, (100, 78, 60), (x + 5, y + h // 2 + 3, w - 10,
                                           h // 2 - 8))
    pygame.draw.rect(surf, (200, 180, 100), (x + w - 6, y + h // 2 - 2, 3, 4))
    pygame.draw.rect(surf, (240, 220, 140), (x + w - 5, y + h // 2 - 1, 1, 2))

    cx = x + w // 2
    pygame.draw.rect(surf, (60, 15, 15), (cx - 8, y - 12, 16, 6))
    pygame.draw.rect(surf, (255, 60, 60), (cx - 7, y - 11, 14, 4))
    W = (255, 255, 255)
    pygame.draw.rect(surf, W, (cx - 6, y - 10, 1, 3))
    pygame.draw.rect(surf, W, (cx - 6, y - 10, 2, 1))
    pygame.draw.rect(surf, W, (cx - 6, y - 9, 1, 1))
    pygame.draw.rect(surf, W, (cx - 6, y - 8, 2, 1))
    pygame.draw.rect(surf, W, (cx - 3, y - 10, 1, 1))
    pygame.draw.rect(surf, W, (cx - 1, y - 10, 1, 1))
    pygame.draw.rect(surf, W, (cx - 2, y - 9, 1, 1))
    pygame.draw.rect(surf, W, (cx - 3, y - 8, 1, 1))
    pygame.draw.rect(surf, W, (cx - 1, y - 8, 1, 1))
    pygame.draw.rect(surf, W, (cx, y - 10, 1, 3))
    pygame.draw.rect(surf, W, (cx + 2, y - 10, 3, 1))
    pygame.draw.rect(surf, W, (cx + 3, y - 9, 1, 2))


def _pa_bench(surf, x, y, w):
    pygame.draw.rect(surf, (110, 75, 45), (x, y, w, 3))
    pygame.draw.rect(surf, (135, 92, 58), (x, y, w, 1))
    pygame.draw.rect(surf, (80, 52, 32), (x + 2, y + 3, 2, 5))
    pygame.draw.rect(surf, (80, 52, 32), (x + w - 4, y + 3, 2, 5))
    pygame.draw.rect(surf, (125, 82, 48), (x, y + 8, w, 4))
    pygame.draw.rect(surf, (150, 102, 62), (x, y + 8, w, 1))
    pygame.draw.rect(surf, (90, 58, 34), (x, y + 12, w, 1))
    for lx in [x + 3, x + w - 6]:
        pygame.draw.rect(surf, (70, 46, 28), (lx, y + 13, 3, 6))
        pygame.draw.rect(surf, (48, 30, 18), (lx, y + 19, 3, 2))


def _pa_scoreboard(surf, x, y):
    pygame.draw.rect(surf, (20, 20, 30), (x - 1, y - 1, 26, 12))
    pygame.draw.rect(surf, (50, 50, 65), (x, y, 24, 10))
    pygame.draw.rect(surf, (15, 15, 20), (x + 1, y + 1, 22, 8))
    pygame.draw.rect(surf, (255, 60, 60), (x + 3, y + 2, 6, 6))
    pygame.draw.rect(surf, (15, 15, 20), (x + 5, y + 4, 2, 2))
    pygame.draw.rect(surf, (60, 220, 100), (x + 14, y + 2, 6, 6))
    pygame.draw.rect(surf, (15, 15, 20), (x + 16, y + 4, 2, 2))


def _build_pixel_gym(surf):
    surf.fill((0, 0, 0))
    _pa_wall(surf)
    _pa_floor(surf)
    _pa_lights(surf)
    _pa_lighting(surf, 0)


# ============================================================
# ФИЗИКА
# ============================================================
def physics_step(px, py, pvx, pvy, geom):
    pvy += geom.gravity_px
    pvx *= FRICTION_AIR
    pvy *= FRICTION_AIR

    old_x, old_y = px, py
    px += pvx
    py += pvy

    scored_hoop = None
    for i, hoop in enumerate(geom.hoops):
        if old_y <= hoop['y'] < py:
            denom = py - old_y
            if abs(denom) > 1e-9:
                t = (hoop['y'] - old_y) / denom
                x_cross = old_x + t * (px - old_x)
                if abs(x_cross - hoop['x']) < geom.score_tolerance:
                    scored_hoop = i
                    break

    collided = False

    if py + geom.ball_radius > geom.floor_y:
        py = geom.floor_y - geom.ball_radius
        if pvy > 0:
            pvy = -pvy * BOUNCE_DAMPING
        pvx *= FRICTION_GROUND
        if abs(pvy) < 0.5:
            pvy = 0
        collided = True

    if px - geom.ball_radius < 0:
        px = geom.ball_radius
        pvx = abs(pvx) * BOUNCE_DAMPING
        collided = True
    elif px + geom.ball_radius > geom.width:
        px = geom.width - geom.ball_radius
        pvx = -abs(pvx) * BOUNCE_DAMPING
        collided = True

    for bb in geom.backboards:
        bx, by, bw, bh = bb
        cx = max(bx, min(px, bx + bw))
        cy = max(by, min(py, by + bh))
        dx, dy = px - cx, py - cy
        if dx * dx + dy * dy < geom.ball_radius * geom.ball_radius:
            if dx == 0 and dy == 0:
                px = bx - geom.ball_radius
                pvx = -abs(pvx) * BACKBOARD_ELASTICITY
            elif abs(dx) > abs(dy):
                if dx > 0:
                    px = bx + bw + geom.ball_radius
                    pvx = abs(pvx) * BACKBOARD_ELASTICITY
                else:
                    px = bx - geom.ball_radius
                    pvx = -abs(pvx) * BACKBOARD_ELASTICITY
            else:
                if dy > 0:
                    py = by + bh + geom.ball_radius
                    pvy = abs(pvy) * BACKBOARD_ELASTICITY
                else:
                    py = by - geom.ball_radius
                    pvy = -abs(pvy) * BACKBOARD_ELASTICITY
            collided = True

    if scored_hoop is None:
        for hoop in geom.hoops:
            for side in (-1, 1):
                rx = hoop['x'] + side * geom.rim_radius
                ry = hoop['y']
                ddx, ddy = px - rx, py - ry
                dist_sq = ddx * ddx + ddy * ddy
                min_d = geom.ball_radius + 1
                if 1e-6 < dist_sq < min_d * min_d:
                    d = math.sqrt(dist_sq)
                    nnx, nny = ddx / d, ddy / d
                    px = rx + nnx * min_d
                    py = ry + nny * min_d
                    dot = pvx * nnx + pvy * nny
                    if dot < 0:
                        pvx -= 2 * dot * nnx * RIM_ELASTICITY
                        pvy -= 2 * dot * nny * RIM_ELASTICITY
                    collided = True

    return px, py, pvx, pvy, collided, scored_hoop


def simulate_trajectory(start_x, start_y, speed_ms, angle_deg, geom,
                        max_steps=SIMULATE_MAX_STEPS):
    v_px = speed_ms * geom.scale / FPS
    rad = math.radians(angle_deg)
    vx = v_px * math.cos(rad)
    vy = -v_px * math.sin(rad)
    px, py = float(start_x), float(start_y)

    points = [(int(px), int(py))]
    will_score = False

    for _ in range(max_steps):
        px, py, vx, vy, _, scored_hoop = physics_step(px, py, vx, vy, geom)
        points.append((int(px), int(py)))
        if scored_hoop is not None:
            will_score = True
            break
        if (abs(vx) < 0.08 and abs(vy) < 0.3
                and py >= geom.floor_y - geom.ball_radius - 1):
            break

    return points, will_score


# ============================================================
# ГЕОМЕТРИЯ
# ============================================================
class Geometry:
    def __init__(self, width, height):
        self.recalc(width, height)

    def recalc(self, width, height):
        self.width = width
        self.height = height
        self.scale = width / COURT_LENGTH_M

        self.floor_y = min(int(height * FLOOR_Y_RATIO),
                           height - FLOOR_MIN_BOTTOM_SPACE)
        self.hoop_y = self.floor_y - int(HOOP_HEIGHT_M * self.scale)

        self.rim_radius = max(3, int(HOOP_RIM_DIAMETER_M / 2 * self.scale))
        self.ball_radius = max(2, int(BALL_DIAMETER_M / 2 * self.scale))
        self.score_tolerance = max(1, self.rim_radius - self.ball_radius)

        self.gravity_px = GRAVITY_MS2 * self.scale / (FPS * FPS)

        left_rim_x = int(HOOP_FROM_BASELINE_M * self.scale)
        right_rim_x = int((COURT_LENGTH_M - HOOP_FROM_BASELINE_M) * self.scale)

        self.hoops = [
            {'x': left_rim_x, 'y': self.hoop_y, 'side': 'left'},
            {'x': right_rim_x, 'y': self.hoop_y, 'side': 'right'},
        ]

        bb_bottom = self.floor_y - int(BB_BOTTOM_M * self.scale)
        bb_top = self.floor_y - int(BB_TOP_M * self.scale)
        bb_h = max(1, bb_bottom - bb_top)
        bb_w = max(3, int(BB_THICK_M * self.scale))

        bb_left_x = int(BB_BACK_FROM_BASELINE_M * self.scale)
        bb_right_x = int((COURT_LENGTH_M - BB_BACK_FROM_BASELINE_M
                          - BB_THICK_M) * self.scale)

        self.backboards = [
            [bb_left_x, bb_top, bb_w, bb_h],
            [bb_right_x, bb_top, bb_w, bb_h],
        ]


# ============================================================
# МЯЧ
# ============================================================
class Ball:
    def __init__(self, geom, x_m=START_X_M):
        self.geom = geom
        self.start_x_m = x_m
        self.reset()

    def reset(self):
        self.x = self.start_x_m * self.geom.scale
        self.y = self.geom.floor_y - DEFAULT_LAUNCH_HEIGHT_M * self.geom.scale
        self.vx = self.vy = 0.0
        self.is_frozen = True
        self.trail = []
        self.settled_frames = 0
        self.launch_origin_x = self.x

    def unfreeze_and_launch(self, speed_ms, angle_deg):
        v_px = speed_ms * self.geom.scale / FPS
        rad = math.radians(angle_deg)
        self.vx = v_px * math.cos(rad)
        self.vy = -v_px * math.sin(rad)
        self.is_frozen = False
        self.trail = [(int(self.x), int(self.y))]
        self.settled_frames = 0
        self.launch_origin_x = self.x

    def freeze_at_position(self, mx, my):
        self.x = float(mx)
        self.y = float(my)
        self.vx = self.vy = 0.0
        self.is_frozen = True
        self.trail = []
        self.settled_frames = 0

    def update_physics(self):
        if self.is_frozen:
            return None
        self.x, self.y, self.vx, self.vy, _, scored_hoop = physics_step(
            self.x, self.y, self.vx, self.vy, self.geom)
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 500:
            self.trail.pop(0)

        speed_sq = self.vx * self.vx + self.vy * self.vy
        on_floor = self.y >= self.geom.floor_y - self.geom.ball_radius - 2
        if speed_sq < 0.04 and on_floor:
            self.settled_frames += 1
            if self.settled_frames > 20:
                self.vx = self.vy = 0.0
                self.is_frozen = True
        else:
            self.settled_frames = 0
        return scored_hoop

    def draw(self, screen):
        height = self.geom.floor_y - self.y
        if height > 0:
            alpha = max(30, int(150 - height / 4))
            sw = max(6, self.geom.ball_radius * 2 - int(height / 30))
            sh = max(3, sw // 2)
            surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (0, 0, 0, alpha), surf.get_rect())
            screen.blit(surf, (self.x - sw // 2, self.geom.floor_y - sh // 2))

        if len(self.trail) > 1:
            pygame.draw.lines(screen, C_TRAIL_ACTUAL, False, self.trail, 2)

        pygame.draw.circle(screen, C_BALL,
                           (int(self.x), int(self.y)), self.geom.ball_radius)
        pygame.draw.circle(screen, (200, 100, 0),
                           (int(self.x), int(self.y)), self.geom.ball_radius, 1)


# ============================================================
# ПОЛЕ ВВОДА
# ============================================================
class InputBox:
    def __init__(self, x, y, w, h, text='', label=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (100, 100, 100)
        self.text = str(text)
        self.label = label
        self.active = False
        self.font = pygame.font.SysFont('Arial', 16)
        self.surface = self.font.render(self.text, True, C_TEXT)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isdigit() or event.unicode == '.':
                self.text += event.unicode
            self.update_surface()

    def update_surface(self):
        self.surface = self.font.render(self.text, True, C_TEXT)

    def get_value(self, default=0.0):
        try:
            return float(self.text)
        except ValueError:
            return default

    def set_value(self, val):
        self.text = f"{val:.1f}" if isinstance(val, float) else str(int(val))
        self.update_surface()

    def draw(self, screen):
        border = (0, 120, 255) if self.active else self.color
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, border, self.rect, 2)
        screen.blit(self.surface, (self.rect.x + 5, self.rect.y + 5))
        if self.label:
            lbl = self.font.render(self.label, True, (80, 80, 80))
            screen.blit(lbl, (self.rect.x, self.rect.y - 18))


# ============================================================
# ИГРОВАЯ ЛОГИКА
# ============================================================
class GameLogic:
    def __init__(self, width, height):
        self.geom = Geometry(width, height)
        self.ball = Ball(self.geom, START_X_M)

        self.input_speed = InputBox(20, 70, 110, 26,
                                    text=f"{DEFAULT_SPEED}",
                                    label="Скорость (м/с)")
        self.input_angle = InputBox(20, 125, 110, 26,
                                    text=f"{int(DEFAULT_ANGLE)}",
                                    label="Угол (0-180°)")

        self.dragging = False
        self.score_status = None
        self.scored_this_shot = False
        self.shot_in_progress = False
        self.shot_frames = 0
        self.total_score = 0
        self.attempts = 0

        self.shot_distance_m = 0.0
        self.trajectory_length_m = 0.0
        self.max_height_m = 0.0
        self.launch_height_m = DEFAULT_LAUNCH_HEIGHT_M
        self.shot_zone_name = ""
        self.target_hoop_idx = 1

        self.teleport_countdown = 0
        self.scored_hoop_idx = None

        self.pred_points = []
        self.pred_will_score = False

        self._build_backgrounds()

    # ---------- Фон ----------
    def _build_backgrounds(self):
        w, h = self.geom.width, self.geom.height
        fy = self.geom.floor_y

        base = pygame.Surface((PA_BASE_W, PA_BASE_H))
        _build_pixel_gym(base)
        wall_portion = base.subsurface((0, 0, PA_BASE_W, PA_WALL_CUTOFF))
        self.bg_crowd = pygame.transform.scale(wall_portion, (w, fy))

        floor_h = h - fy
        self.bg_floor = pygame.Surface((w, floor_h))

        s = self.geom.scale
        ft_left_x = int(FT_LINE_FROM_BASELINE_M * s)
        ft_right_x = int((COURT_LENGTH_M - FT_LINE_FROM_BASELINE_M) * s)

        wood = (198, 156, 108)
        plank_h = max(10, int(22 * w / 1200))
        shades = [(0, 0, 0), (10, 7, 4), (-10, -7, -4),
                  (5, 4, 2), (12, 9, 5)]
        seam = (140, 100, 62)
        gap = (120, 84, 50)

        y, row = 0, 0
        while y < floor_h:
            m = shades[row % len(shades)]
            color = tuple(max(0, min(255, c + d))
                          for c, d in zip(wood, m))
            ph = min(plank_h, floor_h - y)
            pygame.draw.rect(self.bg_floor, color, (0, y, w, ph - 1))

            plank_w = max(60, int(90 * w / 1200))
            offset = (row % 2) * (plank_w // 2)
            x = offset
            while x < w:
                pygame.draw.line(self.bg_floor, seam,
                                 (x, y), (x, y + ph - 2), 1)
                x += plank_w

            pygame.draw.line(self.bg_floor, gap,
                             (0, y + ph - 1), (w, y + ph - 1), 1)
            y += plank_h
            row += 1

        paint = pygame.Surface((w, floor_h), pygame.SRCALPHA)
        paint_key = (172, 74, 54, 150)
        pygame.draw.rect(paint, paint_key, (0, 0, ft_left_x, floor_h))
        pygame.draw.rect(paint, paint_key,
                         (ft_right_x, 0, w - ft_right_x, floor_h))
        self.bg_floor.blit(paint, (0, 0))

        fade = pygame.Surface((w, floor_h), pygame.SRCALPHA)
        for yy in range(floor_h):
            a = int(55 * yy / max(1, floor_h))
            pygame.draw.line(fade, (0, 0, 0, a), (0, yy), (w, yy))
        self.bg_floor.blit(fade, (0, 0))

    # ---------- Утилиты ----------
    def _pick_hoop_by_direction(self, vx_dir, from_x):
        hoops = self.geom.hoops
        if vx_dir > 0:
            cand = [(i, h['x']) for i, h in enumerate(hoops)
                    if h['x'] > from_x]
            if cand:
                return min(cand, key=lambda c: c[1])[0]
        elif vx_dir < 0:
            cand = [(i, h['x']) for i, h in enumerate(hoops)
                    if h['x'] < from_x]
            if cand:
                return max(cand, key=lambda c: c[1])[0]
        return min(range(len(hoops)),
                   key=lambda i: abs(hoops[i]['x'] - from_x))

    def get_current_target_hoop_idx(self):
        angle = max(0.0, min(180.0,
                             self.input_angle.get_value(DEFAULT_ANGLE)))
        vx_dir = math.cos(math.radians(angle))
        if abs(vx_dir) < 0.05:
            return min(range(len(self.geom.hoops)),
                       key=lambda i: abs(self.geom.hoops[i]['x']
                                         - self.ball.x))
        return self._pick_hoop_by_direction(vx_dir, self.ball.x)

    def determine_shot_zone_m(self, dist_m):
        if dist_m <= 1.8:
            return "Под кольцом"
        if dist_m <= 4.6 + 1.0:
            return "Штрафная зона"
        if dist_m <= THREE_PT_DIST_M:
            return "Средняя дистанция"
        return "Трехочковая зона"

    def points_for_zone(self):
        return 3 if "Трехочковая" in self.shot_zone_name else 2

    def _reset_shot_state(self):
        self.score_status = None
        self.scored_this_shot = False
        self.shot_in_progress = False
        self.shot_distance_m = 0.0
        self.trajectory_length_m = 0.0
        self.max_height_m = 0.0
        self.launch_height_m = 0.0
        self.shot_frames = 0
        self.teleport_countdown = 0
        self.scored_hoop_idx = None

    def _teleport_to_free_throw(self, hoop_idx):
        if hoop_idx == 0:
            ft_x_m = FT_LINE_FROM_BASELINE_M
        else:
            ft_x_m = COURT_LENGTH_M - FT_LINE_FROM_BASELINE_M
        self.ball.x = ft_x_m * self.geom.scale
        self.ball.y = (self.geom.floor_y
                       - DEFAULT_LAUNCH_HEIGHT_M * self.geom.scale)
        self.ball.vx = 0.0
        self.ball.vy = 0.0
        self.ball.is_frozen = True
        self.ball.trail = []
        self.ball.settled_frames = 0
        self.ball.launch_origin_x = self.ball.x

    # ---------- События ----------
    def handle_events(self, events):
        for event in events:
            self.input_speed.handle_event(event)
            self.input_angle.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if (self.ball.is_frozen and
                        math.hypot(mx - self.ball.x, my - self.ball.y)
                        < self.ball.geom.ball_radius * 4):
                    self.dragging = True
                    self.ball.freeze_at_position(mx, my)
                    self._reset_shot_state()

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                mx, my = event.pos
                r = self.geom.ball_radius
                min_y = (self.geom.floor_y
                         - DEFAULT_LAUNCH_HEIGHT_M * self.geom.scale)
                max_y = self.geom.floor_y - r
                nx = max(r, min(self.geom.width - r, mx))
                ny = max(min_y, min(max_y, my))
                self.ball.freeze_at_position(nx, ny)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.ball.is_frozen:
                    speed = max(1.0, min(40.0,
                        self.input_speed.get_value(DEFAULT_SPEED)))
                    angle = max(0.0, min(180.0,
                        self.input_angle.get_value(DEFAULT_ANGLE)))
                    self.input_speed.set_value(speed)
                    self.input_angle.set_value(angle)

                    vx_dir = math.cos(math.radians(angle))
                    if abs(vx_dir) < 0.05:
                        vx_dir = 0
                    self.target_hoop_idx = self._pick_hoop_by_direction(
                        vx_dir, self.ball.x)
                    hoop = self.geom.hoops[self.target_hoop_idx]
                    self.shot_distance_m = abs(
                        hoop['x'] - self.ball.x) / self.geom.scale
                    self.shot_zone_name = self.determine_shot_zone_m(
                        self.shot_distance_m)
                    self.launch_height_m = (self.geom.floor_y - self.ball.y) \
                        / self.geom.scale

                    self.ball.unfreeze_and_launch(speed, angle)
                    self._reset_shot_state()
                    self.shot_distance_m = abs(
                        hoop['x'] - self.ball.x) / self.geom.scale
                    self.shot_zone_name = self.determine_shot_zone_m(
                        self.shot_distance_m)
                    self.launch_height_m = (self.geom.floor_y - self.ball.y) \
                        / self.geom.scale
                    self.shot_in_progress = True
                    self.shot_frames = 0
                    self.attempts += 1

                elif event.key == pygame.K_r:
                    self.ball.reset()
                    self.ball.geom = self.geom
                    self._reset_shot_state()

                elif not self.input_speed.active and not self.input_angle.active:
                    if event.key == pygame.K_UP:
                        self.input_speed.set_value(min(
                            self.input_speed.get_value(DEFAULT_SPEED) + 0.5,
                            40))
                    elif event.key == pygame.K_DOWN:
                        self.input_speed.set_value(max(
                            self.input_speed.get_value(DEFAULT_SPEED) - 0.5,
                            1))
                    elif event.key == pygame.K_RIGHT:
                        self.input_angle.set_value(min(
                            self.input_angle.get_value(DEFAULT_ANGLE) + 5,
                            180))
                    elif event.key == pygame.K_LEFT:
                        self.input_angle.set_value(max(
                            self.input_angle.get_value(DEFAULT_ANGLE) - 5,
                            0))

    # ---------- Ресайз ----------
    def on_resize(self, new_w, new_h):
        old_scale = self.geom.scale
        old_floor = self.geom.floor_y
        old_x, old_y = self.ball.x, self.ball.y
        old_vx, old_vy = self.ball.vx, self.ball.vy
        old_trail = list(self.ball.trail)
        old_launch = self.ball.launch_origin_x

        self.geom.recalc(new_w, new_h)
        self._build_backgrounds()

        if old_scale > 0:
            k = self.geom.scale / old_scale
            self.ball.x = old_x * k
            self.ball.y = self.geom.floor_y - (old_floor - old_y) * k
            self.ball.vx = old_vx * k
            self.ball.vy = old_vy * k
            self.ball.launch_origin_x = old_launch * k
            self.ball.trail = [
                (int(px * k), int(self.geom.floor_y - (old_floor - py) * k))
                for px, py in old_trail
            ]

        self.ball.geom = self.geom

    # ---------- Обновление ----------
    def update(self):
        was_frozen = self.ball.is_frozen
        scored_hoop = self.ball.update_physics()

        if not was_frozen:
            self.shot_frames += 1

            if scored_hoop is not None and not self.scored_this_shot:
                self.scored_this_shot = True
                self.score_status = 'SCORE'
                self.total_score += self.points_for_zone()
                self.scored_hoop_idx = scored_hoop
                self.teleport_countdown = 45

            if len(self.ball.trail) >= 2:
                total_px = 0.0
                for i in range(1, len(self.ball.trail)):
                    dx = self.ball.trail[i][0] - self.ball.trail[i - 1][0]
                    dy = self.ball.trail[i][1] - self.ball.trail[i - 1][1]
                    total_px += math.hypot(dx, dy)
                self.trajectory_length_m = total_px / self.geom.scale

                min_y = min(pt[1] for pt in self.ball.trail)
                self.max_height_m = (self.geom.floor_y - min_y) / self.geom.scale

            if self.shot_frames > SHOT_TIMEOUT_FRAMES:
                self.ball.vx = self.ball.vy = 0.0
                self.ball.is_frozen = True

            if self.ball.is_frozen:
                self.shot_in_progress = False
                if not self.scored_this_shot:
                    self.score_status = 'MISS'

        if self.teleport_countdown > 0:
            self.teleport_countdown -= 1
            if self.teleport_countdown == 0 and self.scored_hoop_idx is not None:
                self._teleport_to_free_throw(self.scored_hoop_idx)
                self.scored_hoop_idx = None

        self.pred_points = []
        self.pred_will_score = False
        if self.ball.is_frozen:
            speed = max(1.0, min(40.0,
                self.input_speed.get_value(DEFAULT_SPEED)))
            angle = max(0.0, min(180.0,
                self.input_angle.get_value(DEFAULT_ANGLE)))
            self.pred_points, self.pred_will_score = simulate_trajectory(
                self.ball.x, self.ball.y, speed, angle, self.geom)

    # ---------- Отрисовка ----------
    def draw_coordinates(self, screen):
        font = pygame.font.SysFont('Arial', 10)
        pygame.draw.line(screen, (180, 190, 210),
                         (0, MARGIN_TOP_PX),
                         (self.geom.width, MARGIN_TOP_PX), 1)
        for i in range(0, int(COURT_LENGTH_M) + 1, 2):
            px = i * self.geom.scale
            if px > self.geom.width:
                break
            pygame.draw.line(screen, (100, 110, 130),
                             (px, MARGIN_TOP_PX - 5),
                             (px, MARGIN_TOP_PX + 5), 1)
            txt = font.render(f"{i}m", True, (180, 190, 210))
            screen.blit(txt, (px - 10, MARGIN_TOP_PX - 22))

    def draw_background(self, screen):
        screen.blit(self.bg_crowd, (0, 0))
        screen.blit(self.bg_floor, (0, self.geom.floor_y))

    def draw_court_lines(self, screen):
        s = self.geom.scale
        fy = self.geom.floor_y
        w = self.geom.width

        paint_w = int(PAINT_DEPTH_M * s)
        pygame.draw.rect(screen, C_PAINT_AREA, (0, fy, paint_w, 14))
        pygame.draw.rect(screen, C_PAINT_AREA, (w - paint_w, fy, paint_w, 14))
        pygame.draw.line(screen, C_PAINT_BORDER, (paint_w, fy),
                         (paint_w, fy + 14), 2)
        pygame.draw.line(screen, C_PAINT_BORDER, (w - paint_w, fy),
                         (w - paint_w, fy + 14), 2)

        pygame.draw.line(screen, C_KEY_LINE, (1, fy), (1, fy + 18), 3)
        pygame.draw.line(screen, C_KEY_LINE, (w - 2, fy),
                         (w - 2, fy + 18), 3)

        ft_left_x = int(FT_LINE_FROM_BASELINE_M * s)
        ft_right_x = int((COURT_LENGTH_M - FT_LINE_FROM_BASELINE_M) * s)
        for x in (ft_left_x, ft_right_x):
            pygame.draw.line(screen, C_KEY_LINE, (x, fy), (x, fy + 16), 3)

        for hoop in self.geom.hoops:
            if hoop['side'] == 'left':
                tx = hoop['x'] + int(THREE_PT_DIST_M * s)
            else:
                tx = hoop['x'] - int(THREE_PT_DIST_M * s)
            if 0 < tx < w:
                pygame.draw.line(screen, C_KEY_LINE,
                                 (tx, fy), (tx, fy + 16), 3)

        cx = int(COURT_LENGTH_M / 2 * s)
        pygame.draw.line(screen, C_KEY_LINE, (cx, fy), (cx, fy + 14), 2)

        font = pygame.font.SysFont('Arial', 10, bold=True)
        labels = [(ft_left_x, "Штрафная"), (ft_right_x, "Штрафная")]
        for hoop in self.geom.hoops:
            labels.append((hoop['x'], "Кольцо"))
            if hoop['side'] == 'left':
                labels.append((hoop['x'] + int(THREE_PT_DIST_M * s),
                               "3-очковая"))
            else:
                labels.append((hoop['x'] - int(THREE_PT_DIST_M * s),
                               "3-очковая"))
        for x, name in labels:
            if 40 < x < w - 40:
                txt = font.render(name, True, (240, 240, 240))
                screen.blit(txt, (x - txt.get_width() // 2, fy + 20))

    def draw_hoops(self, screen):
        target_idx = (self.get_current_target_hoop_idx()
                      if self.ball.is_frozen else self.target_hoop_idx)
        scoring_idx = (self.scored_hoop_idx
                       if self.score_status == 'SCORE' else -1)

        for i, (hoop, bb) in enumerate(zip(self.geom.hoops,
                                           self.geom.backboards)):
            bx, by, bw, bh = bb
            pygame.draw.rect(screen, C_BACKBOARD_COLOR, (bx, by, bw, bh))
            pygame.draw.rect(screen, (255, 255, 255), (bx, by, bw, bh), 1)

            if i == scoring_idx:
                rim_color = C_HOOP_SCORE
            elif i == target_idx:
                rim_color = C_HOOP_TARGET
            else:
                rim_color = C_HOOP_RIM_NORMAL

            r = self.geom.rim_radius
            pygame.draw.line(screen, rim_color,
                             (hoop['x'] - r, hoop['y']),
                             (hoop['x'] + r, hoop['y']), 3)
            step = max(2, r // 4)
            for j in range(-r, r + 1, step):
                pygame.draw.line(screen, (230, 230, 230),
                                 (hoop['x'] + j, hoop['y']),
                                 (hoop['x'] + j, hoop['y'] + r * 2), 1)

    def draw_ball_height_indicator(self, screen, font_small):
        if not self.ball.is_frozen:
            return
        h_px = self.geom.floor_y - self.ball.y
        if h_px < 12:
            return

        step = 5
        for i in range(0, int(h_px) - 4, step * 2):
            y1 = int(self.ball.y + i)
            y2 = min(int(self.ball.y + i + step), self.geom.floor_y)
            pygame.draw.line(screen, (200, 200, 220),
                             (int(self.ball.x), y1),
                             (int(self.ball.x), y2), 1)

        h_m = h_px / self.geom.scale
        text = f"{h_m:.1f} м"
        surf = font_small.render(text, True, (255, 255, 255))
        bg = pygame.Surface((surf.get_width() + 8,
                             surf.get_height() + 4), pygame.SRCALPHA)
        bg.fill((40, 40, 40, 210))
        bx = int(self.ball.x + 14)
        by = int(self.ball.y - 10)
        screen.blit(bg, (bx, by))
        screen.blit(surf, (bx + 4, by + 2))

    def draw_ui(self, screen, font_med, font_small):
        panel = pygame.Surface((180, 180), pygame.SRCALPHA)
        panel.fill((30, 35, 50, 235))
        screen.blit(panel, (10, 10))
        pygame.draw.rect(screen, (90, 100, 130), (10, 10, 180, 180), 1)
        screen.blit(font_med.render("ПАРАМЕТРЫ", True, (220, 230, 255)),
                    (20, 15))
        self.input_speed.draw(screen)
        self.input_angle.draw(screen)
        screen.blit(font_small.render("[Space] Бросок  [R] Сброс",
                                      True, (180, 190, 210)), (20, 160))

        sb_w, sb_h = 210, 80
        sb_x = self.geom.width - sb_w - 10
        sb = pygame.Surface((sb_w, sb_h), pygame.SRCALPHA)
        sb.fill((30, 35, 50, 235))
        screen.blit(sb, (sb_x, 10))
        pygame.draw.rect(screen, (90, 100, 130),
                         (sb_x, 10, sb_w, sb_h), 1)
        screen.blit(font_med.render(f"Счёт: {self.total_score}",
                                    True, (255, 240, 150)),
                    (sb_x + 12, 16))
        screen.blit(font_small.render(f"Броски: {self.attempts}",
                                      True, (200, 210, 230)),
                    (sb_x + 12, 46))

        if self.score_status or self.shot_in_progress:
            if self.score_status == 'SCORE':
                header = f"ПОПАДАНИЕ! +{self.points_for_zone()}"
                bg = (0, 130, 40)
            elif self.score_status == 'MISS':
                header = "ПРОМАХ"
                bg = (130, 0, 0)
            else:
                header = "ПОЛЕТ..."
                bg = (35, 40, 55)

            rect = pygame.Rect(self.geom.width // 2 - 240,
                               self.geom.height - 130, 480, 120)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), rect, 1,
                             border_radius=10)

            s = font_med.render(header, True, (255, 255, 255))
            screen.blit(s, (rect.centerx - s.get_width() // 2, rect.y + 6))

            lines = [
                f"Зона броска: {self.shot_zone_name}",
                f"Дистанция броска: {self.shot_distance_m:.1f} м",
                f"Длина траектории: {self.trajectory_length_m:.1f} м",
                f"Высота запуска: {self.launch_height_m:.1f} м",
            ]
            for i, line in enumerate(lines):
                surf = font_small.render(line, True, (235, 235, 235))
                screen.blit(surf, (rect.x + 12, rect.y + 32 + i * 20))

    def draw(self, screen, font_med, font_small):
        screen.fill(C_BG)
        self.draw_background(screen)
        self.draw_coordinates(screen)
        self.draw_court_lines(screen)
        self.draw_hoops(screen)

        if self.ball.is_frozen and len(self.pred_points) > 1:
            color = (C_TRAIL_WILL_SCORE if self.pred_will_score
                     else C_TRAIL_PREDICT)
            for i in range(0, len(self.pred_points) - 1, 2):
                pygame.draw.line(screen, color,
                                 self.pred_points[i],
                                 self.pred_points[i + 1], 2)

        self.ball.draw(screen)
        self.draw_ball_height_indicator(screen, font_small)
        self.draw_ui(screen, font_med, font_small)


# ============================================================
# MAIN
# ============================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT),
                                     pygame.RESIZABLE)
    pygame.display.set_caption("Basketball Sim V11 — Pixel Gym")
    clock = pygame.time.Clock()

    game = GameLogic(DEFAULT_WIDTH, DEFAULT_HEIGHT)
    font_med = pygame.font.SysFont('Arial', 18, bold=True)
    font_small = pygame.font.SysFont('Arial', 13)

    running = True
    while running:
        clock.tick(FPS)
        events = pygame.event.get()

        resize = None
        game_events = []
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.VIDEORESIZE:
                resize = e
            else:
                game_events.append(e)

        if resize:
            w = max(MIN_WIDTH, resize.w)
            h = max(MIN_HEIGHT, resize.h)
            screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            game.on_resize(w, h)

        game.handle_events(game_events)
        game.update()
        game.draw(screen, font_med, font_small)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
