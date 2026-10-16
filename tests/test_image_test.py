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
    return ImageTest.ImageTest(
        screen, font, images, output_path=tmp_path / 'out.txt', image_dir=image_dir
    )


def names(app):
    return [image.name for image in app.images]


# 画像の読み込み


def test_create_image_list_loads_only_images_in_name_order(image_dir):
    images = ImageTest.create_image_list(image_dir)
    assert [image.name for image in images] == ['a.png', 'b.png']
    assert all(image.xy == [0, 0] for image in images)


def test_create_image_list_skips_files_that_cannot_be_opened(image_dir, monkeypatch):
    load = pygame.image.load

    def fake_load(path):
        if path.name == 'b.png':
            raise FileNotFoundError(path)
        return load(path)

    monkeypatch.setattr(pygame.image, 'load', fake_load)
    assert [image.name for image in ImageTest.create_image_list(image_dir)] == ['a.png']


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


def move_mouse(app, pos):
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, buttons=(0, 0, 0)))


def test_tab_chooses_images_under_mouse_from_front_to_back(app):
    app.images[0].xy = [5, 5]  # a.png (奥) は (5, 5)-(15, 15), b.png (手前) は (0, 0)-(10, 10)
    move_mouse(app, (7, 7))
    app.handle_event(key(pygame.K_TAB))
    assert app.images[app.num].name == 'b.png'
    app.handle_event(key(pygame.K_TAB))
    assert app.images[app.num].name == 'a.png'
    app.handle_event(key(pygame.K_TAB))
    assert app.images[app.num].name == 'b.png'
    move_mouse(app, (12, 12))
    app.handle_event(key(pygame.K_TAB))
    assert app.images[app.num].name == 'a.png'
    assert app.mode == 'select'
    assert names(app) == ['a.png', 'b.png']


def test_tab_does_nothing_without_image_under_mouse(app):
    app.handle_event(key(pygame.K_DOWN))
    move_mouse(app, (300, 300))
    app.handle_event(key(pygame.K_TAB))
    assert app.num == 1


def test_z_brings_selected_image_to_front_and_enters_place_mode(app):
    app.handle_event(key(pygame.K_z))
    assert names(app) == ['b.png', 'a.png']
    assert app.num == 1
    assert app.mode == 'place'


def test_shift_z_sends_selected_image_to_the_back(app):
    app.handle_event(key(pygame.K_DOWN))
    app.handle_event(key(pygame.K_z, mod=pygame.KMOD_LSHIFT))
    assert names(app) == ['b.png', 'a.png']
    assert app.images[app.num].name == 'b.png'
    assert app.mode == 'select'
    app.handle_event(key(pygame.K_u))
    assert names(app) == ['a.png', 'b.png']


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


def test_shift_cursor_keys_move_image_by_ten_pixels(placing):
    image = placing.images[placing.num]
    image.xy = [10, 5]
    placing.handle_event(key(pygame.K_RIGHT, mod=pygame.KMOD_LSHIFT))
    placing.handle_event(key(pygame.K_DOWN, mod=pygame.KMOD_RSHIFT))
    assert image.xy == [20, 15]
    placing.handle_event(key(pygame.K_UP, mod=pygame.KMOD_LSHIFT))
    placing.handle_event(key(pygame.K_UP, mod=pygame.KMOD_LSHIFT))
    assert image.xy == [20, 0]
    image.xy = [WIDTH - 5, 0]
    placing.handle_event(key(pygame.K_RIGHT, mod=pygame.KMOD_LSHIFT))
    assert image.xy == [WIDTH - 1, 0]


@pytest.mark.parametrize(
    ('start', 'k', 'end'),
    [
        ([700, 500], pygame.K_DOWN, [700, 500]),
        ([700, 500], pygame.K_RIGHT, [700, 500]),
        ([700, 500], pygame.K_UP, [700, 499]),
        ([700, 500], pygame.K_LEFT, [699, 500]),
        ([-20, -30], pygame.K_UP, [-20, -30]),
        ([-20, -30], pygame.K_LEFT, [-20, -30]),
        ([-20, -30], pygame.K_DOWN, [-20, -29]),
        ([-20, -30], pygame.K_RIGHT, [-19, -30]),
    ],
)
def test_cursor_keys_do_not_pull_off_screen_image_to_the_edge(placing, start, k, end):
    image = placing.images[placing.num]
    image.xy = start
    placing.handle_event(key(k))
    assert image.xy == end


@pytest.mark.parametrize(
    ('k', 'end'),
    [
        (pygame.K_HOME, [0, 20]),
        (pygame.K_END, [WIDTH - 10, 20]),
        (pygame.K_PAGEUP, [30, 0]),
        (pygame.K_PAGEDOWN, [30, HEIGHT - 10]),
    ],
)
def test_home_end_pageup_pagedown_put_image_on_screen_edge(placing, k, end):
    image = placing.images[placing.num]
    image.xy = [30, 20]
    placing.handle_event(key(k))
    assert image.xy == end


def test_edge_keys_do_nothing_in_select_mode(app):
    app.images[0].xy = [30, 20]
    app.handle_event(key(pygame.K_END))
    assert app.images[0].xy == [30, 20]


@pytest.mark.parametrize('event', [key(pygame.K_x), click(3)])
def test_x_or_right_click_returns_to_select_mode(placing, event):
    placing.handle_event(event)
    assert placing.mode == 'select'


# テキスト出力


@pytest.mark.parametrize('event', [key(pygame.K_F1), key(pygame.K_s), click(2)])
def test_f1_or_middle_click_writes_positions_as_text(placing, event, tmp_path):
    placing.handle_event(click(1, pos=(5, 6)))
    placing.handle_event(event)
    text = (tmp_path / 'out.txt').read_text(encoding='utf-8')
    assert text == 'b.png [0, 0]\na.png [5, 6]\n'
    assert placing.notice


def test_click_closing_notice_does_not_drag_image(placing):
    image = placing.images[placing.num]
    drag = pygame.event.Event(pygame.MOUSEMOTION, pos=(300, 300), buttons=(1, 0, 0))
    placing.handle_event(key(pygame.K_F1))
    placing.handle_event(click(1, pos=(299, 299)))
    placing.handle_event(drag)
    assert image.xy == [0, 0]
    placing.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(300, 300)))
    placing.handle_event(drag)
    assert image.xy == [300, 300]


def test_mouse_motion_keeps_notice(placing):
    placing.handle_event(key(pygame.K_F1))
    placing.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(5, 5), buttons=(0, 0, 0)))
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


# 元に戻す


def test_u_undoes_moves_one_by_one(placing):
    image = placing.images[placing.num]
    placing.handle_event(click(1, pos=(10, 10)))
    placing.handle_event(click(1, pos=(50, 60)))
    placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [50, 60]
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [10, 10]
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]


def test_u_undoes_a_whole_drag_at_once(placing):
    image = placing.images[placing.num]
    placing.handle_event(click(1, pos=(5, 5)))
    for pos in [(20, 20), (30, 30)]:
        placing.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, buttons=(1, 0, 0)))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]


def release(pos=(0, 0)):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)


def drag(app, start, end):
    app.handle_event(click(1, pos=start))
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=end, buttons=(1, 0, 0)))
    app.handle_event(release(end))


def test_u_undoes_drag_of_front_image_started_in_select_mode(app):
    app.handle_event(key(pygame.K_DOWN))  # b.png はもう一番手前なので、クリックで並びは変わらない
    drag(app, (5, 5), (100, 100))
    assert app.images[app.num].xy == [100, 100]
    app.handle_event(key(pygame.K_u))
    assert app.images[app.num].xy == [0, 0]


def test_u_undoes_drag_started_on_top_left_and_previous_move_separately(placing):
    image = placing.images[placing.num]
    drag(placing, (50, 50), (50, 50))
    drag(placing, (50, 50), (200, 200))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [50, 50]
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]


def test_click_without_change_is_not_an_undo_step(placing):
    image = placing.images[placing.num]
    drag(placing, (30, 30), (30, 30))
    drag(placing, (30, 30), (30, 30))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]
    assert names(placing) == ['b.png', 'a.png']


def test_u_during_drag_cancels_the_drag(placing):
    image = placing.images[placing.num]
    placing.handle_event(click(1, pos=(10, 10)))
    placing.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(20, 20), buttons=(1, 0, 0)))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]
    placing.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(41, 41), buttons=(1, 0, 0)))
    placing.handle_event(release((41, 41)))
    assert image.xy == [0, 0]
    placing.handle_event(key(pygame.K_u))
    assert names(placing) == ['a.png', 'b.png']


def test_same_key_in_a_row_is_one_undo_step(placing):
    image = placing.images[placing.num]
    image.xy = [10, 10]
    for _ in range(3):
        placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_DOWN))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [13, 10]
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [10, 10]


def test_reload_is_not_an_undo_step(app, image_dir):
    app.handle_event(key(pygame.K_z))
    save_png(image_dir / 'c.png')
    app.handle_event(key(pygame.K_F5))
    app.handle_event(key(pygame.K_u))
    assert names(app) == ['a.png', 'b.png', 'c.png']


def test_same_key_after_undo_is_a_new_step(placing):
    image = placing.images[placing.num]
    placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_u))
    placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]
    assert names(placing) == ['b.png', 'a.png']


@pytest.mark.parametrize('mod', [pygame.KMOD_LCTRL, pygame.KMOD_RCTRL, pygame.KMOD_LGUI])
def test_ctrl_or_cmd_z_undoes_without_reordering(app, mod):
    app.handle_event(key(pygame.K_z))
    app.handle_event(key(pygame.K_x))
    app.handle_event(key(pygame.K_z, mod=mod))
    assert names(app) == ['a.png', 'b.png']
    assert app.mode == 'select'
    app.handle_event(key(pygame.K_z, mod=mod | pygame.KMOD_LSHIFT))
    assert names(app) == ['a.png', 'b.png']


def test_u_without_history_does_nothing(app):
    app.handle_event(key(pygame.K_u))
    assert [(image.name, image.xy) for image in app.images] == [
        ('a.png', [0, 0]),
        ('b.png', [0, 0]),
    ]


def test_key_move_while_button_is_held_joins_the_click_step(placing):
    image = placing.images[placing.num]
    placing.handle_event(click(1, pos=(0, 0)))  # 位置は変わらないクリック (ボタンはまだ押したまま)
    placing.handle_event(key(pygame.K_RIGHT))
    placing.handle_event(key(pygame.K_u))
    assert image.xy == [0, 0]
    placing.handle_event(key(pygame.K_u))
    assert names(placing) == ['a.png', 'b.png']


def test_undo_history_is_limited(placing):
    for x in range(ImageTest.HISTORY_LIMIT + 10):
        placing.handle_event(click(1, pos=(x + 1, 0)))
        placing.handle_event(release())
    assert len(placing.history) == ImageTest.HISTORY_LIMIT


def test_u_undoes_reorder_and_keeps_selection(app):
    app.handle_event(key(pygame.K_z))
    assert names(app) == ['b.png', 'a.png']
    app.handle_event(key(pygame.K_u))
    assert names(app) == ['a.png', 'b.png']
    assert app.images[app.num].name == 'a.png'
    assert not app.dirty


def test_u_while_notice_only_closes_notice(placing):
    placing.handle_event(click(1, pos=(10, 10)))
    placing.handle_event(key(pygame.K_F1))
    placing.handle_event(key(pygame.K_u))
    assert placing.notice is None
    assert placing.images[placing.num].xy == [10, 10]


# 画像フォルダの読みなおし


def test_f5_reloads_images_keeping_positions_order_and_selection(app, image_dir):
    app.handle_event(key(pygame.K_DOWN))
    app.handle_event(key(pygame.K_z))
    app.handle_event(click(1, pos=(5, 6)))
    save_png(image_dir / 'c.png')
    (image_dir / 'a.png').unlink()
    app.handle_event(key(pygame.K_F5))
    assert [(image.name, image.xy) for image in app.images] == [
        ('b.png', [5, 6]),
        ('c.png', [0, 0]),
    ]
    assert app.images[app.num].name == 'b.png'
    assert app.mode == 'place'


def test_f5_selects_first_image_when_selected_one_is_gone(app, image_dir):
    app.handle_event(key(pygame.K_DOWN))
    (image_dir / 'b.png').unlink()
    app.handle_event(key(pygame.K_F5))
    assert names(app) == ['a.png']
    assert app.num == 0


def test_f5_keeps_images_when_folder_became_empty(app, image_dir):
    for path in image_dir.glob('*.png'):
        path.unlink()
    app.handle_event(key(pygame.K_F5))
    assert names(app) == ['a.png', 'b.png']
    assert app.info_text()[0] == f'● {image_dir} に画像がありません ●'


def test_f5_returns_to_select_mode_when_placed_image_is_gone(app, image_dir):
    app.handle_event(key(pygame.K_z))
    (image_dir / 'a.png').unlink()
    app.handle_event(key(pygame.K_F5))
    assert names(app) == ['b.png']
    assert app.mode == 'select'


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
        app.handle_event(key(pygame.K_s))
        app.handle_event(key(pygame.K_SPACE))
    app.handle_event(event)
    assert not app.running


@pytest.mark.parametrize(
    'change',
    [
        [key(pygame.K_z)],
        [key(pygame.K_z), key(pygame.K_x), key(pygame.K_DOWN), click(1), click(1, (3, 4))],
    ],
)
def test_changes_are_marked_unsaved(app, change):
    assert not app.dirty
    for event in change:
        app.handle_event(event)
    assert app.dirty
    assert app.info_text()[1].endswith('  *未保存')
    app.handle_event(key(pygame.K_s))
    assert not app.dirty


def test_moving_back_to_saved_layout_is_not_a_change(app):
    app.handle_event(key(pygame.K_z))
    app.handle_event(key(pygame.K_x))
    app.handle_event(key(pygame.K_DOWN))
    app.handle_event(click(1))
    assert names(app) == ['a.png', 'b.png']
    assert not app.dirty


def test_reload_and_selection_are_not_changes(app):
    app.handle_event(key(pygame.K_DOWN))
    app.handle_event(click(5))
    app.handle_event(key(pygame.K_F5))
    assert not app.dirty


@pytest.mark.parametrize('quit_key', [key(pygame.K_ESCAPE), key(pygame.K_F4, mod=pygame.KMOD_LALT)])
def test_quit_with_unsaved_changes_needs_second_press(app, quit_key):
    app.handle_event(key(pygame.K_z))
    app.handle_event(quit_key)
    assert app.running
    assert app.info_text()[0].startswith('● 保存していません')
    app.handle_event(quit_key)
    assert not app.running


def test_unsaved_warning_is_closed_by_other_keys_and_shown_again(app):
    app.handle_event(key(pygame.K_z))
    app.handle_event(key(pygame.K_ESCAPE))
    app.handle_event(key(pygame.K_SPACE))
    assert app.notice is None
    app.handle_event(key(pygame.K_ESCAPE))
    assert app.running
    app.handle_event(key(pygame.K_ESCAPE))
    assert not app.running


def test_window_close_quits_even_with_unsaved_changes(app):
    app.handle_event(key(pygame.K_z))
    app.handle_event(pygame.event.Event(pygame.QUIT))
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


@pytest.mark.parametrize('mode_key', [None, pygame.K_z])
def test_b_cycles_background(app, screen, mode_key):
    if mode_key:
        app.handle_event(key(mode_key))
    colors = []
    for _ in range(5):
        app.draw()
        colors.append((screen.get_at((200, 200))[:3], screen.get_at((216, 200))[:3]))
        app.handle_event(key(pygame.K_b))
    black, gray, white = (0, 0, 0), (128, 128, 128), (255, 255, 255)
    assert colors[:3] == [(black, black), (gray, gray), (white, white)]
    checker_a, checker_b = colors[3]
    assert checker_a != checker_b
    assert {checker_a, checker_b}.isdisjoint({black, white})
    assert colors[4] == (black, black)


def test_g_cycles_grid(app, screen):
    def lines():
        app.draw()
        return [
            x for x in (8, 9, 16, 32, 40) if screen.get_at((x, 201))[:3] == ImageTest.GRID_COLOR
        ]

    assert lines() == []
    app.handle_event(key(pygame.K_g))
    assert lines() == [8, 16, 32, 40]
    app.handle_event(key(pygame.K_g))
    assert lines() == [16, 32]
    app.handle_event(key(pygame.K_g))
    assert lines() == [32]
    app.handle_event(key(pygame.K_g))
    assert lines() == []


def loupe_cell(app, screen, dx, dy):
    """拡大表示で、マウスから (dx, dy) ずれたピクセルのマスの真ん中の色。"""
    size, scale = ImageTest.LOUPE_SIZE, ImageTest.LOUPE_SCALE
    top = HEIGHT - 5 - size * scale
    center = size // 2
    return screen.get_at(
        (5 + (center + dx) * scale + scale // 2, top + (center + dy) * scale + scale // 2)
    )[:3]


def test_m_shows_magnified_pixels_around_mouse(app, screen):
    app.images[1].xy = [20, 20]  # b.png (青) は (20, 20)-(30, 30)
    move_mouse(app, (19, 25))
    app.draw()
    assert loupe_cell(app, screen, 1, 0) != (0, 0, 255)
    app.handle_event(key(pygame.K_m))
    app.draw()
    assert loupe_cell(app, screen, 0, 0) == (0, 0, 0)
    assert loupe_cell(app, screen, 1, 0) == (0, 0, 255)
    assert loupe_cell(app, screen, 7, 0) == (0, 0, 255)
    app.handle_event(key(pygame.K_m))
    app.draw()
    assert loupe_cell(app, screen, 1, 0) != (0, 0, 255)


def test_magnifier_shows_black_outside_screen(app, screen):
    app.handle_event(key(pygame.K_b))
    app.handle_event(key(pygame.K_b))  # 背景を白にして、画面の外 (黒) と区別する
    move_mouse(app, (0, 14))  # 画像は (0, 0)-(10, 10)。手前は b.png (青)
    app.handle_event(key(pygame.K_m))
    app.draw()
    assert loupe_cell(app, screen, 0, 0) == (255, 255, 255)
    assert loupe_cell(app, screen, 0, -5) == (0, 0, 255)
    assert loupe_cell(app, screen, -1, 0) == (0, 0, 0)
    assert loupe_cell(app, screen, -1, -5) == (0, 0, 0)


def test_magnifier_is_drawn_over_the_frame(app, screen):
    app.images[0].xy = [20, HEIGHT - 70]  # 選択中の a.png の枠が拡大表示の場所を通る
    move_mouse(app, (300, 100))
    app.draw()
    assert screen.get_at((19, HEIGHT - 65))[:3] == ImageTest.FRAME_COLORS['select']
    app.handle_event(key(pygame.K_m))
    app.draw()
    assert screen.get_at((19, HEIGHT - 65))[:3] == (0, 0, 0)


def test_magnifier_moves_right_while_mouse_is_over_it(app, screen):
    app.handle_event(key(pygame.K_m))
    border_left, border_right = (5, HEIGHT - 60), (WIDTH - 6, HEIGHT - 60)
    move_mouse(app, (300, 100))
    app.draw()
    assert screen.get_at(border_left)[:3] == (255, 255, 255)
    assert screen.get_at(border_right)[:3] != (255, 255, 255)
    move_mouse(app, (20, HEIGHT - 20))
    app.draw()
    assert screen.get_at(border_left)[:3] != (255, 255, 255)
    assert screen.get_at(border_right)[:3] == (255, 255, 255)


@pytest.mark.parametrize('show', [[], [pygame.K_F2], [pygame.K_z]])
def test_info_box_fits_small_screen(image_dir, tmp_path, font, show):
    small = pygame.display.set_mode((320, 240))
    images = ImageTest.create_image_list(image_dir)
    app = ImageTest.ImageTest(small, font, images, output_path=tmp_path / 'out.txt')
    for k in show:
        app.handle_event(key(k))
    lines = app.wrap(app.info_text())
    assert all(font.size(line)[0] <= 320 - 20 for line in lines)
    assert ' '.join(lines).split() == ' '.join(app.info_text()).split()
    app.draw()
    box_left = 320 - (max(font.size(line)[0] for line in lines) + 10) - 5
    assert box_left >= 0
    assert small.get_at((box_left + 1, 6))[:3] == (255, 255, 255)


def test_wrap_keeps_lines_that_fit(app):
    assert app.wrap(['abc', 'de f']) == ['abc', 'de f']


def test_h_hides_info_but_not_notice(app, screen):
    corner = (WIDTH - 6, 6)
    app.handle_event(key(pygame.K_h))
    app.draw()
    assert screen.get_at(corner)[:3] == (0, 0, 0)
    app.handle_event(key(pygame.K_F1))
    app.draw()
    assert screen.get_at(corner)[:3] == (255, 255, 255)
    app.handle_event(key(pygame.K_SPACE))
    app.handle_event(key(pygame.K_h))
    app.draw()
    assert screen.get_at(corner)[:3] == (255, 255, 255)


def test_info_text_follows_mode(app):
    assert app.info_text()[0].startswith('<選択モード>')
    assert app.info_text()[1:] == [
        '▼ a.png',
        '  位置: [0, 0]  大きさ: 10x10  右下: (10, 10)',
        '  ﾏｳｽ: (0, 0)  画像内: (0, 0)',
    ]
    app.handle_event(key(pygame.K_z))
    assert app.info_text()[0].startswith('<配置ﾓｰﾄﾞ>')
    assert app.info_text()[2] == '▼ 位置: [0, 0]  大きさ: 10x10  右下: (10, 10)'
    app.handle_event(click(1, pos=(30, 40)))
    assert app.info_text()[2] == '▼ 位置: [30, 40]  大きさ: 10x10  右下: (40, 50)'
    app.handle_event(key(pygame.K_F1))
    assert app.info_text()[0] == '● データをテキスト出力しました ●'


def test_f2_toggles_help_with_all_keys(app):
    app.handle_event(key(pygame.K_F2))
    help_text = '\n'.join(app.info_text())
    assert app.info_text()[0].startswith('<ﾍﾙﾌﾟ>')
    for word in [
        'Tab',
        'Z',
        'Shift+Z',
        'X',
        'Shift',
        'Home',
        'PageDown',
        'F1',
        'S',
        'F5',
        'U',
        'Ctrl+Z',
        'B',
        'G',
        'M',
        'H',
        'ESC',
    ]:
        assert word in help_text
    app.handle_event(key(pygame.K_F2))
    assert app.info_text()[0].startswith('<選択モード>')


def test_help_is_shown_even_when_info_is_hidden(app, screen):
    app.handle_event(key(pygame.K_h))
    app.handle_event(key(pygame.K_F2))
    app.draw()
    assert screen.get_at((WIDTH - 6, 6))[:3] == (255, 255, 255)


def test_info_text_shows_mouse_position(app):
    app.images[0].xy = [10, 10]
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(15, 17), buttons=(0, 0, 0)))
    assert app.info_text()[3] == '  ﾏｳｽ: (15, 17)  画像内: (5, 7)'


def test_selected_image_is_framed_by_mode_color(app, screen):
    app.images[0].xy = [20, 20]
    app.draw()
    assert screen.get_at((30, 25))[:3] == ImageTest.FRAME_COLORS['select']
    assert screen.get_at((25, 25))[:3] == (255, 0, 0)
    assert screen.get_at((31, 25))[:3] == (0, 0, 0)
    app.handle_event(key(pygame.K_z))
    app.draw()
    assert screen.get_at((19, 25))[:3] == ImageTest.FRAME_COLORS['place']
    app.handle_event(key(pygame.K_h))
    app.draw()
    assert screen.get_at((19, 25))[:3] == (0, 0, 0)


# 前回の配置の読み込み


def test_restore_positions_applies_saved_positions_and_order(image_dir, tmp_path):
    saved = tmp_path / 'saved.txt'
    saved.write_text(
        'b.png [5, 6]\nbroken line\nmissing.png [1, 2]\nmy a.png [9, 9]\na.png [7, -8]\n',
        encoding='utf-8',
    )
    images = ImageTest.restore_positions(ImageTest.create_image_list(image_dir), saved)
    assert [(image.name, image.xy) for image in images] == [('b.png', [5, 6]), ('a.png', [7, -8])]


def test_restore_positions_reads_file_with_bom(image_dir, tmp_path):
    saved = tmp_path / 'saved.txt'
    saved.write_text('b.png [5, 6]\n', encoding='utf-8-sig')
    images = ImageTest.restore_positions(ImageTest.create_image_list(image_dir), saved)
    assert (images[0].name, images[0].xy) == ('b.png', [5, 6])


def test_restore_positions_puts_unsaved_images_in_front(image_dir, tmp_path):
    saved = tmp_path / 'saved.txt'
    saved.write_text('b.png [5, 6]\n', encoding='utf-8')
    images = ImageTest.restore_positions(ImageTest.create_image_list(image_dir), saved)
    assert [(image.name, image.xy) for image in images] == [('b.png', [5, 6]), ('a.png', [0, 0])]


@pytest.mark.parametrize('content', [None, '画像.png [1, 2]'.encode('shift_jis')])
def test_restore_positions_ignores_missing_or_unreadable_file(image_dir, tmp_path, content):
    saved = tmp_path / 'saved.txt'
    if content is not None:
        saved.write_bytes(content)
    images = ImageTest.restore_positions(ImageTest.create_image_list(image_dir), saved)
    assert [(image.name, image.xy) for image in images] == [('a.png', [0, 0]), ('b.png', [0, 0])]


def test_saved_text_round_trips(app, tmp_path):
    app.images[0].xy = [3, 4]
    app.handle_event(key(pygame.K_z))
    app.handle_event(key(pygame.K_F1))
    images = ImageTest.restore_positions(
        ImageTest.create_image_list(tmp_path / 'image'), app.output_path
    )
    assert [(image.name, image.xy) for image in images] == [('b.png', [0, 0]), ('a.png', [3, 4])]


# 起動


def test_main_restores_layout_from_current_folder(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(
        ImageTest.ImageTest,
        'run',
        lambda self: seen.update(images=self.images, path=self.output_path),
    )
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'imagetestText.txt').write_text('pupil.png [1, 2]\n', encoding='utf-8')
    ImageTest.main()
    assert [(image.name, image.xy) for image in seen['images']] == [
        ('pupil.png', [1, 2]),
        ('skype.png', [0, 0]),
        ('dialogbox.png', [0, 0]),
        ('lecturer.png', [0, 0]),
    ]
    assert seen['path'] == ImageTest.OUTPUT_FILE


def test_main_sets_up_window_and_runs(monkeypatch, tmp_path):
    seen = {}

    def fake_run(self):
        seen['caption'] = pygame.display.get_caption()[0]
        seen['size'] = self.screen.get_size()
        seen['images'] = [image.name for image in self.images]
        seen['image_dir'] = self.image_dir
        seen['repeat'] = pygame.key.get_repeat()

    monkeypatch.setattr(ImageTest.ImageTest, 'run', fake_run)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('IMAGETEST_SIZE', raising=False)
    ImageTest.main()
    assert seen == {
        'caption': '画像配置テスト ESCキーで終了できます',
        'size': (WIDTH, HEIGHT),
        # 保存ファイルが無いときは大きい画像ほど奥 (同じ大きさなら名前順)
        'images': ['skype.png', 'dialogbox.png', 'lecturer.png', 'pupil.png'],
        'repeat': (500, 50),
        'image_dir': ImageTest.IMAGE_DIR,
    }


def test_main_uses_screen_size_from_environment(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(
        ImageTest.ImageTest, 'run', lambda self: seen.update(size=self.screen.get_size())
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('IMAGETEST_SIZE', '800x600')
    ImageTest.main()
    assert seen['size'] == (800, 600)


@pytest.mark.parametrize(('value', 'size'), [(None, (640, 480)), ('1024x768', (1024, 768))])
def test_screen_size(monkeypatch, value, size):
    if value is None:
        monkeypatch.delenv('IMAGETEST_SIZE', raising=False)
    else:
        monkeypatch.setenv('IMAGETEST_SIZE', value)
    assert ImageTest.screen_size() == size


@pytest.mark.parametrize('value', ['big', '800x', '0x600', '800x600x2', '-800x600'])
def test_screen_size_rejects_bad_value(monkeypatch, value):
    monkeypatch.setenv('IMAGETEST_SIZE', value)
    with pytest.raises(SystemExit, match='IMAGETEST_SIZE'):
        ImageTest.screen_size()


@pytest.mark.parametrize('folder', ['empty', 'missing'])
def test_main_exits_with_message_when_no_images(monkeypatch, tmp_path, folder):
    (tmp_path / 'empty').mkdir()
    monkeypatch.setattr(ImageTest, 'IMAGE_DIR', tmp_path / folder)
    with pytest.raises(SystemExit, match='画像がありません'):
        ImageTest.main()
