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

OTURUM_GUN = 7

COOKIE_ADI = "planlama_giris"

controller = CookieController()


# =========================================================
# TÜRKÇE BÜYÜK HARF
# =========================================================

def tr_upper(text):

    if pd.isna(text):
        return ""

    text = str(text)

    return (
        text
        .replace("i", "İ")
        .replace("ı", "I")
        .upper()
    )


# =========================================================
# ŞİFRE KONTROLÜ
# =========================================================

def check_password():

    cookie = controller.get(COOKIE_ADI)

    if cookie == "OK":
        return True

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if "password_attempted" not in st.session_state:
        st.session_state.password_attempted = False

    def password_entered():

        st.session_state.password_attempted = True

        girilen_sifre = st.session_state.get(
            "password",
            ""
        )

        if girilen_sifre == SIFRE:

            st.session_state.password_correct = True

            controller.set(
                COOKIE_ADI,
                "OK",
                max_age=OTURUM_GUN * 24 * 60 * 60
            )

            if "password" in st.session_state:
                del st.session_state["password"]

        else:

            st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # =====================================================
    # GİRİŞ EKRANI
    # =====================================================

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:30px 10px 15px 10px;
        ">

            <h2>🔐 PLANLAMA SİSTEMİ</h2>

            <p>
                Devam etmek için erişim şifrenizi giriniz.
            </p>

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

    if (
        st.session_state.password_attempted
        and not st.session_state.password_correct
    ):

        st.error("❌ Şifre yanlış!")

    return False


# =========================================================
# ŞİFREYİ KONTROL ET
# =========================================================

if not check_password():

    st.stop()


# =========================================================
# EXCEL VERİLERİNİ YÜKLE
# =========================================================

@st.cache_data
def load_data():

    if not os.path.exists(EXCEL_FILE):

        return None, None, "veri.xlsx dosyası bulunamadı."

    try:

        xls = pd.ExcelFile(EXCEL_FILE)

        sheets = xls.sheet_names

        # -------------------------------------------------
        # MAHALLE SAYFASINI BUL
        # -------------------------------------------------

        mahalle_sheet = next(
            (
                s
                for s in sheets
                if "MAHALLE" in str(s).upper()
            ),
            None
        )

        # -------------------------------------------------
        # MADDE SAYFASINI BUL
        # -------------------------------------------------

        madde_sheet = next(
            (
                s
                for s in sheets
                if "MADDE" in str(s).upper()
            ),
            None
        )

        if mahalle_sheet is None:

            return (
                None,
                None,
                "Mahalle sayfası bulunamadı."
            )

        if madde_sheet is None:

            return (
                None,
                None,
                "Madde sayfası bulunamadı."
            )

        # -------------------------------------------------
        # MAHALLE VERİLERİ
        # -------------------------------------------------

        df_mahalle = pd.read_excel(
            EXCEL_FILE,
            sheet_name=mahalle_sheet,
            header=0
        )

        # -------------------------------------------------
        # MADDE VERİLERİ
        # -------------------------------------------------

        df_madde = pd.read_excel(
            EXCEL_FILE,
            sheet_name=madde_sheet,
            header=None
        )

        return df_mahalle, df_madde, None

    except Exception as e:

        return None, None, str(e)


df_mahalle, df_madde, excel_error = load_data()


# =========================================================
# EXCEL KONTROL
# =========================================================

if excel_error:

    st.error(
        f"❌ Excel yüklenemedi: {excel_error}"
    )

    st.stop()


# =========================================================
# BAŞLIK
# =========================================================

col_title, col_exit = st.columns([5, 1])


with col_title:

    st.markdown(
        """
        <h2 style="text-align:center;">
            📍 MAHALLE ve MADDE ARAMA
        </h2>
        """,
        unsafe_allow_html=True
    )


with col_exit:

    st.markdown(
        "<div style='margin-top:10px;'></div>",
        unsafe_allow_html=True
    )

    if st.button(
        "🚪 Çıkış",
        use_container_width=True
    ):

        controller.remove(
            COOKIE_ADI
        )

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
        key="search_query",
        placeholder="Arama yapın..."
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


search_upper = tr_upper(
    search_text
)


st.markdown("---")


# =========================================================
# MAHALLE VE KOLLUK ARAMASI
# =========================================================

if "Mahalle" in mode:

    bulunan_sayi = 0

    # -----------------------------------------------------
    # SÜTUNLARI BUL
    # -----------------------------------------------------

    columns = list(
        df_mahalle.columns
    )

    # MAHALLE sütunu
    mahalle_col = next(
        (
            c
            for c in columns
            if "MAHALLE" in str(c).upper()
        ),
        None
    )

    # KOLLUK sütunu
    kolluk_col = next(
        (
            c
            for c in columns
            if "KOLLUK" in str(c).upper()
        ),
        None
    )

    # İLÇE sütunu
    ilce_col = next(
        (
            c
            for c in columns
            if "İLÇE" in str(c).upper()
            or "ILCE" in str(c).upper()
        ),
        None
    )


    # =====================================================
    # MAHALLELERİ DÖN
    # =====================================================

    for _, row in df_mahalle.iterrows():

        # -------------------------------------------------
        # MAHALLE
        # -------------------------------------------------

        if mahalle_col is not None:

            val_mahalle = row.get(
                mahalle_col,
                ""
            )

        else:

            val_mahalle = ""


        # -------------------------------------------------
        # KOLLUK
        # -------------------------------------------------

        if kolluk_col is not None:

            val_kolluk = row.get(
                kolluk_col,
                ""
            )

        else:

            val_kolluk = ""


        # -------------------------------------------------
        # İLÇE
        # -------------------------------------------------

        if ilce_col is not None:

            val_ilce = row.get(
                ilce_col,
                ""
            )

        else:

            val_ilce = ""


        # -------------------------------------------------
        # BOŞ / NAN TEMİZLE
        # -------------------------------------------------

        if pd.isna(val_mahalle):

            val_mahalle = ""

        else:

            val_mahalle = str(
                val_mahalle
            ).strip()


        if pd.isna(val_kolluk):

            val_kolluk = ""

        else:

            val_kolluk = str(
                val_kolluk
            ).strip()


        if pd.isna(val_ilce):

            val_ilce = ""

        else:

            val_ilce = str(
                val_ilce
            ).strip()


        # =================================================
        # ÇOK ÖNEMLİ
        #
        # ARAMA SADECE MAHALLE ÜZERİNDEN YAPILIYOR
        #
        # İlçe ve kolluk burada aramaya dahil DEĞİL.
        # =================================================

        mahalle_arama = tr_upper(
            val_mahalle
        )


        if (
            not search_upper
            or search_upper in mahalle_arama
        ):

            bulunan_sayi += 1


            # -------------------------------------------------
            # SONUÇ KARTI
            # -------------------------------------------------

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### 📍 {val_mahalle}"
                )

                st.write(
                    f"**İlçe:** {val_ilce}"
                )

                st.write(
                    f"**Kolluk Birimi:** {val_kolluk}"
                )


    # =====================================================
    # SONUÇ SAYISI
    # =====================================================

    if bulunan_sayi == 0:

        st.info(
            "🔎 Aranan mahalle bulunamadı."
        )

    else:

        st.caption(
            f"Toplam {bulunan_sayi} mahalle bulundu."
        )


# =========================================================
# MADDE VE SUÇ ARAMASI
# =========================================================

else:

    bulunan_sayi = 0


    # =====================================================
    # EXCEL'DEKİ SÜTUNLAR
    #
    # Madde ve Suçlar sayfasında:
    #
    # 1. sütun = MADDE
    # 2. sütun = SUÇ TANIMI
    # 3. sütun = KANUN
    # =====================================================

    for _, row in df_madde.iterrows():

        # -------------------------------------------------
        # MADDE
        # -------------------------------------------------

        if len(row) > 0:

            val_madde = row.iloc[0]

        else:

            val_madde = ""


        # -------------------------------------------------
        # SUÇ TANIMI
        # -------------------------------------------------

        if len(row) > 1:

            val_suc = row.iloc[1]

        else:

            val_suc = ""


        # -------------------------------------------------
        # KANUN
        # -------------------------------------------------

        if len(row) > 2:

            val_kanun = row.iloc[2]

        else:

            val_kanun = ""


        # -------------------------------------------------
        # NAN TEMİZLE
        # -------------------------------------------------

        if pd.isna(val_madde):

            val_madde = ""

        else:

            val_madde = str(
                val_madde
            ).strip()


        if pd.isna(val_suc):

            val_suc = ""

        else:

            val_suc = str(
                val_suc
            ).strip()


        if pd.isna(val_kanun):

            val_kanun = ""

        else:

            val_kanun = str(
                val_kanun
            ).strip()


        # -------------------------------------------------
        # MADDE ARAMA
        # -------------------------------------------------

        aranacak = " ".join(
            [
                tr_upper(val_madde),
                tr_upper(val_suc),
                tr_upper(val_kanun)
            ]
        )


        if (
            not search_upper
            or search_upper in aranacak
        ):

            bulunan_sayi += 1


            # -------------------------------------------------
            # SONUÇ KARTI
            # -------------------------------------------------

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### ⚖️ Madde {val_madde}"
                )

                st.write(
                    f"**Suç Tanımı:** {val_suc}"
                )

                st.write(
                    f"**Kanun:** {val_kanun}"
                )


    # =====================================================
    # SONUÇ
    # =====================================================

    if bulunan_sayi == 0:

        st.info(
            "🔎 Aranan madde veya suç tanımı bulunamadı."
        )

    else:

        st.caption(
            f"Toplam {bulunan_sayi} sonuç bulundu."
        )


# =========================================================
# ALT BİLGİ
# =========================================================

st.markdown("---")

st.caption(
    f"🔐 Oturum {OTURUM_GUN} gün boyunca hatırlanır."
)
