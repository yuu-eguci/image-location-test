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

- F1 を押すと `output/imagetestText.txt` に全画像の座標が出力される。
- `image/` フォルダに自分の画像を入れて起動しなおすと、その画像を配置できる。
- ESC で終了すると、コンテナも止まる。

![1](media/IMAGETEST.jpg)

## Usage

    Select Image Mode
        Mouse
            Mouse wheel: Choose images
            Left Click: To Place Image Mode
        Keyboard
            Up, Down: Choose images
            Z: To Place Image Mode

    Place Image Mode
        Mouse
            Left Click, Left Drag: Move image
            Right Click: To Select Image Mode
        Keyboard
            Cursor keys: Move image
            X: To Select Image Mode

    Others
        F1, Mouse Click 2: Output data as text file (imagetestText.txt, UTF-8)
        ESC, Alt+F4: Quit

テキストはこんな感じで、1 行に 1 画像の名前と座標 `[x, y]` が並ぶ。

    dialogbox.png [0, 330]
    skype.png [0, 0]

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
