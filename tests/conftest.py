"""pytest 共通設定。

ここでのテストは SDL の dummy ドライバ上で動く (画面は出ない)。
イベントもテスト内で作った合成イベントを直接渡している。
実際の画面とマウス・キーボード操作での確認は README の Docker 手順で行う。
"""

import os

import pygame
import pytest

import ImageTest

# pygame.init() より前に設定する
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'


@pytest.fixture
def screen():
    pygame.init()
    yield pygame.display.set_mode(ImageTest.SCREEN_SIZE)
    pygame.quit()


@pytest.fixture
def font(screen):
    return pygame.font.Font(ImageTest.OTHER_DIR / 'VL-Gothic-Regular.ttf', 12)


def save_png(path, size=(10, 10), color=(255, 0, 0)):
    surface = pygame.Surface(size)
    surface.fill(color)
    pygame.image.save(surface, path)
    return path
