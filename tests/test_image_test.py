import pygame
import pytest
from conftest import save_png

import ImageTest

WIDTH, HEIGHT = ImageTest.SCREEN_SIZE


def key(k, mod=pygame.KMOD_NONE):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=mod)


def click(button, pos=(0, 0)):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button, pos=pos)


@pytest.fixture
def image_dir(tmp_path, screen):
    d = tmp_path / 'image'
    d.mkdir()
    save_png(d / 'b.png', color=(0, 0, 255))
    save_png(d / 'a.png', color=(255, 0, 0))
    (d / '.gitkeep').write_text('')
    (d / 'memo.txt').write_text('not an image')
    (d / 'sub').mkdir()
    return d


@pytest.fixture
def app(image_dir, screen, font, tmp_path):
    images = ImageTest.create_image_list(image_dir)
    return ImageTest.ImageTest(screen, font, images, output_path=tmp_path / 'out.txt')


def names(app):
    return [image.name for image in app.images]


# 画像の読み込み


def test_create_image_list_loads_only_images_in_name_order(image_dir):
    images = ImageTest.create_image_list(image_dir)
    assert [image.name for image in images] == ['a.png', 'b.png']
    assert all(image.xy == [0, 0] for image in images)


def test_create_image_list_is_empty_without_folder(tmp_path, screen):
    assert ImageTest.create_image_list(tmp_path / 'missing') == []


def test_create_image_list_reads_bundled_images(screen):
    images = ImageTest.create_image_list(ImageTest.IMAGE_DIR)
    assert [image.name for image in images] == [
        'dialogbox.png',
        'lecturer.png',
        'pupil.png',
        'skype.png',
    ]


# 画像選択モード


def test_starts_in_select_mode_with_first_image(app):
    assert app.mode == 'select'
    assert app.num == 0
    assert app.running


def test_up_down_keys_choose_image_and_wrap(app):
    app.handle_event(key(pygame.K_DOWN))
    assert app.num == 1
    app.handle_event(key(pygame.K_DOWN))
    assert app.num == 0
    app.handle_event(key(pygame.K_UP))
    assert app.num == 1


def test_mouse_wheel_chooses_image_like_up_down_keys(screen, font):
    app = ImageTest.ImageTest(screen, font, ImageTest.create_image_list(ImageTest.IMAGE_DIR))
    app.handle_event(click(5))
    assert app.num == 1
    app.handle_event(click(4))
    app.handle_event(click(4))
    assert app.num == 3


def test_z_brings_selected_image_to_front_and_enters_place_mode(app):
    app.handle_event(key(pygame.K_z))
    assert names(app) == ['b.png', 'a.png']
    assert app.num == 1
    assert app.mode == 'place'


def test_left_click_enters_place_mode_with_selected_image_in_front(app):
    app.handle_event(key(pygame.K_DOWN))
    app.handle_event(click(1))
    assert names(app) == ['a.png', 'b.png']
    assert app.images[app.num].name == 'b.png'
    assert app.mode == 'place'


# 画像配置モード


@pytest.fixture
def placing(app):
    app.handle_event(key(pygame.K_z))
    return app


def test_left_click_places_image_at_cursor(placing):
    placing.handle_event(click(1, pos=(100, 120)))
    assert placing.images[placing.num].xy == [100, 120]


def test_left_drag_moves_image(placing):
    motion = pygame.event.Event(pygame.MOUSEMOTION, pos=(30, 40), buttons=(1, 0, 0))
    placing.handle_event(motion)
    assert placing.images[placing.num].xy == [30, 40]


def test_mouse_motion_without_button_does_not_move_image(placing):
    motion = pygame.event.Event(pygame.MOUSEMOTION, pos=(30, 40), buttons=(0, 0, 0))
    placing.handle_event(motion)
    assert placing.images[placing.num].xy == [0, 0]


def test_cursor_keys_move_image_by_one_pixel(placing):
    image = placing.images[placing.num]
    image.xy = [10, 10]
    placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_DOWN))
    placing.handle_event(key(pygame.K_DOWN))
    assert image.xy == [11, 12]
    placing.handle_event(key(pygame.K_LEFT))
    placing.handle_event(key(pygame.K_UP))
    assert image.xy == [10, 11]


def test_cursor_keys_stop_at_screen_edges(placing):
    image = placing.images[placing.num]
    image.xy = [0, 0]
    placing.handle_event(key(pygame.K_LEFT))
    placing.handle_event(key(pygame.K_UP))
    assert image.xy == [0, 0]
    image.xy = [WIDTH - 1, HEIGHT - 1]
    placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_DOWN))
    assert image.xy == [WIDTH - 1, HEIGHT - 1]


@pytest.mark.parametrize('event', [key(pygame.K_x), click(3)])
def test_x_or_right_click_returns_to_select_mode(placing, event):
    placing.handle_event(event)
    assert placing.mode == 'select'


# テキスト出力


@pytest.mark.parametrize('event', [key(pygame.K_F1), click(2)])
def test_f1_or_middle_click_writes_positions_as_text(placing, event, tmp_path):
    placing.handle_event(click(1, pos=(5, 6)))
    placing.handle_event(event)
    text = (tmp_path / 'out.txt').read_text(encoding='utf-8')
    assert text == 'b.png [0, 0]\na.png [5, 6]\n'
    assert placing.notice


def test_text_output_is_utf8_for_any_file_name(tmp_path, screen, font):
    d = tmp_path / 'image'
    d.mkdir()
    save_png(d / '画像😀.png')
    images = ImageTest.create_image_list(d)
    app = ImageTest.ImageTest(screen, font, images, output_path=tmp_path / 'out.txt')
    app.handle_event(key(pygame.K_F1))
    assert (tmp_path / 'out.txt').read_text(encoding='utf-8') == '画像😀.png [0, 0]\n'


def test_text_output_error_is_shown_instead_of_crashing(app, tmp_path):
    app.output_path = tmp_path  # フォルダには書き込めない
    app.handle_event(key(pygame.K_F1))
    assert app.running
    assert app.info_text()[0].startswith('● テキスト出力できませんでした')


@pytest.mark.parametrize('event', [key(pygame.K_SPACE), key(pygame.K_ESCAPE), click(1)])
def test_any_key_or_click_closes_notice_and_keeps_mode(placing, event):
    placing.handle_event(key(pygame.K_F1))
    placing.handle_event(event)
    assert not placing.notice
    assert placing.mode == 'place'
    assert placing.running
    assert placing.images[placing.num].xy == [0, 0]


# 終了


@pytest.mark.parametrize(
    'event',
    [
        pygame.event.Event(pygame.QUIT),
        key(pygame.K_ESCAPE),
        key(pygame.K_F4, mod=pygame.KMOD_LALT),
    ],
)
@pytest.mark.parametrize('mode_key', [None, pygame.K_z])
def test_quit_events_stop_the_app(app, event, mode_key):
    if mode_key:
        app.handle_event(key(mode_key))
    app.handle_event(event)
    assert not app.running


def test_f4_without_alt_does_not_quit(app):
    app.handle_event(key(pygame.K_F4, mod=pygame.KMOD_NUM))
    assert app.running


def test_run_draws_after_handling_input(app, screen):
    pygame.event.post(key(pygame.K_DOWN))
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app.run()
    shown = screen.copy()
    app.draw()
    assert app.num == 1
    assert pygame.image.tobytes(shown, 'RGB') == pygame.image.tobytes(screen, 'RGB')


def test_run_returns_after_quit_event(app):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app.run()
    assert not app.running


# 描画


def test_draw_shows_images_and_info_box(app, screen):
    app.images[1].xy = [50, 50]
    app.draw()
    assert screen.get_at((0, 0))[:3] == (255, 0, 0)
    assert screen.get_at((55, 55))[:3] == (0, 0, 255)
    assert screen.get_at((200, 200))[:3] == (0, 0, 0)
    assert screen.get_at((WIDTH - 6, 6))[:3] == (255, 255, 255)


def test_info_text_follows_mode(app):
    assert app.info_text()[0].startswith('<選択モード>')
    assert app.info_text()[1] == '▼ a.png'
    app.handle_event(key(pygame.K_z))
    assert app.info_text()[0].startswith('<配置ﾓｰﾄﾞ>')
    assert app.info_text()[2] == '▼ 位置: [0, 0]'
    app.handle_event(key(pygame.K_F1))
    assert app.info_text()[0] == '● データをテキスト出力しました ●'


# 起動


def test_main_sets_up_window_and_runs(monkeypatch):
    seen = {}

    def fake_run(self):
        seen['caption'] = pygame.display.get_caption()[0]
        seen['size'] = self.screen.get_size()
        seen['images'] = [image.name for image in self.images]
        seen['repeat'] = pygame.key.get_repeat()

    monkeypatch.setattr(ImageTest.ImageTest, 'run', fake_run)
    ImageTest.main()
    assert seen == {
        'caption': '画像配置テスト ESCキーで終了できます',
        'size': (WIDTH, HEIGHT),
        'images': ['dialogbox.png', 'lecturer.png', 'pupil.png', 'skype.png'],
        'repeat': (500, 50),
    }


@pytest.mark.parametrize('folder', ['empty', 'missing'])
def test_main_exits_with_message_when_no_images(monkeypatch, tmp_path, folder):
    (tmp_path / 'empty').mkdir()
    monkeypatch.setattr(ImageTest, 'IMAGE_DIR', tmp_path / folder)
    with pytest.raises(SystemExit, match='画像がありません'):
        ImageTest.main()
