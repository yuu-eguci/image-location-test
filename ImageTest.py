"""pygameアプリ補助ツール ImageTest2.0
imageフォルダ内の画像を全部表示する。
画像を選択し、配置し、その座標を見て、そのデータをテキスト出力できる。
以上の操作はマウスですべて出来るし、キーボードでもすべて出来る。

0.1からの変更点
●imageフォルダの画像を全部読むので、スクリプトで画像を設定する必要がなくなった。
●選択した画像を最前面に表示するようになった。
●マウス操作に対応した。
●現在の状態をテキスト出力できるようになった。

========================================
バージョン0.2(2016-08-01)
    上述の通り完成。
バージョン1.0(2017-09-25)
    macのためにマウスクリック2をF1に変換するのを追加。
    docをつけました。
バージョン2.0(2026-10-15)
    Python 3.15 + pygame-ce に対応 (imghdrは無くなったのでpygameで読めるかで判定)。
    左クリックだけでも配置できるようにした (前はドラッグしないと動かなかった)。
    カーソルキーの画面端判定の縦横が逆だったのを修正。
    Alt+F4判定が、F4と何かの修飾キーで反応していたのを修正。
    キーの長押しは0.5秒後から連続で動くようにした。
    テキスト出力をUTF-8にした (SJISで書けないファイル名で落ちていた)。
    image, otherフォルダはスクリプトの場所から探す。
    マウスホイールの向きを上下キーに合わせた (上で前の画像、下で次の画像)。
    テキスト出力できなかったときは落ちないで、理由を表示する。
    選択中の画像を枠で囲むようにした (選択モードは黄色、配置モードは赤)。
    Shift+カーソルキーで10ピクセルずつ動かせるようにした。
    右上に画像の大きさとマウスの位置も表示するようにした。
"""

import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / 'image'
OTHER_DIR = BASE_DIR / 'other'
SCREEN_SIZE = (640, 480)
FRAMERATE = 20
# 選択中の画像を囲む枠の色
FRAME_COLORS = {'select': (255, 255, 0), 'place': (255, 0, 0)}


class Images:
    """画像のサーフィスと座標をもつクラス。
    property
        name 画像名
        surface サーフィス
        xy 座標
    """

    def __init__(self, image_path):
        self.name = image_path.name
        self.surface = pygame.image.load(image_path).convert_alpha()
        self.xy = [0, 0]


def create_image_list(image_dir):
    """フォルダの画像を全部Imagesインスタンスにしてリストを作る。画像じゃないファイルは飛ばす。"""
    image_list = []
    if not image_dir.is_dir():
        return image_list
    for path in sorted(image_dir.iterdir()):
        if not path.is_file():
            continue
        try:
            image_list.append(Images(path))
        except pygame.error:
            continue
    return image_list


class ImageTest:
    """画像選択モード('select')と画像配置モード('place')をもつアプリ本体。
    notice にメッセージが入っている間はそれを表示して、何か入力されるまで待つ。
    """

    def __init__(self, screen, font, images, output_path=Path('imagetestText.txt')):
        self.screen = screen
        self.font = font
        self.images = images
        self.output_path = output_path
        self.mode = 'select'
        self.num = 0
        self.notice = None
        self.mouse = (0, 0)
        self.running = True

    def run(self):
        """ゲームループ。"""
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            pygame.display.update()
            clock.tick(FRAMERATE)

    def draw(self):
        """画像を置いて、右上にテキストを表示する。"""
        self.screen.fill((0, 0, 0))
        for image in self.images:
            self.screen.blit(image.surface, tuple(image.xy))
        # 選択中の画像を枠で囲む (画像の1ピクセル外側)
        image = self.images[self.num]
        frame = image.surface.get_rect(topleft=image.xy).inflate(2, 2)
        pygame.draw.rect(self.screen, FRAME_COLORS[self.mode], frame, 1)
        self.blit_text(self.info_text())

    def info_text(self):
        """右上に表示するテキスト。"""
        if self.notice:
            return ['● ' + self.notice + ' ●', '  何かキーを押してください']
        image = self.images[self.num]
        width, height = image.surface.get_size()
        position = f'位置: {image.xy}  大きさ: {width}x{height}'
        mouse = f'  ﾏｳｽ: {self.mouse}'
        if self.mode == 'select':
            return [
                '<選択モード> ﾏｳｽﾎｲｰﾙ:画像選択 左ｸﾘｯｸ:決定 F1:ﾃｷｽﾄ出力',
                '▼ ' + image.name,
                '  ' + position,
                mouse,
            ]
        return [
            '<配置ﾓｰﾄﾞ> 左ｸﾘｯｸ/ﾄﾞﾗｯｸﾞ:画像配置 右ｸﾘｯｸ:戻る F1:ﾃｷｽﾄ出力',
            '  ' + image.name,
            '▼ ' + position,
            mouse,
        ]

    def blit_text(self, text_list):
        """Rect作ってその上にtext載せる"""
        # メッセージボックスの大きさを求める (一番長い行の幅+10, 行の高さ*行数+10)
        width = max(self.font.size(line)[0] for line in text_list) + 10
        height = self.font.get_linesize() * len(text_list) + 10
        # 右上にRect配置
        screen_width = self.screen.get_width()
        pygame.draw.rect(
            self.screen, (255, 255, 255), pygame.Rect(screen_width - width - 5, 5, width, height)
        )
        # テキストを置く
        for line_num, line in enumerate(text_list):
            text = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text, (screen_width - width, 10 + self.font.get_linesize() * line_num))

    def handle_event(self, event):
        """イベントをひとつ処理する。"""
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            self.mouse = event.pos
        if event.type == pygame.QUIT:
            self.running = False
        elif self.notice:
            # 何か入力があるまでメッセージを表示する
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.notice = None
        elif event.type == pygame.KEYDOWN and (
            event.key == pygame.K_ESCAPE
            or (event.key == pygame.K_F4 and event.mod & pygame.KMOD_ALT)
        ):
            self.running = False
        elif (event.type == pygame.KEYDOWN and event.key == pygame.K_F1) or (
            # F1の代替。
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 2
        ):
            self.putfile()
        elif self.mode == 'select':
            self.select_mode(event)
        else:
            self.place_mode(event)

    def select_mode(self, event):
        """画像選択モード
        上下, マウスホイール:選択
        Z, 左クリック:画像配置モードへ
        """
        last = len(self.images) - 1
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.num = self.num - 1 if self.num != 0 else last
            if event.key == pygame.K_DOWN:
                self.num = self.num + 1 if self.num != last else 0
            if event.key == pygame.K_z:
                self.change_image_order()
                self.mode = 'place'
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.change_image_order()
                self.mode = 'place'
            # マウスホイール上下 (上下キーと同じ向き)
            if event.button == 4:
                self.num = self.num - 1 if self.num != 0 else last
            if event.button == 5:
                self.num = self.num + 1 if self.num != last else 0

    def change_image_order(self):
        """現在選択されてる画像をリストの最後(最前面)にもってくる。
        背景画像が前面に出てしまったときの対策。"""
        self.images.append(self.images.pop(self.num))
        self.num = len(self.images) - 1

    def place_mode(self, event):
        """画像配置モード
        マウスクリック, ドラッグ:その座標に配置
        カーソルキー:1ピクセルずつ移動 (Shiftを押しながらだと10ピクセルずつ)
        X, 右クリック:画像選択モードへ
        """
        image = self.images[self.num]
        x, y = image.xy
        if event.type == pygame.KEYDOWN:
            step = 10 if event.mod & pygame.KMOD_SHIFT else 1
            if event.key == pygame.K_x:
                self.mode = 'select'
            # 上下左右で画像移動 (画面の外には出さない)
            if event.key == pygame.K_UP:
                image.xy[1] = max(y - step, 0)
            if event.key == pygame.K_DOWN:
                image.xy[1] = min(y + step, self.screen.get_height() - 1)
            if event.key == pygame.K_LEFT:
                image.xy[0] = max(x - step, 0)
            if event.key == pygame.K_RIGHT:
                image.xy[0] = min(x + step, self.screen.get_width() - 1)
        # マウスクリック(左)とドラッグ(左)で画像移動
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or (
            event.type == pygame.MOUSEMOTION and event.buttons[0]
        ):
            image.xy = list(event.pos)
        # マウスクリック(右)で戻る
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.mode = 'select'

    def putfile(self):
        """画像の一覧をテキスト出力する。書き込めなかったら理由を表示する。"""
        text = ''.join(f'{image.name} {image.xy}\n' for image in self.images)
        try:
            self.output_path.write_text(text, encoding='utf-8')
        except OSError as error:
            self.notice = f'テキスト出力できませんでした ({error.strerror})'
        else:
            self.notice = 'データをテキスト出力しました'


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    icon = pygame.image.load(OTHER_DIR / 'pythongreen32x32.png').convert_alpha()
    icon.set_colorkey(icon.get_at((0, 0)), pygame.RLEACCEL)
    pygame.display.set_icon(icon)
    pygame.display.set_caption('画像配置テスト ESCキーで終了できます')
    # 長押しを有効化する。0.5秒押し続けたら、あとはフレームごとくらいの間隔で動く
    pygame.key.set_repeat(500, 50)
    font = pygame.font.Font(OTHER_DIR / 'VL-Gothic-Regular.ttf', 12)
    images = create_image_list(IMAGE_DIR)
    if not images:
        pygame.quit()
        sys.exit(f'{IMAGE_DIR} に画像がありません。')
    ImageTest(screen, font, images).run()
    pygame.quit()


if __name__ == '__main__':
    main()
