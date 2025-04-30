import asyncio
from datetime import datetime
from hashlib import sha256

from flet import (
    ButtonStyle,
    Colors,
    Column,
    Container,
    CrossAxisAlignment,
    DataCell,
    DataColumn,
    DataRow,
    DataTable,
    Divider,
    ElevatedButton,
    IconButton,
    Icons,
    ListTile,
    ListView,
    MainAxisAlignment,
    Padding,
    Page,
    ProgressRing,
    RoundedRectangleBorder,
    Row,
    Slider,
    Text,
    TextField,
    alignment,
    app,
    border,
)
from pyperclip import copy as pyperclip_copy

from src.core.password_manager import PasswordManager


class GUIApp:
    def __init__(self):
        self.password_manager = None
        self.page = None
        self.password_list = None
        self.detail_view = None
        self.selected_uid = None

    def run(self):
        app(target=self.main)

    def main(self, page: Page):
        self.page = page
        self.page.title = "Password Manager"
        self.page.window_width = 800
        self.page.window_height = 600
        # イベントループを設定
        self.page.on_event = lambda e: self.handle_page_event(e)
        self.show_master_password_screen()

    def handle_page_event(self, e):
        """ページイベントを処理します"""
        if hasattr(e, "data") and e.data == "timer_tick":
            self.page.update()

    def show_master_password_screen(self, error_message=None):
        self.page.clean()

        def on_master_password_submit(e):
            master_password = master_password_field.value
            try:
                self.password_manager = PasswordManager(master_password)
                # ローディング表示を追加
                loading = ProgressRing()
                loading_text = Text("パスワードを読み込んでいます...")
                self.page.clean()
                self.page.add(
                    Column(
                        [loading, loading_text],
                        alignment=MainAxisAlignment.CENTER,
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                    )
                )

                def on_load_complete(success, error):
                    if success:
                        self.show_main_screen()
                    else:
                        self.show_master_password_screen(
                            f"Failed to load passwords: {error}. Please try again."
                        )

                # 非同期でパスワードを読み込む
                self.password_manager.load_passwords(callback=on_load_complete)

            except ValueError as ex:
                self.show_master_password_screen(
                    f"Invalid Master Password: {str(ex)}. Please try again."
                )
            except Exception as ex:
                self.show_master_password_screen(
                    f"Unexpected error: {str(ex)}. Please try again."
                )

        master_password_field = TextField(
            label="Enter Master Password", password=True, width=300
        )

        master_password_button = ElevatedButton(
            text="Submit", on_click=on_master_password_submit
        )

        error_text = Text(error_message, color=Colors.RED) if error_message else None

        self.page.add(
            Column(
                [
                    error_text if error_text else Container(),
                    master_password_field,
                    master_password_button,
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            )
        )

    def show_main_screen(self):
        self.page.clean()

        # サイドペイン
        self.password_list = ListView(expand=1, spacing=10)
        self.update_password_list()

        # メインペイン
        self.detail_view = Column(expand=3, spacing=10)

        # 追加ボタン
        add_button = Container(
            content=IconButton(
                icon=Icons.ADD,
                icon_color=Colors.WHITE,
                bgcolor=Colors.GREEN,
                tooltip="Add Password",
                on_click=self.add_password,
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=8),
                    padding=Padding(8, 8, 8, 8),
                ),
            ),
            width=200,
            alignment=alignment.center,
            padding=Padding(10, 0, 10, 0),
        )

        # レイアウト
        self.page.add(
            Row(
                [
                    Container(
                        content=Column(
                            [
                                self.password_list,
                                Container(
                                    content=add_button,
                                    alignment=alignment.center,
                                    padding=Padding(10, 0, 0, 0),
                                ),
                            ],
                            expand=True,
                        ),
                        width=200,
                    ),
                    Container(content=self.detail_view, expand=3),
                ],
                expand=True,
            )
        )

    def update_password_list(self):
        self.password_list.controls.clear()
        for uid, info in self.password_manager.passwords.items():
            self.password_list.controls.append(
                ListTile(
                    title=Text(info["title"]),
                    on_click=lambda e, uid=uid: self.show_password_details(uid),
                )
            )
        self.page.update()

    def show_password_details(self, uid):
        self.selected_uid = uid
        self.detail_view.controls.clear()
        password_info = self.password_manager.get_password_info(uid)

        edit_button = IconButton(
            icon=Icons.EDIT,
            icon_color=Colors.BLUE,
            tooltip="Edit Password",
            on_click=lambda e: self.edit_password(uid),
        )

        delete_button = IconButton(
            icon=Icons.DELETE,
            icon_color=Colors.RED,
            tooltip="Delete Password",
            on_click=lambda e: self.delete_password(),
        )

        self.detail_view.controls.append(
            Row(
                [
                    Text("Password Details", weight="bold", size=20),
                    Row([edit_button, delete_button]),
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        table_rows = []
        for key, value in password_info.items():
            if "パスワード" in key or "password" in key:
                password_visible = False
                password_text = "*****"

                def make_toggle_visibility(k, v):
                    def toggle_visibility(e):
                        nonlocal password_text, password_visible
                        password_visible = not password_visible
                        row_index = None
                        for i, row in enumerate(table_rows):
                            if row.cells[0].content.value == k:
                                row_index = i
                                break

                        if row_index is not None:
                            table_rows[row_index].cells[1].content.value = (
                                v if password_visible else "*****"
                            )
                            self.page.update()

                    return toggle_visibility

                def make_copy_value(v):
                    def copy_value(e):
                        pyperclip_copy(v)

                    return copy_value

                eye_button = IconButton(
                    icon=Icons.VISIBILITY,
                    tooltip="Show/Hide Password",
                    on_click=make_toggle_visibility(key, value),
                )

                copy_button = IconButton(
                    icon=Icons.COPY,
                    tooltip="Copy Password",
                    on_click=make_copy_value(value),
                )

                row = DataRow(
                    cells=[
                        DataCell(Text(key)),
                        DataCell(Text(password_text)),
                        DataCell(Row([eye_button, copy_button])),
                    ]
                )
                table_rows.append(row)
            else:
                copy_button = IconButton(
                    icon=Icons.COPY,
                    tooltip="Copy Value",
                    on_click=lambda e, value=value: pyperclip_copy(value),
                )

                row = DataRow(
                    cells=[
                        DataCell(Text(key)),
                        DataCell(Text(value)),
                        DataCell(copy_button),
                    ]
                )
                table_rows.append(row)

        # OTP行の追加
        if "winauth_name" in password_info:
            otp_generator = self.password_manager.get_otp(uid)
            if otp_generator:
                otp_code_text = Text("", weight="bold")
                remaining_time_text = Text("", color=Colors.BLUE, size=12)
                progress_ring = ProgressRing(
                    width=16, height=16, stroke_width=2, visible=False
                )

                def make_copy_otp():
                    def copy_otp(e):
                        if otp_code_text.value:
                            pyperclip_copy(otp_code_text.value)

                    return copy_otp

                generate_button = ElevatedButton(
                    text="Generate",
                    on_click=lambda e: self.generate_otp(
                        otp_generator,
                        otp_code_text,
                        remaining_time_text,
                        generate_button,
                        progress_ring,
                    ),
                    style=ButtonStyle(
                        padding=Padding(8, 4, 8, 4),
                    ),
                )

                copy_button = IconButton(
                    icon=Icons.COPY,
                    tooltip="Copy OTP",
                    on_click=make_copy_otp(),
                )

                otp_row = DataRow(
                    cells=[
                        DataCell(Text("OTP")),
                        DataCell(
                            Row(
                                [
                                    otp_code_text,
                                    remaining_time_text,
                                    progress_ring,
                                ],
                                alignment=MainAxisAlignment.START,
                                spacing=10,
                            )
                        ),
                        DataCell(
                            Row(
                                [generate_button, copy_button],
                                alignment=MainAxisAlignment.START,
                            )
                        ),
                    ]
                )
                table_rows.append(otp_row)

        if table_rows:
            self.detail_view.controls.append(
                DataTable(
                    columns=[
                        DataColumn(Text("Field")),
                        DataColumn(Text("Value")),
                        DataColumn(Text("Actions")),
                    ],
                    rows=table_rows,
                )
            )

        self.page.update()

    def edit_password(self, uid):
        password_info = self.password_manager.get_password_info(uid)
        custom_fields = []

        def add_custom_field(e):
            field_name = TextField(label="Field Name")
            field_value = TextField(label="Field Value")
            remove_button = IconButton(
                icon=Icons.REMOVE, icon_color=Colors.RED, on_click=None  # 後で設定
            )

            field_row = Row([field_name, field_value, remove_button])

            # remove_buttonのon_clickを設定
            remove_button.on_click = lambda e, row=field_row: remove_custom_field(row)

            custom_fields.append((field_name, field_value))
            custom_fields_container.controls.append(field_row)
            self.page.update()

        def remove_custom_field(field_row):
            if field_row in custom_fields_container.controls:
                custom_fields_container.controls.remove(field_row)
                # カスタムフィールドのリストも更新
                field_name = field_row.controls[0]
                field_value = field_row.controls[1]
                custom_fields[:] = [
                    (name, value)
                    for name, value in custom_fields
                    if name != field_name and value != field_value
                ]
                self.page.update()

        def on_submit(e):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_info = {
                "title": title_field.value,
                "password": password_field.value,
                "note": note_field.value,
                "update-time": current_time,
            }

            # 既存のcreate-timeを保持
            if "create-time" in password_info:
                updated_info["create-time"] = password_info["create-time"]

            # WinAuth名が設定されている場合は保持
            if "winauth_name" in password_info:
                updated_info["winauth_name"] = password_info["winauth_name"]

            # カスタムフィールドを追加
            for field_name, field_value in custom_fields:
                if field_name.value.strip() and field_value.value.strip():
                    updated_info[field_name.value.strip()] = field_value.value.strip()

            self.password_manager.update_password(uid, updated_info)
            self.update_password_list()
            self.show_password_details(uid)

        def on_cancel(e):
            self.show_password_details(uid)

        self.detail_view.controls.clear()

        title_field = TextField(label="Title", value=password_info.get("title", ""))
        password_field = TextField(
            label="Password", value=password_info.get("password", ""), password=True
        )
        note_field = TextField(label="Note", value=password_info.get("note", ""))

        custom_fields_container = Column()
        for key, value in password_info.items():
            if key not in ["title", "password", "note", "create-time", "update-time"]:
                field_name = TextField(label="Field Name", value=key)
                field_value = TextField(label="Field Value", value=value)
                remove_button = IconButton(
                    icon=Icons.REMOVE,
                    icon_color=Colors.RED,
                    on_click=lambda e, field_row=None: remove_custom_field(field_row),
                )

                field_row = Row([field_name, field_value, remove_button])
                custom_fields.append((field_name, field_value))
                custom_fields_container.controls.append(field_row)

        add_field_button = ElevatedButton(
            text="Add Custom Field", on_click=add_custom_field
        )

        submit_button = ElevatedButton(text="Submit", on_click=on_submit)
        cancel_button = ElevatedButton(text="Cancel", on_click=on_cancel)

        self.detail_view.controls.append(
            Column(
                [
                    Text("Edit Password", weight="bold", size=20),
                    title_field,
                    password_field,
                    note_field,
                    custom_fields_container,
                    add_field_button,
                    Row(
                        [submit_button, cancel_button],
                        alignment=MainAxisAlignment.END,
                    ),
                ],
            )
        )

        self.page.update()

    def add_password(self, e):
        custom_fields = []

        def add_custom_field(e):
            field_name = TextField(label="Field Name")
            field_value = TextField(label="Field Value")
            remove_button = IconButton(
                icon=Icons.REMOVE,
                icon_color=Colors.RED,
                on_click=lambda e: remove_custom_field(field_row),
            )

            field_row = Row([field_name, field_value, remove_button])
            custom_fields.append((field_name, field_value))
            custom_fields_container.controls.append(field_row)
            self.page.update()

        def remove_custom_field(field_row):
            custom_fields_container.controls.remove(field_row)
            custom_fields[:] = [
                (name, value)
                for name, value in custom_fields
                if name != field_row.controls[0] and value != field_row.controls[1]
            ]
            self.page.update()

        def on_submit(e):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            password_info = {
                "title": title_field.value,
                "password": password_field.value,
                "note": note_field.value,
                "create-time": current_time,
                "update-time": current_time,
            }

            # WinAuth名が入力されている場合は追加
            if winauth_field.value.strip():
                password_info["winauth_name"] = winauth_field.value.strip()

            for field_name, field_value in custom_fields:
                if field_name.value.strip() and field_value.value.strip():
                    password_info[field_name.value.strip()] = field_value.value.strip()

            self.password_manager.add_password(password_info)
            self.update_password_list()
            self.detail_view.controls.clear()
            self.detail_view.controls.append(
                Text("Password added successfully!", color=Colors.GREEN)
            )
            self.page.update()

        def on_cancel(e):
            self.detail_view.controls.clear()
            self.detail_view.controls.append(
                Text("Password addition canceled.", color=Colors.BLUE)
            )
            self.page.update()

        def generate_password(e):
            base_text = password_seed_field.value
            if not base_text:
                return

            hash_obj = sha256(base_text.encode())
            hash_value = hash_obj.hexdigest()

            password_length = int(length_slider.value)
            generated_password = hash_value[:password_length]
            password_result.value = generated_password
            self.page.update()

        def copy_generated_password(e):
            if password_result.value:
                pyperclip_copy(password_result.value)

        def update_length_label(e):
            length_label.value = f"パスワード長: {int(length_slider.value)}"
            self.page.update()

        self.detail_view.controls.clear()
        title_field = TextField(label="Title")
        password_field = TextField(label="Password", password=True)
        note_field = TextField(label="Note")
        winauth_field = TextField(
            label="WinAuth Name", hint_text="WinAuthのXMLファイルの<name>タグの値を入力"
        )

        custom_fields_container = Column()

        add_field_button = ElevatedButton(
            text="Add Custom Field", on_click=add_custom_field
        )

        submit_button = ElevatedButton(text="Submit", on_click=on_submit)
        cancel_button = ElevatedButton(text="Cancel", on_click=on_cancel)

        password_generator_container = Container(
            content=Column(
                [
                    Text("パスワード生成", weight="bold", size=16),
                    Row(
                        [
                            Text("元となる文字: "),
                            password_seed_field := TextField(
                                hint_text="ハッシュ化する文字を入力", expand=True
                            ),
                        ]
                    ),
                    Row(
                        [
                            length_slider := Slider(
                                min=4,
                                max=64,
                                value=12,
                                divisions=60,
                                label="{value}",
                                on_change=update_length_label,
                                expand=True,
                            ),
                        ]
                    ),
                    length_label := Text("パスワード長: 12"),
                    Row(
                        [
                            ElevatedButton(
                                text="生成",
                                on_click=generate_password,
                                icon=Icons.PASSWORD,
                            ),
                        ]
                    ),
                    Row(
                        [
                            password_result := Text("", expand=True),
                            IconButton(
                                icon=Icons.COPY,
                                tooltip="Copy Generated Password",
                                on_click=copy_generated_password,
                            ),
                        ]
                    ),
                ]
            ),
            padding=10,
            border=border.all(1, Colors.GREY_400),
            border_radius=10,
        )

        self.detail_view.controls.append(
            Column(
                [
                    Text("Add New Password", weight="bold"),
                    title_field,
                    password_field,
                    note_field,
                    winauth_field,  # WinAuthフィールドを追加
                    custom_fields_container,
                    add_field_button,
                    Row(
                        [submit_button, cancel_button],
                        alignment=MainAxisAlignment.END,
                    ),
                    Divider(),
                    password_generator_container,
                ]
            )
        )

        self.page.update()

    def delete_password(self):  # eパラメータを削除
        selected_uid = self.selected_uid
        if not selected_uid:
            self.detail_view.controls.clear()
            self.detail_view.controls.append(
                Text("No password selected!", color=Colors.RED)
            )
            self.page.update()
            return

        def on_confirm(e):
            self.password_manager.delete_password(selected_uid)
            self.update_password_list()
            self.detail_view.controls.clear()
            self.detail_view.controls.append(
                Text("Password deleted successfully!", color=Colors.GREEN)
            )
            self.page.update()

        def on_cancel(e):
            self.detail_view.controls.clear()
            self.show_password_details(selected_uid)  # キャンセル時は詳細画面に戻る

        self.detail_view.controls.clear()
        self.detail_view.controls.append(
            Column(
                [
                    Text(
                        "このパスワードを削除してもよろしいですか？",
                        weight="bold",
                        size=16,
                        color=Colors.RED,
                    ),
                    Row(
                        [
                            ElevatedButton(
                                text="はい",
                                on_click=on_confirm,
                                style=ButtonStyle(
                                    color=Colors.WHITE,
                                    bgcolor=Colors.RED,
                                ),
                            ),
                            ElevatedButton(
                                text="いいえ",
                                on_click=on_cancel,
                            ),
                        ],
                        alignment=MainAxisAlignment.END,
                        spacing=10,
                    ),
                ],
                spacing=20,
            )
        )
        self.page.update()

    async def countdown_timer(
        self,
        remaining_seconds: int,
        remaining_time_text,
        otp_code_text,
        generate_button,
        progress_ring,
    ):
        """残り時間のカウントダウンを行います"""
        try:
            while remaining_seconds > 0:
                remaining_time_text.value = f"({remaining_seconds}秒)"
                self.page.update()
                await asyncio.sleep(1)
                remaining_seconds -= 1

            # タイマー終了時の処理
            otp_code_text.value = ""
            remaining_time_text.value = ""
            generate_button.disabled = False
            progress_ring.visible = False
            self.page.update()
        except Exception as e:
            print(f"Countdown timer error: {e}")

    def generate_otp(
        self,
        otp_generator,
        otp_code_text,
        remaining_time_text,
        generate_button,
        progress_ring,
    ):
        """OTPを生成し、タイマーを開始します"""
        try:
            otp_info = otp_generator.generate()
            otp_code_text.value = otp_info.otp
            generate_button.disabled = True
            progress_ring.visible = True
            self.page.update()

            # カウントダウンタイマーを開始
            asyncio.run(
                self.countdown_timer(
                    otp_info.remaining_seconds,
                    remaining_time_text,
                    otp_code_text,
                    generate_button,
                    progress_ring,
                )
            )
        except Exception as e:
            print(f"Generate OTP error: {e}")
            # エラー時の状態リセット
            generate_button.disabled = False
            progress_ring.visible = False
            self.page.update()
