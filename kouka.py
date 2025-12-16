import pygame
import sys
import random
import os

# --- 資料の必須要件: 実行ディレクトリをファイルのある場所に固定 ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)       # こうかとん
BLUE = (0, 0, 255)      # 雑魚敵
YELLOW = (255, 215, 0)  # ボス
GREEN = (34, 139, 34)   # 草原
GRAY = (169, 169, 169)  # キャンパス床

# 状態定数
STATE_MAP = "MAP"
STATE_BATTLE = "BATTLE"
STATE_ENDING = "ENDING"

# マップID
MAP_VILLAGE = 0
MAP_FIELD = 1
MAP_CAMPUS = 2

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RPG 工科クエスト")
        self.clock = pygame.time.Clock()
        
        try:
            self.font = pygame.font.SysFont("meiryo", 32)
        except:
            self.font = pygame.font.Font(None, 32)

        # --- 画像の読み込み ---
        try:
            # ★ここを修正: アップロードされた画像ファイル名に変更しました
            # figフォルダの中に village-L1.png を入れてください
            self.bg_village_original = pygame.image.load("fig/2.png")
            self.bg_village = pygame.transform.scale(self.bg_village_original, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            print("エラー: 画像が見つかりません。figフォルダに 2.png を入れてください。")
            self.bg_village = None

        #  スポーン地点を真ん中の茶色い道の上（400, 300）に設定
        self.player_pos = [400, 200]
        self.player_size = 40
        self.speed = 5
        
        # ゲーム進行管理
        self.state = STATE_MAP
        self.current_map = MAP_VILLAGE
        self.is_boss_battle = False
        
        # 戦闘用変数
        self.enemy_hp = 0
        self.battle_message = ""
        self.battle_sub_message = ""

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if self.state == STATE_BATTLE:
                    if event.key == pygame.K_SPACE:
                        damage = random.randint(30, 60)
                        self.enemy_hp -= damage
                        self.battle_message = f"こうかとんの攻撃！ {damage} のダメージ！"
                        if self.enemy_hp <= 0:
                            self.end_battle()
                
                elif self.state == STATE_ENDING:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def update(self):
        if self.state == STATE_MAP:
            keys = pygame.key.get_pressed()
            moved = False
            
            # 移動予定の座標を計算
            new_x = self.player_pos[0]
            new_y = self.player_pos[1]
            
            if keys[pygame.K_LEFT]:  new_x -= self.speed
            if keys[pygame.K_RIGHT]: new_x += self.speed
            if keys[pygame.K_UP]:    new_y -= self.speed
            if keys[pygame.K_DOWN]:  new_y += self.speed

            # --- ここで「歩けるかどうか」をチェック ---
            if self.is_walkable(new_x, new_y):
                # 歩ける場合のみ座標を更新
                if new_x != self.player_pos[0] or new_y != self.player_pos[1]:
                    self.player_pos[0] = new_x
                    self.player_pos[1] = new_y
                    moved = True
            
            # マップ切り替え判定
            self.check_map_transition()

            # エンカウント判定
            if moved and self.current_map == MAP_FIELD:
                self.check_random_encounter()

            # ボス戦判定
            if self.current_map == MAP_CAMPUS and self.player_pos[0] > 700:
                self.start_battle(is_boss=True)

    def is_walkable(self, x, y):
        """
        指定された座標が「茶色い道」かどうかを判定する関数
        """
        # 村以外のマップ（画像がないマップ）は自由に歩ける
        if self.current_map != MAP_VILLAGE or self.bg_village is None:
            return True

        # プレイヤーの「足元」の中心座標を取得
        check_x = int(x + self.player_size / 2)
        check_y = int(y + self.player_size)

        # 画面外チェック
        if check_x < 0 or check_x >= SCREEN_WIDTH or check_y < 0 or check_y >= SCREEN_HEIGHT:
            return True

        try:
            # その座標のピクセルの色を取得
            pixel = self.bg_village.get_at((check_x, check_y))
            r, g, b = pixel[0], pixel[1], pixel[2]

            # --- ★ここを修正: 茶色い道だけ歩ける判定ロジック ---
            
            # 道の色（ベージュ・薄茶）の特徴:
            # 1. 基本的に明るい色である (R+G+Bがある程度大きい)
            # 2. 緑(G)より赤(R)の方が強い、または同じくらい (G > R + 10 とかなら草原)
            # 3. 青(B)が一番弱い（黄色～茶色系の特徴）

            # 判定1: 草原排除 (緑成分が赤より明らかに強い場合は草原)
            if g > r + 15:
                return False

            # 判定2: 暗い色排除 (屋根、木、影などはRGB合計値が低い)
            # 茶色の道は明るいので合計400以上はあるはず
            if r + g + b < 350:
                return False

            # 判定3: 青っぽい色排除 (水辺など)
            if b > r:
                return False

            # 上記のNG条件に引っかからなければ「道」とみなす
            return True

        except IndexError:
            return False

    def check_map_transition(self):
        """画面端に到達したらマップを切り替える判定"""
        if self.player_pos[0] >= SCREEN_WIDTH - self.player_size:
            if self.current_map < MAP_CAMPUS:
                self.current_map += 1
                self.player_pos[0] = 10
            else:
                self.player_pos[0] = SCREEN_WIDTH - self.player_size

        elif self.player_pos[0] <= 0:
            if self.current_map > MAP_VILLAGE:
                self.current_map -= 1
                self.player_pos[0] = SCREEN_WIDTH - 10 - self.player_size
            else:
                self.player_pos[0] = 0
        
        if self.player_pos[1] < 0:
            self.player_pos[1] = 0
        if self.player_pos[1] > SCREEN_HEIGHT - self.player_size:
            self.player_pos[1] = SCREEN_HEIGHT - self.player_size

    def check_random_encounter(self):
        if random.randint(0, 100) < 1:
            self.start_battle(is_boss=False)

    def start_battle(self, is_boss):
        self.state = STATE_BATTLE
        self.is_boss_battle = is_boss
        self.battle_sub_message = "スペースキーで攻撃！"
        
        if is_boss:
            self.enemy_hp = 500
            self.battle_message = "「単位を奪う悪の組織」が現れた！(BOSS)"
        else:
            self.enemy_hp = 100
            self.battle_message = "「未提出の課題」が現れた！"

    def end_battle(self):
        if self.is_boss_battle:
            self.state = STATE_ENDING
        else:
            self.state = STATE_MAP
            self.battle_message = ""
            pygame.time.wait(500)

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == STATE_MAP:
            if self.current_map == MAP_VILLAGE:
                if self.bg_village:
                    self.screen.blit(self.bg_village, (0, 0))
                else:
                    self.screen.fill((100, 200, 100))
                text = self.font.render("最初の村 (茶色の道を進もう)", True, BLACK)
                self.screen.blit(text, (20, 20))

            elif self.current_map == MAP_FIELD:
                self.screen.fill(GREEN)
                text = self.font.render("フィールド (敵が出ます！)", True, BLACK)
                self.screen.blit(text, (20, 20))

            elif self.current_map == MAP_CAMPUS:
                self.screen.fill(GRAY)
                text = self.font.render("キャンパス (奥にボスがいます)", True, BLACK)
                self.screen.blit(text, (20, 20))
            
            pygame.draw.rect(self.screen, RED, (*self.player_pos, self.player_size, self.player_size))
            
        elif self.state == STATE_BATTLE:
            enemy_color = BLUE if not self.is_boss_battle else YELLOW
            pygame.draw.rect(self.screen, enemy_color, (300, 100, 200, 200))
            
            pygame.draw.rect(self.screen, BLACK, (0, 400, SCREEN_WIDTH, 200))
            pygame.draw.rect(self.screen, WHITE, (0, 400, SCREEN_WIDTH, 200), 2)

            msg = self.font.render(self.battle_message, True, WHITE)
            self.screen.blit(msg, (50, 420))
            
            hp_msg = self.font.render(f"敵HP: {self.enemy_hp}", True, WHITE)
            self.screen.blit(hp_msg, (50, 470))

            sub_msg = self.font.render(self.battle_sub_message, True, WHITE)
            self.screen.blit(sub_msg, (50, 520))

        elif self.state == STATE_ENDING:
            self.screen.fill(WHITE)
            end_text = self.font.render("Game Clear! 単位獲得！", True, BLACK)
            self.screen.blit(end_text, (250, 300))

        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()