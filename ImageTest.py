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
    Python 3.14以上 + pygame-ce に対応 (imghdrは無くなったのでpygameで読めるかで判定)。
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
    右上に画像の大きさとマウスの位置 (選択中の画像の左上からの位置も) を表示するようにした。
    起動したときにテキスト出力したファイルがあれば、その位置と重なり順を読み込む。
    Sキーでもテキスト出力できるようにした (MacやブラウザだとF1が押しにくいので)。
    画面の大きさを環境変数 IMAGETEST_SIZE で変えられるようにした。
    Bキーで背景を黒、灰色、白、チェック柄に切り替えられるようにした。
    Hキーで右上の表示と枠を隠せるようにした。
    F5キーでimageフォルダを読みなおせるようにした (位置はそのまま)。
    開けない画像ファイルは飛ばすようにした (前は落ちていた)。
    メッセージを閉じたクリックのままドラッグしても画像が動かないようにした。
    画面の外にある画像をカーソルキーで動かしたときに、画面の端まで飛ばないようにした。
    保存していない変更があるときは、ESCを2回押さないと終了しないようにした。
    F2キーでヘルプを表示するようにした。
    右上に画像の右下の座標 (位置+大きさ) も表示するようにした。
    保存したファイルが無いときは、大きい画像ほど奥に置くようにした (背景で全部隠れないように)。
    Uキーで、ひとつ前の位置と重なり順に戻せるようにした。
    Home, End, PageUp, PageDownで画像を画面の端にぴったり置けるようにした。
    Tabキーでマウスの下にある画像を選べるようにした (押すたびに奥の画像へ)。
    Gキーで方眼 (8, 16, 32ピクセル) を表示できるようにした。
    Mキーでマウスのまわりを8倍に拡大して表示できるようにした。
    Shift+Zで選択中の画像を一番奥に送れるようにした。
    Ctrl+Z (MacはCmd+Z) でも元に戻せるようにした。
    小さい画面では右上の表示を折り返すようにした。拡大表示はマウスが重なったら右下へ逃げる。
"""

import os
import re
import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / 'image'
OTHER_DIR = BASE_DIR / 'other'
# テキスト出力するファイル (カレントディレクトリ)。1行に「画像名 [x, y]」
OUTPUT_FILE = Path('imagetestText.txt')
LINE_PATTERN = re.compile(r'(.+) \[(-?\d+), (-?\d+)\]')
# 画面の大きさ。環境変数 IMAGETEST_SIZE (例: 800x600) で変えられる
SCREEN_SIZE = (640, 480)
FRAMERATE = 20
# 選択中の画像を囲む枠の色
FRAME_COLORS = {'select': (255, 255, 0), 'place': (255, 0, 0)}
# Bキーで切り替える背景 (Noneはチェック柄)
BACKGROUNDS = [(0, 0, 0), (128, 128, 128), (255, 255, 255), None]
# Gキーで切り替える方眼の間隔 (0は無し)
GRID_SPACINGS = [0, 8, 16, 32]
GRID_COLOR = (0, 255, 255)
# Mキーの拡大表示: マウスのまわり LOUPE_SIZE ピクセル四方を LOUPE_SCALE 倍で左下に出す
LOUPE_SIZE = 15
LOUPE_SCALE = 8
# Uキーで戻れる回数
HISTORY_LIMIT = 100
QUIT_WARNING = '保存していません。もう一度押すと終了'
HELP_TEXT = [
    '<ﾍﾙﾌﾟ> F2:閉じる',
    '選択ﾓｰﾄﾞ  上下/ﾎｲｰﾙ:画像選択  Tab:ﾏｳｽの下の画像',
    '          Z/左ｸﾘｯｸ:手前にして配置ﾓｰﾄﾞへ  Shift+Z:一番奥へ',
    '配置ﾓｰﾄﾞ  ｶｰｿﾙ:1px  Shift+ｶｰｿﾙ:10px  左ｸﾘｯｸ/ﾄﾞﾗｯｸﾞ:配置',
    '          Home/End/PageUp/PageDown:画面の端へ  X/右ｸﾘｯｸ:選択ﾓｰﾄﾞへ',
    'F1/S/中ｸﾘｯｸ:ﾃｷｽﾄ出力  F5:画像の読みなおし  U/Ctrl+Z:元に戻す',
    'B:背景  G:方眼  M:拡大  H:表示を隠す  ESC/Alt+F4:終了',
]


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

    def rect(self):
        """画面上で画像がある範囲。"""
        return self.surface.get_rect(topleft=self.xy)


def screen_size():
    """環境変数 IMAGETEST_SIZE があればその大きさ、無ければ SCREEN_SIZE。"""
    value = os.environ.get('IMAGETEST_SIZE')
    if not value:
        return SCREEN_SIZE
    match = re.fullmatch(r'([1-9]\d*)x([1-9]\d*)', value)
    if not match:
        sys.exit(f'IMAGETEST_SIZE は 800x600 のように書いてください: {value}')
    return int(match[1]), int(match[2])


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
        except pygame.error, OSError:
            continue
    return image_list


def image_area(image):
    """画像の面積。"""
    width, height = image.surface.get_size()
    return width * height


def apply_layout(images, layout):
    """(画像名, [x, y]) の並びのとおりに位置と重なり順をそろえる。並びに無い画像は前面に置く。"""
    unplaced = {image.name: image for image in images}
    placed = []
    for name, xy in layout:
        if name in unplaced:
            image = unplaced.pop(name)
            image.xy = list(xy)
            placed.append(image)
    return placed + [image for image in images if image.name in unplaced]


def restore_positions(images, path):
    """前回テキスト出力した位置と重なり順を読み込む。読めないファイルや行は無視する。"""
    try:
        # エディタで編集してBOMが付いても読めるように utf-8-sig
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except OSError, UnicodeDecodeError:
        return images
    matches = (LINE_PATTERN.fullmatch(line) for line in lines)
    return apply_layout(images, [(m[1], [int(m[2]), int(m[3])]) for m in matches if m])


def is_quit_key(event):
    """ESCかAlt+F4。"""
    return event.type == pygame.KEYDOWN and (
        event.key == pygame.K_ESCAPE or (event.key == pygame.K_F4 and event.mod & pygame.KMOD_ALT)
    )


def is_undo_key(event):
    """UかCtrl+Z (MacならCmd+Z)。"""
    return event.type == pygame.KEYDOWN and (
        event.key == pygame.K_u
        or (event.key == pygame.K_z and event.mod & (pygame.KMOD_CTRL | pygame.KMOD_GUI))
    )


class ImageTest:
    """画像選択モード('select')と画像配置モード('place')をもつアプリ本体。
    notice にメッセージが入っている間はそれを表示して、何か入力されるまで待つ。
    """

    def __init__(self, screen, font, images, output_path=OUTPUT_FILE, image_dir=IMAGE_DIR):
        self.screen = screen
        self.font = font
        self.images = images
        self.output_path = output_path
        self.image_dir = image_dir
        self.mode = 'select'
        self.num = 0
        self.notice = None
        self.mouse = (0, 0)
        # メッセージを閉じたクリックのまま、ドラッグで画像が動かないようにする
        self.drag_blocked = False
        self.background = 0
        self.grid = 0
        self.show_loupe = False
        self.show_info = True
        self.show_help = False
        self.saved_layout = self.layout()
        # Uキーで戻すための、変更前の (画像名, 位置) の並び
        self.history = []
        # 左ボタンを押している間 True。同じキーを続けて押したら1回分として覚えるための、前のキー
        self.pressed = False
        self.last_key = None
        self.running = True

    def layout(self):
        """今の (画像名, 位置) の並び。"""
        return [(image.name, list(image.xy)) for image in self.images]

    @property
    def dirty(self):
        """最後にテキスト出力 (か起動) してから、位置か重なり順が変わったか。"""
        return self.layout() != self.saved_layout

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
        self.fill_background()
        for image in self.images:
            self.screen.blit(image.surface, tuple(image.xy))
        self.draw_grid()
        # 拡大表示は枠より上に出すが、中身は枠を描く前の画面
        area = self.mouse_area() if self.show_loupe else None
        if self.show_info:
            # 選択中の画像を枠で囲む (画像の1ピクセル外側)
            image = self.images[self.num]
            frame = image.rect().inflate(2, 2)
            pygame.draw.rect(self.screen, FRAME_COLORS[self.mode], frame, 1)
        if area:
            self.draw_loupe(area)
        if self.show_info or self.notice or self.show_help:
            self.blit_text(self.wrap(self.info_text()))

    def draw_grid(self):
        """方眼を描く。"""
        spacing = GRID_SPACINGS[self.grid]
        if not spacing:
            return
        width, height = self.screen.get_size()
        for x in range(0, width, spacing):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, height - 1))
        for y in range(0, height, spacing):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (width - 1, y))

    def mouse_area(self):
        """マウスのまわり LOUPE_SIZE ピクセル四方の画面のコピー。画面の外は黒。"""
        mx, my = self.mouse
        half = LOUPE_SIZE // 2
        area = pygame.Surface((LOUPE_SIZE, LOUPE_SIZE))
        area.blit(self.screen, (0, 0), pygame.Rect(mx - half, my - half, LOUPE_SIZE, LOUPE_SIZE))
        return area

    def draw_loupe(self, area):
        """area を拡大して左下 (マウスが左下にあるときは右下) に表示する。
        真ん中の赤い枠がマウスのピクセル。"""
        half = LOUPE_SIZE // 2
        zoomed = pygame.transform.scale_by(area, LOUPE_SCALE)
        width, height = self.screen.get_size()
        left, top = 5, height - 5 - zoomed.get_height()
        if zoomed.get_rect(topleft=(left, top)).collidepoint(self.mouse):
            left = width - 5 - zoomed.get_width()
        self.screen.blit(zoomed, (left, top))
        pygame.draw.rect(self.screen, (255, 255, 255), zoomed.get_rect(topleft=(left, top)), 1)
        center = (left + half * LOUPE_SCALE, top + half * LOUPE_SCALE, LOUPE_SCALE, LOUPE_SCALE)
        pygame.draw.rect(self.screen, (255, 0, 0), center, 1)

    def fill_background(self):
        """背景を塗る。チェック柄は16ピクセルの市松模様。"""
        color = BACKGROUNDS[self.background]
        if color:
            self.screen.fill(color)
            return
        self.screen.fill((102, 102, 102))
        width, height = self.screen.get_size()
        for y in range(0, height, 16):
            for x in range(y // 16 % 2 * 16, width, 32):
                self.screen.fill((153, 153, 153), (x, y, 16, 16))

    def info_text(self):
        """右上に表示するテキスト。"""
        if self.notice:
            return ['● ' + self.notice + ' ●', '  何かキーを押してください']
        if self.show_help:
            return HELP_TEXT
        image = self.images[self.num]
        unsaved = '  *未保存' if self.dirty else ''
        width, height = image.surface.get_size()
        x, y = image.xy
        position = f'位置: {image.xy}  大きさ: {width}x{height}  右下: ({x + width}, {y + height})'
        mx, my = self.mouse
        mouse = f'  ﾏｳｽ: {self.mouse}  画像内: ({mx - x}, {my - y})'
        if self.mode == 'select':
            return [
                '<選択モード> ﾏｳｽﾎｲｰﾙ:画像選択 左ｸﾘｯｸ:決定 F1:ﾃｷｽﾄ出力 F2:ﾍﾙﾌﾟ',
                '▼ ' + image.name + unsaved,
                '  ' + position,
                mouse,
            ]
        return [
            '<配置ﾓｰﾄﾞ> 左ｸﾘｯｸ/ﾄﾞﾗｯｸﾞ:画像配置 右ｸﾘｯｸ:戻る F1:ﾃｷｽﾄ出力 F2:ﾍﾙﾌﾟ',
            '  ' + image.name + unsaved,
            '▼ ' + position,
            mouse,
        ]

    def wrap(self, text_list):
        """画面の幅に入らない行は、スペースのところで折り返す (小さい IMAGETEST_SIZE 用)。"""
        max_width = self.screen.get_width() - 20
        lines = []
        for line in text_list:
            if self.font.size(line)[0] <= max_width:
                lines.append(line)
                continue
            current = ''
            for word in line.split():
                if current and self.font.size(f'{current} {word}')[0] > max_width:
                    lines.append(current)
                    current = '  ' + word
                else:
                    current = f'{current} {word}' if current else word
            lines.append(current)
        return lines

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
        """イベントをひとつ処理する。位置か重なり順が変わったら、元に戻せるように変更前を覚えておく。
        クリックとそのままのドラッグは1回分、同じキーを続けて押したのも1回分。F5の読みなおしは覚えない。"""
        if is_undo_key(event) and not self.notice:
            self.undo()
            # ドラッグ中なら、そのドラッグはやめる
            self.drag_blocked = self.pressed
            self.last_key = None
            return
        notice = self.notice
        before = self.layout()
        self.process(event)
        if event.type == pygame.KEYDOWN and event.key != pygame.K_F5:
            changed = self.layout() != before
            if changed and event.key != self.last_key:
                self.remember(before)
            self.last_key = event.key if changed else None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # このあとドラッグするかもしれないので、変わっていなくても覚えておく
            self.pressed = True
            self.last_key = None
            if not notice:
                self.remember(before)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # 結局なにも変わらなかったクリックは忘れる
            self.pressed = False
            if self.history and self.history[-1] == self.layout():
                self.history.pop()

    def remember(self, layout):
        """元に戻せるように並びを覚える。"""
        if self.history and self.history[-1] == layout:
            return
        self.history = [*self.history, layout][-HISTORY_LIMIT:]

    def undo(self):
        """ひとつ前の位置と重なり順に戻す。選択中の画像はそのまま。"""
        if self.history:
            self.select_by_name(self.images[self.num].name, self.history.pop())

    def select_by_name(self, name, layout, images=None):
        """images (省略したら今の画像) を layout の並びにして、name の画像を選びなおす。
        name の画像が無くなっていたら、選択モードで最初の画像を選ぶ。"""
        self.images = apply_layout(self.images if images is None else images, layout)
        names = [image.name for image in self.images]
        if name in names:
            self.num = names.index(name)
        else:
            self.num = 0
            self.mode = 'select'

    def process(self, event):
        """イベントをひとつ処理する (元に戻す以外)。"""
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            self.mouse = event.pos
        if event.type == pygame.MOUSEBUTTONUP:
            self.drag_blocked = False
        # ウィンドウを閉じたときと、確認のあとにもう一度ESCを押したときは終了
        if event.type == pygame.QUIT or (self.notice == QUIT_WARNING and is_quit_key(event)):
            self.running = False
        elif self.notice:
            # 何か入力があるまでメッセージを表示する
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.notice = None
                self.drag_blocked = event.type == pygame.MOUSEBUTTONDOWN
        elif is_quit_key(event):
            # 保存していない変更があったら、一度だけ確認する
            if self.dirty:
                self.notice = QUIT_WARNING
            else:
                self.running = False
        elif (event.type == pygame.KEYDOWN and event.key in (pygame.K_F1, pygame.K_s)) or (
            # F1の代替。
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 2
        ):
            self.putfile()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
            self.reload()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_b:
            self.background = (self.background + 1) % len(BACKGROUNDS)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            self.grid = (self.grid + 1) % len(GRID_SPACINGS)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.show_loupe = not self.show_loupe
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            self.show_info = not self.show_info
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.show_help = not self.show_help
        elif self.mode == 'select':
            self.select_mode(event)
        else:
            self.place_mode(event)

    def select_mode(self, event):
        """画像選択モード
        上下, マウスホイール:選択
        Tab:マウスの下の画像を手前から選択
        Z, 左クリック:画像配置モードへ
        Shift+Z:選択中の画像を一番奥へ
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.choose_next(-1)
            if event.key == pygame.K_DOWN:
                self.choose_next(1)
            if event.key == pygame.K_TAB:
                self.choose_under_mouse()
            if event.key == pygame.K_z and event.mod & pygame.KMOD_SHIFT:
                self.send_to_back()
            elif event.key == pygame.K_z:
                self.change_image_order()
                self.mode = 'place'
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.change_image_order()
                self.mode = 'place'
            # マウスホイール上下 (上下キーと同じ向き)
            if event.button == 4:
                self.choose_next(-1)
            if event.button == 5:
                self.choose_next(1)

    def choose_next(self, step):
        """ひとつ前 (-1) か次 (1) の画像を選ぶ。端まで行ったら反対の端へ。"""
        self.num = (self.num + step) % len(self.images)

    def choose_under_mouse(self):
        """マウスの下にある画像を手前から選ぶ。もう一度呼ぶと、その奥の画像を選ぶ。"""
        nums = reversed(range(len(self.images)))
        under = [num for num in nums if self.images[num].rect().collidepoint(self.mouse)]
        if not under:
            return
        next_index = under.index(self.num) + 1 if self.num in under else 0
        self.num = under[next_index % len(under)]

    def change_image_order(self):
        """現在選択されてる画像をリストの最後(最前面)にもってくる。
        背景画像が前面に出てしまったときの対策。"""
        self.images.append(self.images.pop(self.num))
        self.num = len(self.images) - 1

    def send_to_back(self):
        """現在選択されてる画像をリストの最初(一番奥)にもってくる。前面に出てしまった背景画像用。"""
        self.images.insert(0, self.images.pop(self.num))
        self.num = 0

    def place_mode(self, event):
        """画像配置モード
        マウスクリック, ドラッグ:その座標に配置
        カーソルキー:1ピクセルずつ移動 (Shiftを押しながらだと10ピクセルずつ)
        Home, End, PageUp, PageDown:画面の左端、右端、上端、下端に置く
        X, 右クリック:画像選択モードへ
        """
        image = self.images[self.num]
        x, y = image.xy
        if event.type == pygame.KEYDOWN:
            step = 10 if event.mod & pygame.KMOD_SHIFT else 1
            if event.key == pygame.K_x:
                self.mode = 'select'
            # 上下左右で画像移動 (画面の外には出さない。もう外にあるときはその場で止める)
            width, height = self.screen.get_size()
            if event.key == pygame.K_UP:
                image.xy[1] = max(y - step, min(y, 0))
            if event.key == pygame.K_DOWN:
                image.xy[1] = min(y + step, max(y, height - 1))
            if event.key == pygame.K_LEFT:
                image.xy[0] = max(x - step, min(x, 0))
            if event.key == pygame.K_RIGHT:
                image.xy[0] = min(x + step, max(x, width - 1))
            # Home, End, PageUp, PageDownで画面の左端、右端、上端、下端にぴったり置く
            image_width, image_height = image.surface.get_size()
            if event.key == pygame.K_HOME:
                image.xy[0] = 0
            if event.key == pygame.K_END:
                image.xy[0] = width - image_width
            if event.key == pygame.K_PAGEUP:
                image.xy[1] = 0
            if event.key == pygame.K_PAGEDOWN:
                image.xy[1] = height - image_height
        # マウスクリック(左)とドラッグ(左)で画像移動
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or (
            event.type == pygame.MOUSEMOTION and event.buttons[0] and not self.drag_blocked
        ):
            image.xy = list(event.pos)
        # マウスクリック(右)で戻る
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.mode = 'select'

    def reload(self):
        """画像フォルダを読みなおす。位置と重なり順と選択中の画像はそのまま。"""
        images = create_image_list(self.image_dir)
        if not images:
            self.notice = f'{self.image_dir} に画像がありません'
            return
        self.select_by_name(self.images[self.num].name, self.layout(), images)

    def putfile(self):
        """画像の一覧をテキスト出力する。書き込めなかったら理由を表示する。"""
        text = ''.join(f'{image.name} {image.xy}\n' for image in self.images)
        try:
            self.output_path.write_text(text, encoding='utf-8')
        except OSError as error:
            self.notice = f'テキスト出力できませんでした ({error.strerror})'
        else:
            self.notice = 'データをテキスト出力しました'
            self.saved_layout = self.layout()


def main():
    size = screen_size()
    pygame.init()
    screen = pygame.display.set_mode(size)
    icon = pygame.image.load(OTHER_DIR / 'pythongreen32x32.png').convert_alpha()
    icon.set_colorkey(icon.get_at((0, 0)), pygame.RLEACCEL)
    pygame.display.set_icon(icon)
    pygame.display.set_caption('画像配置テスト ESCキーで終了できます')
    # 長押しを有効化する。0.5秒押し続けたら、あとはフレームごとくらいの間隔で動く
    pygame.key.set_repeat(500, 50)
    font = pygame.font.Font(OTHER_DIR / 'VL-Gothic-Regular.ttf', 12)
    # 大きい画像 (背景など) ほど奥に置く。保存したファイルがあればそちらの並びが優先
    images = sorted(create_image_list(IMAGE_DIR), key=image_area, reverse=True)
    if not images:
        pygame.quit()
        sys.exit(f'{IMAGE_DIR} に画像がありません。')
    ImageTest(screen, font, restore_positions(images, OUTPUT_FILE), image_dir=IMAGE_DIR).run()
    pygame.quit()


if __name__ == '__main__':
    main()
