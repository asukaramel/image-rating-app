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

# ストリームリットのタイトル
st.title("📸 写真魅力度調査")

if image_files:
    # 進捗バー
    st.progress(st.session_state.index / len(image_files))

    # 評価対象の画像があるとき
    if st.session_state.index < len(image_files):
        st.write("1〜5のボタンで魅力度を選択してください。")

        fname = image_files[st.session_state.index]
        st.image(
            os.path.join(IMAGE_FOLDER, fname),
            caption=f"{st.session_state.index+1} / {len(image_files)}",
            use_container_width=True
        )

        # 1〜5の評価ボタン
        cols = st.columns(5)
        for i, col in enumerate(cols, start=1):
            if col.button(str(i)):
                # セッション状態に評価結果を保持
                st.session_state.ratings[fname] = i
                st.session_state.index += 1
                st.rerun()  # 画像の切り替えをスムーズにするために、次の画像に行く

        # 進捗バーを更新
        st.progress(st.session_state.index / len(image_files))

    else:
        # すべての画像を評価し終わった後
        # Google Sheets の設定
        SPREADSHEET_ID = "1ISAKfWMjMQ7zUoZB7486pq9JSPU4yxpT_8AorqKQAl8"  # Google SheetsのIDを設定
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_dict = st.secrets["gsheets"]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        gc = gspread.authorize(credentials)

        # スプレッドシートに接続
        worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1
        

        for filename, rating in st.session_state.ratings.items():
            worksheet.append_row([filename, rating])

        st.success("✨ すべての写真を評価しました！ありがとうございました！")

else:
    st.warning("写真が見つかりませんでした。")
