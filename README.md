ImageTest
===

imageフォルダ内の画像を全部表示する。
画像を選択し、配置し、その座標を見て、そのデータをテキスト出力できる。
以上の操作はマウスですべて出来るし、キーボードでもすべて出来る。

- Docker: 対応!
- Python: 3.15!
- Linter: Ruff!
- Test: pytest!
- pygame-ce: 2.5!

## パッと実行してみたい

```bash
docker compose up --build
```

ブラウザで http://localhost:6080/vnc.html?autoconnect=1 を開くと、下の画面がブラウザの中に出てくる。

- F1 (または S) を押すと `output/imagetestText.txt` に全画像の座標が出力される。次に起動したときは、その配置から始まる。
- `image/` フォルダに自分の画像を入れて F5 を押す (か起動しなおす) と、その画像を配置できる。
- ESC で終了すると、コンテナも止まる。
- 画面の大きさは 640x480。作っているゲームに合わせたいときは `IMAGETEST_SIZE=800x600 docker compose up` みたいに指定する。
- コンテナの中はユーザー ID 1000 で動く。Linux で `output/` に書き込めないと言われたら `chmod a+w output` する。

![1](media/IMAGETEST.jpg)

(昔の Windows 版の画面。今はこれがブラウザの中に出て、選択中の画像は枠で囲まれる。)

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
        Upper right: image name, position, size and mouse position
        B: Change background (black, gray, white, checker)
        H: Hide / show the upper right info

    Others
        F1, S, Mouse Click 2: Output data as text file (imagetestText.txt, UTF-8)
        F5: Reload the image folder (positions are kept)
        ESC, Alt+F4: Quit

テキストはこんな感じで、1 行に 1 画像の名前と座標 `[x, y]` が、奥にある画像から順に並ぶ。
Docker なら `output/`、Docker を使わないときは起動したフォルダに書かれる。
書き込めなかったときは、右上にその理由が出る。
次に起動したときにこのファイルがあると、その位置と重なり順を読み込んで続きから始まる。

    lecturer.png [0, 0]
    pupil.png [0, 0]
    skype.png [0, 0]
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
