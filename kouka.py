import pygame
import sys
import random
import os


# --- 設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60


# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)   # 草原
GRAY = (169, 169, 169)  # キャンパス床
RED = (255, 0, 0)       # こうかとん
BLUE = (0, 0, 255)      # 雑魚敵
YELLOW = (255, 215, 0)  # ボス


# 状態定数
STATE_MAP = "MAP"
STATE_BATTLE = "BATTLE"
STATE_ENDING = "ENDING"
STATE_GAME_OVER = "GAME_OVER"


# マップID
MAP_VILLAGE = 0
MAP_FIELD = 1
MAP_CAMPUS = 2


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RPG こうく")
        self.clock = pygame.time.Clock()
       
        # 日本語フォントの設定（OSに合わせて読み込む）
        self.font = self.get_japanese_font(32)
        # 戦闘メッセージなど用の小さいフォント
        self.msg_font = self.get_japanese_font(20)

        # ゲーム進行管理（初期状態）
        self.state = STATE_MAP
        self.current_map = MAP_VILLAGE

        # プレイヤー初期状態
        self.player_pos = [50, 300]
        self.player_size = 40
        self.speed = 5
        # プレイヤーHP
        self.player_max_hp = 500
        self.player_hp = self.player_max_hp
        self.is_boss_battle = False
       
        # 戦闘用変数
        self.enemy_hp = 0
        self.battle_message = ""
        self.battle_sub_message = ""
        # 回復回数（戦闘ごとにリセット）
        self.heals_left = 0
        # アイテム（回復薬、攻撃力アップ、防御力アップ）
        self.items = {"potion": 3, "atk": 1, "def": 1}
        # バフ（ターン数）と倍率
        self.atk_buff_turns = 0
        self.def_buff_turns = 0
        self.atk_multiplier = 1.0
        self.def_multiplier = 1.0
        # メッセージログ（戦闘内で行動ごとに更新）
        self.message_log = []
        self.max_messages = 4


    def get_japanese_font(self, size):
        """OS標準の日本語フォントを優先的に探して返す"""
        # Windows, Mac, Linuxで一般的な日本語フォント名
        font_names = ["meiryo", "msgothic", "yugothic", "hiraginosans", "notosanscjkjp", "takaoexgothic"]
        available_fonts = pygame.font.get_fonts()
       
        selected_font = None
        for name in font_names:
            if name in available_fonts:
                selected_font = name
                break
       
        if selected_font:
            return pygame.font.SysFont(selected_font, size)
        else:
            # 見つからない場合はデフォルト（日本語が表示できない可能性あり）
            print("警告: 日本語フォントが見つかりませんでした。")
            return pygame.font.Font(None, size)


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
           
            # 戦闘中・エンディング中の操作
            if event.type == pygame.KEYDOWN:
                if self.state == STATE_BATTLE:
                    if event.key == pygame.K_SPACE:
                        # プレイヤーの攻撃処理（攻撃バフを反映）
                        base_damage = random.randint(30, 60)
                        damage = int(base_damage * self.atk_multiplier)
                        self.enemy_hp -= damage
                        self.add_message(f"こうかとんの攻撃！ {damage} のダメージ！")
                        if self.enemy_hp > 0:
                            # 敵が生きていれば反撃（共通処理）
                            self.enemy_counterattack()
                        else:
                            # 敵を倒した
                            self.add_message("敵を倒した！")
                            self.end_battle()

                    elif event.key == pygame.K_h:
                        # 回復処理（使える回数がある場合のみ）
                        if self.heals_left > 0:
                            # 回復量は通常敵とボスで少し変える
                            if self.is_boss_battle:
                                heal = random.randint(500, 1000)
                            else:
                                heal = random.randint(200, 400)
                            old_hp = self.player_hp
                            self.player_hp = min(self.player_max_hp, self.player_hp + heal)
                            actual_heal = self.player_hp - old_hp
                            self.heals_left -= 1
                            self.add_message(f"こうかとんは回復した！ +{actual_heal} HP")
                            # 回復した後、敵の反撃（共通処理）
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("回復できる回数がありません！")

                    elif event.key == pygame.K_1:
                        # 回復薬使用
                        if self.items.get("potion", 0) > 0:
                            heal_amount = random.randint(100, 200)
                            old_hp = self.player_hp
                            self.player_hp = min(self.player_max_hp, self.player_hp + heal_amount)
                            actual = self.player_hp - old_hp
                            self.items["potion"] -= 1
                            self.add_message(f"回復薬を使用！ +{actual} HP")
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("回復薬がありません！")

                    elif event.key == pygame.K_2:
                        # 攻撃力アップ使用
                        if self.items.get("atk", 0) > 0:
                            self.items["atk"] -= 1
                            self.atk_buff_turns = 3
                            self.atk_multiplier = 1.5
                            self.add_message("攻撃力アップを使用！ 次の数ターン攻撃力上昇")
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("攻撃力アップがありません！")

                    elif event.key == pygame.K_3:
                        # 防御力アップ使用
                        if self.items.get("def", 0) > 0:
                            self.items["def"] -= 1
                            self.def_buff_turns = 3
                            self.def_multiplier = 0.5
                            self.add_message("防御力アップを使用！ 次の数ターン被ダメ半減")
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("防御力アップがありません！")
                    elif event.key == pygame.K_2:
                        # 攻撃力アップ使用
                        if self.items.get("atk", 0) > 0:
                            self.items["atk"] -= 1
                            self.atk_buff_turns = 3
                            self.atk_multiplier = 1.5
                            self.battle_message = "攻撃力アップを使用！ 次の数ターン攻撃力上昇"
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.battle_sub_message = "攻撃力アップがありません！"

                    elif event.key == pygame.K_3:
                        # 防御力アップ使用
                        if self.items.get("def", 0) > 0:
                            self.items["def"] -= 1
                            self.def_buff_turns = 3
                            self.def_multiplier = 0.5
                            self.battle_message = "防御力アップを使用！ 次の数ターン被ダメ半減"
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.battle_sub_message = "防御力アップがありません！"
                elif self.state == STATE_ENDING:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif self.state == STATE_GAME_OVER:
                    # Rでリトライ、ESCで終了
                    if event.key == pygame.K_r:
                        self.restart()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()


    def update(self):
        if self.state == STATE_MAP:
            keys = pygame.key.get_pressed()
            moved = False
           
            # 移動処理
            if keys[pygame.K_LEFT]:
                self.player_pos[0] -= self.speed
                moved = True
            if keys[pygame.K_RIGHT]:
                self.player_pos[0] += self.speed
                moved = True
            if keys[pygame.K_UP]:
                self.player_pos[1] -= self.speed
                moved = True
            if keys[pygame.K_DOWN]:
                self.player_pos[1] += self.speed
                moved = True


            # マップ遷移判定とエンカウント
            self.check_map_transition()
            if moved and self.current_map == MAP_FIELD:
                self.check_random_encounter()
           
            # ボスイベント判定（キャンパス奥地）
            if self.current_map == MAP_CAMPUS and self.player_pos[0] > 700:
                self.start_battle(is_boss=True)


    def check_map_transition(self):
        # 画面端でのマップ切り替え
        if self.player_pos[0] > SCREEN_WIDTH:
            if self.current_map < MAP_CAMPUS:
                self.current_map += 1
                self.player_pos[0] = 10 # 次のマップの左端へ
            else:
                self.player_pos[0] = SCREEN_WIDTH - self.player_size # 行き止まり


        elif self.player_pos[0] < 0:
            if self.current_map > MAP_VILLAGE:
                self.current_map -= 1
                self.player_pos[0] = SCREEN_WIDTH - 10 # 前のマップの右端へ
            else:
                self.player_pos[0] = 0 # 行き止まり


    # --- 重要：遷移関数 ---
    def check_random_encounter(self):
        # 1%の確率で戦闘開始（移動中常に呼ばれる）
        if random.randint(0, 100) < 1: # 遭遇率調整
            self.start_battle(is_boss=False)


    def start_battle(self, is_boss):
        self.state = STATE_BATTLE
        self.is_boss_battle = is_boss
        # 回復を使える回数を設定
        self.heals_left = 3 if not is_boss else 5
        # メッセージログをリセットして見やすくする
        self.message_log = []
        if is_boss:
            self.enemy_hp = 500
            self.add_message("「単位を奪う悪の組織」が現れた！")
        else:
            self.enemy_hp = 100
            self.add_message("「未提出の課題」が現れた！")
        # 操作説明を最初に表示
        self.add_message("操作: SPACE 攻撃  H 回復  1:回復薬 2:攻撃UP 3:防御UP")


    def end_battle(self):
        if self.is_boss_battle:
            self.state = STATE_ENDING
        else:
            self.state = STATE_MAP
            self.battle_message = ""
            # 戦闘終了後、再エンカウント防止のために少し座標をずらすなどの処理を入れるとより良い
            pygame.time.wait(500) # 少しウェイトを入れる

    def game_over(self):
        """プレイヤーのHPが0になったときの処理"""
        self.state = STATE_GAME_OVER

    def restart(self):
        """簡易リスタート（村に戻りHP回復）"""
        self.state = STATE_MAP
        self.current_map = MAP_VILLAGE
        self.player_pos = [50, 300]
        self.player_hp = self.player_max_hp
        self.enemy_hp = 0
        self.battle_message = ""
        self.battle_sub_message = ""
        self.heals_left = 0
        self.clear_messages()
        # アイテム・バフもリセット
        self.items = {"potion": 3, "atk": 1, "def": 1}
        self.atk_buff_turns = 0
        self.def_buff_turns = 0
        self.atk_multiplier = 1.0
        self.def_multiplier = 1.0

    def enemy_counterattack(self):
        """敵の反撃処理（防御バフを適用、バフターンを減らす）"""
        if self.enemy_hp <= 0:
            return
        # 敵の攻撃ダメージはボスか通常で変える
        if self.is_boss_battle:
            edamage = random.randint(30, 80)
        else:
            edamage = random.randint(10, 30)
        # 防御バフを適用
        edamage = max(1, int(edamage * self.def_multiplier))
        self.player_hp -= edamage
        # 表示用メッセージを追加
        self.add_message(f"敵の反撃！ {edamage} のダメージ！ (残りHP: {max(0, self.player_hp)}) 回復残り: {self.heals_left} 回復薬: {self.items.get('potion',0)}")
        if self.player_hp <= 0:
            self.game_over()
        # バフのターンを減らす
        if self.atk_buff_turns > 0:
            self.atk_buff_turns -= 1
            if self.atk_buff_turns == 0:
                self.atk_multiplier = 1.0
        if self.def_buff_turns > 0:
            self.def_buff_turns -= 1
            if self.def_buff_turns == 0:
                self.def_multiplier = 1.0

    def add_message(self, text):
        """メッセージをログに追加し、最大長を超えたら古いものを削除する"""
        self.message_log.append(text)
        # 最新メッセージのみ保持
        if len(self.message_log) > self.max_messages:
            self.message_log = self.message_log[-self.max_messages:]

    def clear_messages(self):
        self.message_log = []


    def draw(self):
        self.screen.fill(BLACK)


        if self.state == STATE_MAP:
            # 背景描画
            color = GREEN
            loc_text = ""
            if self.current_map == MAP_VILLAGE:
                color = (100, 200, 100)
                loc_text = "最初の村（右へ進もう）"
            elif self.current_map == MAP_FIELD:
                color = GREEN
                loc_text = "外の散策エリア（敵が出ます）"
            elif self.current_map == MAP_CAMPUS:
                color = GRAY
                loc_text = "八王子キャンパス（奥にボスがいます）"
           
            pygame.draw.rect(self.screen, color, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
           
            # プレイヤー（こうかとん）
            pygame.draw.rect(self.screen, RED, (*self.player_pos, self.player_size, self.player_size))
           
            # ガイド表示
            text = self.font.render(loc_text, True, BLACK)
            self.screen.blit(text, (20, 20))


        elif self.state == STATE_BATTLE:
            # 戦闘画面
            # 敵の描画
            enemy_color = BLUE if not self.is_boss_battle else YELLOW
            pygame.draw.rect(self.screen, enemy_color, (300, 100, 200, 200))
           
            # メッセージ枠
            pygame.draw.rect(self.screen, BLACK, (0, 400, SCREEN_WIDTH, 200))
            pygame.draw.rect(self.screen, WHITE, (0, 400, SCREEN_WIDTH, 200), 2)


            # メッセージログ（最新のメッセージを上から順に表示）
            y = 420
            for m in self.message_log[-self.max_messages:]:
                msg = self.msg_font.render(m, True, WHITE)
                self.screen.blit(msg, (50, y))
                y += 22

            hp_msg = self.msg_font.render(f"敵HP: {self.enemy_hp}", True, WHITE)
            self.screen.blit(hp_msg, (50, y))

            # プレイヤーHP表示
            p_hp_msg = self.msg_font.render(f"プレイヤーHP: {self.player_hp}", True, WHITE)
            self.screen.blit(p_hp_msg, (400, y))

            # 回復残り表示
            heal_msg = self.msg_font.render(f"回復残り: {self.heals_left}", True, WHITE)
            self.screen.blit(heal_msg, (400, y+30))

            # アイテム表示
            item_msg = self.msg_font.render(f"回復薬: {self.items.get('potion',0)}  攻撃UP: {self.items.get('atk',0)}  防御UP: {self.items.get('def',0)}", True, WHITE)
            self.screen.blit(item_msg, (50, 395))

            # バフ残り表示
            buff_msg = self.msg_font.render(f"ATK+:{self.atk_buff_turns}  DEF-:{self.def_buff_turns}", True, WHITE)
            self.screen.blit(buff_msg, (400, y+60))


        elif self.state == STATE_ENDING:
            # エンディング（白暗転）
            self.screen.fill(WHITE)
            end_text1 = self.font.render("単位は守られた！", True, BLACK)
            end_text2 = self.font.render("Thank you for playing.", True, BLACK)
           
            self.screen.blit(end_text1, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 20))
            self.screen.blit(end_text2, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 30))

        elif self.state == STATE_GAME_OVER:
            # ゲームオーバー画面
            self.screen.fill(BLACK)
            go_text = self.font.render("GAME OVER", True, RED)
            info_text = self.font.render("R: リトライ    ESC: 終了", True, WHITE)
            self.screen.blit(go_text, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 - 30))
            self.screen.blit(info_text, (SCREEN_WIDTH//2 - 140, SCREEN_HEIGHT//2 + 30))


        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()

