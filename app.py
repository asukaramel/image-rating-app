import streamlit as st
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError
import threading
import time
import json
from streamlit_cookies_manager import EncryptedCookieManager
from datetime import datetime, timezone, timedelta
import random


# Cookie Manager セットアップ
cookies = EncryptedCookieManager(
    prefix="photo-rating-app",
    password=st.secrets["cookie_password"]
)

if not cookies.ready():
    st.stop()


# セッションステート初期化
if "index" not in st.session_state:
    st.session_state.index = 0
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
if "resumed" not in st.session_state:
    st.session_state.resumed = False
if "set_number" not in st.session_state:
    #1~3の乱数を生成してセットを割り当てる
    st.session_state.set_number=random.randint(5,6)

# 画像フォルダとファイル一覧取得
IMAGE_FOLDER = f"images/set{st.session_state.set_number}"

if "shuffled_images" not in st.session_state:
    image_files=[
        f for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    random.shuffle(image_files)
    st.session_state.shuffled_images=image_files
else:
    image_files = st.session_state.shuffled_images


# Google Sheets 初期化（キャッシュ）
@st.cache_resource
def init_worksheet():
    SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gsheets"], scope
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1

worksheet = init_worksheet()

# バックグラウンド書き込み関数（レート制限対応）
def save_row_background(row, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            worksheet.append_row(row)
            break
        except APIError as e:
            if hasattr(e, 'response') and e.response.status_code == 429:
                retries += 1
                time.sleep(60)
            else:
                st.error(f"保存エラー: {e}")
                break

# タイトル
st.title("📸 写真魅力度調査")
# 角丸解除スタイル
st.markdown(
    """
    <style>
    img {
        border-radius: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ユーザー情報取得 or 入力
info = cookies.get("info")
if info is None:
    st.write("まずは以下の情報を入力してください（所要時間は約5分です）")
    name = st.text_input("お名前")
    age_group = st.selectbox(
        "年代", ["選択してください", "10代", "20代", "30代", "40代", "50代", "60代以上"]
    )
    gender = st.selectbox("性別", ["選択してください", "男性", "女性", "その他"])
    if st.button("スタート"):
        if name and age_group != "選択してください" and gender != "選択してください":
            info = {"name": name.strip(), "age_group": age_group, "gender": gender}
            cookies["info"] = json.dumps(info)
            cookies.save()
            st.rerun()
        else:
            st.warning("名前、年代、性別を正しく入力してください。")
    st.stop()

# 再開処理：Google Sheetsから読み込む
if not st.session_state.resumed:
    stored = json.loads(cookies.get("info"))
    rows = worksheet.get_all_values()
    for row in rows:
        if len(row) >= 7 and \
           row[1] == stored['name'] and \
           row[2] == stored['age_group'] and \
           row[3] == stored['gender'] and \
           row[4] == f"set{st.session_state.set_number}":
            fname = row[5]
            try:
                st.session_state.ratings[fname] = int(row[6])
            except:
                pass
    # 未評価の最初のインデックスをセット
    for idx, fname in enumerate(image_files):
        if fname not in st.session_state.ratings:
            st.session_state.index = idx
            break
    else:
        st.session_state.index = len(image_files)
    st.session_state.resumed = True

# 評価UI表示
info = json.loads(cookies.get("info"))

if image_files:

    if st.session_state.index < len(image_files):
        st.markdown("> **※画質も考慮して評価してください。**")
        fname = image_files[st.session_state.index]
        st.image(
            os.path.join(IMAGE_FOLDER, fname),
            caption=f"{st.session_state.index+1} / {len(image_files)}",
            use_container_width=True
        )
        st.progress(st.session_state.index / len(image_files))
        labels=[
            "1全く魅力的でない",
            "2あまり魅力的でない",
            "3どちらともいえない",
            "4やや魅力的",
            "5とても魅力的"
        ]
        cols = st.columns(5)
        for i, col in enumerate(cols):
            if col.button(labels[i]):
                rating_val=i+1
                st.session_state.ratings[fname] = rating_val
                jst=timezone(timedelta(hours=9))
                timestamp=datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
                row = [timestamp,info['name'], info['age_group'], info['gender'], f"set{st.session_state.set_number}", fname, rating_val]
                threading.Thread(target=save_row_background, args=(row,)).start()
                st.session_state.index += 1
                st.rerun()
    else:
        st.success("✨ 全ての写真を評価しました！ありがとうございました！")
else:
    st.warning("写真が見つかりませんでした。")
