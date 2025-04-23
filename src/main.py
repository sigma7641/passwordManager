#!/usr/bin/env python
# coding: utf-8

"""
パスワード管理アプリケーション

GUIを備えるパスワード管理アプリ
パスワードはJSONファイルに記録される
パスワードを記録したJSONファイルは暗号化し、マスターパスワードを利用して復号化する
マスターパスワードはSHA256でハッシュ化して保存する
パスワードの照会はマスターパスワードを利用する

機能：
- GUIでパスワードの登録、更新、削除、検索ができる
- GUIでパスワードの登録、更新ではtitleとmemo、title、メモ、
  カスタム属性（任意の項目、属性名もカスタム可能）を登録できる。
- GUIで起動時にマスターパスワードを入力する
- GUIでサイドペインを利用して登録されているパスワードのtitleを一覧表示する
- サイドペインのパスワードのtitleをクリックすると、メインペインに詳細情報が表示される
"""

import os
import sys

# srcディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nest_asyncio  # noqa: E402

from src.gui.app import GUIApp  # noqa: E402

# 非同期のイベントループを許可
nest_asyncio.apply()

if __name__ == "__main__":
    app = GUIApp()
    app.run()
