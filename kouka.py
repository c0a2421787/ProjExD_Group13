import pygame as pg
import os
import sys

# --- 資料の必須要件: 実行ディレクトリの固定 ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数定義 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 32
FPS = 60

# 色定義
COLOR_GRASS = (60, 160, 60)      # 草原
COLOR_ROAD = (180, 180, 180)     # 道（石畳）
COLOR_WATER = (50, 100, 200)     # お堀
COLOR_WALL = (120, 120, 120)     # 城壁
COLOR_ROOF = (200, 50, 50)       # 屋根
COLOR_HOUSE = (150, 100, 50)     # 民家
COLOR_HERO = (50, 50, 200)       # 勇者
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

class Player(pg.sprite.Sprite):
    """
    主人公キャラクタークラス
    """
    def __init__(self, x: int, y: int):
        super().__init__()
        # ドット絵風勇者を生成
        self.image = pg.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(COLOR_HERO)
        # 顔
        pg.draw.rect(self.image, (255, 200, 150), (4, 4, 24, 24))
        # 目
        pg.draw.rect(self.image, COLOR_BLACK, (8, 10, 4, 4))
        pg.draw.rect(self.image, COLOR_BLACK, (20, 10, 4, 4))
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.speed = 4

    def update(self, keys):
        # 移動処理
        dx = 0
        dy = 0
        if keys[pg.K_LEFT]:  dx = -self.speed
        if keys[pg.K_RIGHT]: dx = self.speed
        if keys[pg.K_UP]:    dy = -self.speed
        if keys[pg.K_DOWN]:  dy = self.speed

        self.rect.x += dx
        self.rect.y += dy

        # 画面外にはみ出さない処理
        self.rect.clamp_ip(pg.display.get_surface().get_rect())

class Game:
    """
    ゲーム全体管理クラス
    """
    def __init__(self):
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("工科クエスト - 始まりの城下町")
        self.clock = pg.time.Clock()
        self.running = True

        # マップ（背景）の作成
        self.bg_image = self.create_castle_town_map()

        # プレイヤー配置（画面下の中央＝町の入り口付近）
        self.player = Player(SCREEN_WIDTH // 2 - 16, SCREEN_HEIGHT - 100)
        self.all_sprites = pg.sprite.Group(self.player)

    def create_castle_town_map(self) -> pg.Surface:
        """
        お城と城下町の背景画像を生成して返す関数
        外部ファイルを使わず、描画コマンドでRPG風マップを作る
        """
        surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 1. 全体を草原で塗りつぶし
        surface.fill(COLOR_GRASS)

        # 2. 中央の道（石畳）を描く
        road_width = 120
        center_x = SCREEN_WIDTH // 2
        pg.draw.rect(surface, COLOR_ROAD, (center_x - road_width//2, 200, road_width, SCREEN_HEIGHT - 200))

        # 3. お城エリア（上部）
        # お堀
        pg.draw.rect(surface, COLOR_WATER, (0, 0, SCREEN_WIDTH, 200))
        # 城の土台（地面）
        castle_ground_rect = (center_x - 150, 20, 300, 180)
        pg.draw.rect(surface, COLOR_ROAD, castle_ground_rect)
        # 橋
        pg.draw.rect(surface, (160, 100, 50), (center_x - 40, 180, 80, 40)) # 木の橋

        # --- お城の建物 ---
        # 城壁
        pg.draw.rect(surface, COLOR_WALL, (center_x - 100, 50, 200, 100))
        # 門（黒い部分）
        pg.draw.rect(surface, (30, 30, 30), (center_x - 30, 110, 60, 40))
        # 屋根（3つの塔）
        # 中央の塔
        pg.draw.polygon(surface, COLOR_ROOF, [(center_x - 50, 50), (center_x + 50, 50), (center_x, 10)])
        # 左の塔
        pg.draw.rect(surface, COLOR_WALL, (center_x - 120, 60, 40, 80))
        pg.draw.polygon(surface, COLOR_ROOF, [(center_x - 130, 60), (center_x - 70, 60), (center_x - 100, 30)])
        # 右の塔
        pg.draw.rect(surface, COLOR_WALL, (center_x + 80, 60, 40, 80))
        pg.draw.polygon(surface, COLOR_ROOF, [(center_x + 70, 60), (center_x + 130, 60), (center_x + 100, 30)])

        # 4. 城下町の民家（左右に配置）
        house_positions = [
            (100, 300), (100, 450), # 左側の家
            (600, 300), (600, 450)  # 右側の家
        ]
        
        for hx, hy in house_positions:
            # 家の壁
            pg.draw.rect(surface, COLOR_HOUSE, (hx, hy, 80, 60))
            # 家のドア
            pg.draw.rect(surface, (50, 30, 10), (hx + 30, hy + 30, 20, 30))
            # 家の屋根
            pg.draw.polygon(surface, (200, 100, 100), [(hx - 10, hy), (hx + 90, hy), (hx + 40, hy - 40)])

        return surface

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

    def update(self):
        keys = pg.key.get_pressed()
        self.player.update(keys)

    def draw(self):
        self.screen.blit(self.bg_image, (0, 0))
        self.all_sprites.draw(self.screen)
        pg.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pg.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()