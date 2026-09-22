```python
import os
import pandas as pd
import streamlit as st
from streamlit_cookies_controller import CookieController

# =========================================================
# SAYFA AYARLARI
# =========================================================

st.set_page_config(
    page_title="PLANLAMA - Arama Uygulaması",
    page_icon="📍",
    layout="centered"
)

# =========================================================
# AYARLAR
# =========================================================

EXCEL_FILE = "veri.xlsx"

SIFRE = "0707"

# Şifrenin kaç gün hatırlanacağı
OTURUM_GUN = 7

COOKIE_ADI = "planlama_giris"

# Cookie yöneticisi
controller = CookieController()

# =========================================================
# ŞİFRE KONTROLÜ
# =========================================================

def check_password():

    # Daha önce giriş yapılmış mı?
    cookie = controller.get(COOKIE_ADI)

    if cookie == "OK":

        # Oturum açık
        return True

    # Henüz giriş yapılmamış
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    def password_entered():

        girilen_sifre = st.session_state.get("password", "")

        if girilen_sifre == SIFRE:

            st.session_state.password_correct = True

            # Cookie oluştur
            controller.set(
                COOKIE_ADI,
                "OK",
                max_age=OTURUM_GUN * 24 * 60 * 60
            )

            # Şifreyi session_state'den kaldır
            if "password" in st.session_state:
                del st.session_state["password"]

        else:

            st.session_state.password_correct = False

    # Şifre zaten doğruysa
    if st.session_state.password_correct:
        return True

    # -----------------------------------------------------
    # GİRİŞ EKRANI
    # -----------------------------------------------------

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:25px 10px 10px 10px;
        ">
            <h2>🔐 PLANLAMA SİSTEMİ</h2>
            <p>Devam etmek için erişim şifrenizi giriniz.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.text_input(
        "🔒 Erişim Şifresi",
        type="password",
        key="password",
        on_change=password_entered
    )

    if st.session_state.password_correct is False:

        # Yanlış şifre girilmişse
        if st.session_state.get("password_attempted", False):
            st.error("❌ Şifre yanlış!")

    return False


# =========================================================
# ŞİFRE KONTROLÜ
# =========================================================

if not check_password():
    st.stop()


# =========================================================
# VERİLERİ YÜKLE
# =========================================================

@st.cache_data
def load_data(path):

    if not os.path.exists(path):
        return None, None

    try:

        xls = pd.ExcelFile(path)

        sheets = xls.sheet_names

        mahalle_sheet = next(
            (s for s in sheets if "MAHALLE" in s.upper()),
            None
        )

        madde_sheet = next(
            (s for s in sheets if "MADDE" in s.upper()),
            None
        )

        df_mahalle = (
            pd.read_excel(path, sheet_name=mahalle_sheet)
            if mahalle_sheet
            else pd.DataFrame()
        )

        df_madde = (
            pd.read_excel(path, sheet_name=madde_sheet)
            if madde_sheet
            else pd.DataFrame()
        )

        return df_mahalle, df_madde

    except Exception:

        return None, None


df_mahalle, df_madde = load_data(EXCEL_FILE)


# =========================================================
# EXCEL KONTROLÜ
# =========================================================

if (
    df_mahalle is None
    or df_madde is None
    or df_mahalle.empty
    or df_madde.empty
):

    st.error(
        f"'{EXCEL_FILE}' dosyası bulunamadı veya "
        "'MAHALLE' / 'MADDE' sayfaları eksik!"
    )

    st.stop()


# =========================================================
# TÜRKÇE BÜYÜK HARF
# =========================================================

def tr_upper(text):

    if not isinstance(text, str):

        text = str(text) if pd.notna(text) else ""

    return text.replace("i", "İ").replace("ı", "I").upper()


# =========================================================
# ÜST BÖLÜM
# =========================================================

col_title, col_exit = st.columns([5, 1])

with col_title:

    st.markdown(
        """
        <h2 style='text-align:center;'>
        MAHALLE ve MADDE ARAMA
        </h2>
        """,
        unsafe_allow_html=True
    )

with col_exit:

    st.markdown(
        "<div style='margin-top:12px;'></div>",
        unsafe_allow_html=True
    )

    if st.button("🚪 Çıkış", use_container_width=True):

        controller.remove(COOKIE_ADI)

        st.session_state.clear()

        st.rerun()


st.markdown("---")


# =========================================================
# ARAMA MODU
# =========================================================

mode = st.radio(
    "Arama Modunu Seçin:",
    [
        "📍 Mahalle ve Kolluk Birimleri",
        "⚖️ Madde ve Suç Tanımları"
    ],
    horizontal=True
)


# =========================================================
# ARAMA KUTUSU
# =========================================================

if "search_query" not in st.session_state:

    st.session_state.search_query = ""


def clear_text():

    st.session_state.search_query = ""


col1, col2 = st.columns([5, 1])


with col1:

    search_text = st.text_input(
        "🔍 Aramak istediğiniz metni girin...",
        key="search_query"
    ).strip()


with col2:

    st.markdown(
        "<div style='margin-top:28px;'></div>",
        unsafe_allow_html=True
    )

    st.button(
        "🧹 Temizle",
        on_click=clear_text,
        use_container_width=True
    )


search_text_upper = tr_upper(search_text)

st.markdown("---")


# =========================================================
# MAHALLE MODU
# =========================================================

if "Mahalle" in mode:

    bulunan_sayi = 0

    for _, row in df_mahalle.iterrows():

        val_mahalle = (
            ""
            if pd.isna(row.iloc[0])
            else str(row.iloc[0])
        )

        val_kolluk = (
            ""
            if len(row) <= 2 or pd.isna(row.iloc[2])
            else str(row.iloc[2])
        )

        val_ilce = (
            ""
            if len(row) <= 3 or pd.isna(row.iloc[3])
            else str(row.iloc[3])
        )

        mahalle_val_upper = tr_upper(val_mahalle)

        if (
            not search_text_upper
            or search_text_upper in mahalle_val_upper
        ):

            bulunan_sayi += 1

            with st.container(border=True):

                st.markdown(
                    f"**📍 {val_mahalle}**"
                )

                st.markdown(
                    f"**İlçe:** {val_ilce}"
                )

                st.markdown(
                    f"**Kolluk Birimi:** {val_kolluk}"
                )


    if bulunan_sayi == 0:

        st.info(
            "Aranan kriterlere uygun sonuç bulunamadı."
        )


# =========================================================
# MADDE MODU
# =========================================================

else:

    bulunan_sayi = 0

    for _, row in df_madde.iterrows():

        full_row_text = " ".join(
            [
                tr_upper(x)
                for x in row.values
            ]
        )

        if (
            not search_text_upper
            or search_text_upper in full_row_text
        ):

            bulunan_sayi += 1

            val_madde = (
                ""
                if pd.isna(row.iloc[0])
                else str(row.iloc[0])
            )

            val_suc = (
                ""
                if len(row) <= 1 or pd.isna(row.iloc[1])
                else str(row.iloc[1])
            )

            val_kanun = (
                ""
                if len(row) <= 2 or pd.isna(row.iloc[2])
                else str(row.iloc[2])
            )

            with st.container(border=True):

                st.markdown(
                    f"**⚖️ Madde {val_madde}** "
                    f"*({val_kanun})*"
                )

                st.markdown(
                    f"**Suç Tanımı:** {val_suc}"
                )


    if bulunan_sayi == 0:

        st.info(
            "Aranan kriterlere uygun sonuç bulunamadı."
        )


# =========================================================
# ALT BİLGİ
# =========================================================

st.markdown("---")

st.caption(
    f"🔐 Oturum {OTURUM_GUN} gün boyunca hatırlanır."
)
```
