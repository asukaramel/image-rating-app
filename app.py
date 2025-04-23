import streamlit as st
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 画像フォルダとファイル一覧取得
IMAGE_FOLDER = "images"
image_files = sorted([
    f for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
])

# セッション初期化
if "index" not in st.session_state:
    st.session_state.index = 0
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
if "submitted_name" not in st.session_state:
    st.session_state.submitted_name = ""

# タイトル
st.title("📸 写真魅力度調査")

# 名前の入力（最初に一度だけ）
if st.session_state.submitted_name == "":
    name = st.text_input("名前を入力してください（ニックネーム可）:")
    if st.button("スタート"):
        if name.strip():
            st.session_state.submitted_name = name.strip()
            st.rerun()
        else:
            st.warning("名前を入力してください。")
else:
    # 評価パート
    if image_files:
        st.progress(st.session_state.index / len(image_files))

        if st.session_state.index < len(image_files):
            st.write("1〜5のボタンで魅力度を選択してください。")
            fname = image_files[st.session_state.index]
            st.image(
                os.path.join(IMAGE_FOLDER, fname),
                caption=f"{st.session_state.index+1} / {len(image_files)}",
                use_container_width=True
            )

            cols = st.columns(5)
            for i, col in enumerate(cols, start=1):
                if col.button(str(i)):
                    st.session_state.ratings[fname] = i
                    st.session_state.index += 1
                    st.rerun()

            st.progress(st.session_state.index / len(image_files))
        else:
            # Google Sheets に保存（タイムスタンプなし）
            SPREADSHEET_ID = "1ISAKfWMjMQ7zUoZB7486pq9JSPU4yxpT_8AorqKQAl8"
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            credentials_dict = st.secrets["gsheets"]
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
            gc = gspread.authorize(credentials)
            worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1

            name = st.session_state.submitted_name
            rows = [[name, filename, rating] for filename, rating in st.session_state.ratings.items()]
            worksheet.append_rows(rows)

            st.success("✨ すべての写真を評価しました！ありがとうございました！")
    else:
        st.warning("写真が見つかりませんでした。")
