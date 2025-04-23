# パスワードマネージャー

シンプルで安全なパスワード管理ツール。

## 機能

- パスワードの安全な暗号化保存
- パスワードの追加、閲覧、更新、削除
- AES暗号化方式を使用したセキュアな保存

## TODO

- OTP対応

## セットアップ

1. リポジトリをクローン:

```bash
git clone https://github.com/[your-username]/passwordManager.git
cd passwordManager
```

2. 仮想環境を作成して有効化:

```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# または
.\venv\Scripts\activate  # Windows
```

3. 必要なパッケージをインストール:

```bash
pip install -r requirements.txt
```

## 使い方

1. 起動

```bash
source venv/bin.activate
#または
.\venv\Scripts\activate

python src/main.py
```

2. マスターパスワード入力

初回に入力したパスワードがAESのキーとなり、今後の復号時にも利用されます。

![マスターパスワード入力](images/master_password.png)

3. パスワード追加

`+`アイコンをクリックすることでパスワード情報を追加できます。
![パスワード入力](images/add_password.png)
![パスワード入力フォーム](images/add_password_form.png)

4. パスワード利用

サイドペインでtitleをクリックすると入力したパスワード情報を利用できます。

![パスワード参照](images/password_info.png)

## セキュリティ

- AES暗号化を使用してパスワードを保護
- パスワードはローカルに暗号化された状態で保存

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。
