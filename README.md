ImageTest
===

`image/` フォルダ内の画像を全部表示する。
画像を選択し、配置し、その座標を見て、そのデータをテキスト出力できる。
画像の選択・配置・座標出力は、マウスでもキーボードでもできる。

- Docker: 対応!
- Python: 3.15! (3.14 でも動く)
- Linter: Ruff!
- Test: pytest!
- pygame-ce: 2.5!

## パッと実行してみたい

```bash
docker compose up --build
```

ブラウザで `http://localhost:6080/vnc.html?autoconnect=1` を開く。
画像を選んで置くと、右上で座標を確認できる。
F1 または S で、全画像の座標が `output/imagetestText.txt` に出る。
次に起動すると、保存した配置から始まる。

- `image/` フォルダに自分の画像を入れて F5 を押す (か起動しなおす) と、その画像を配置できる。
- ESC で終了すると、コンテナも止まる。保存していない変更があるときは、もう一度 ESC を押すと終了する。
- F2 で操作方法が出る。
- 画面の大きさは 640x480。作っているゲームに合わせたいときは `IMAGETEST_SIZE=800x600 docker compose up` みたいに指定する。
- コンテナはユーザー ID 1000 で動く。Linux で保存に失敗するときは、`output/` の書き込み権限を確認する。

![1](media/IMAGETEST.jpg)

昔の Windows 版の画面。
今はブラウザの中に表示され、選択中の画像が枠で囲まれる。

## Usage

    Select Image Mode
        Mouse
            Mouse wheel: Choose images (up = previous, down = next)
            Left Click: To Place Image Mode
        Keyboard
            Up, Down: Choose images
            Z: To Place Image Mode

    Place Image Mode
        Mouse
            Left Click, Left Drag: Move image
            Right Click: To Select Image Mode
        Keyboard
            Cursor keys: Move image (1px, with Shift: 10px)
            X: To Select Image Mode

    Screen
        Selected image: framed (yellow: Select Image Mode, red: Place Image Mode)
        Upper right: image name, position, size, bottom-right (position + size)
                     and mouse position (also from the image's top-left)
        First start (no saved text file): larger images are put behind smaller ones
        B: Change background (black, gray, white, checker)
        H: Hide / show the upper right info and the frame
        F2: Show / hide help
        "*未保存" after the image name: moved but not saved yet

    Others
        F1, S, Mouse Click 2: Output data as text file (imagetestText.txt, UTF-8)
        F5: Reload the image folder (positions are kept)
        ESC, Alt+F4: Quit (press twice if not saved)

テキストはこんな感じで、1 行に 1 画像の名前と座標 `[x, y]` が、奥にある画像から順に並ぶ。
Docker なら `output/`、Docker を使わないときは起動したフォルダに書かれる。
書き込めなかったときは、右上にその理由が出る。
次に起動したときにこのファイルがあると、その位置と重なり順を読み込んで続きから始まる。

    skype.png [0, 0]
    lecturer.png [0, 0]
    pupil.png [0, 0]
    dialogbox.png [0, 330]

## 開発

```bash
# lint と test
docker compose run --rm --build dev

# Docker を使わない場合 (uv が必要)
uv sync
uv run ruff check
uv run ruff format --check
uv run pytest
uv run python ImageTest.py
```
