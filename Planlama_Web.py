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
        girilen_sifre = st.session_state.get("password", "")

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

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:30px 10px 15px 10px;
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

    if (
        st.session_state.password_attempted
        and not st.session_state.password_correct
    ):
        st.error("❌ Şifre yanlış!")

    return False


if not check_password():
    st.stop()

# =========================================================
# EXCEL'İ YÜKLE
# =========================================================

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None, None, None

    try:
        xls = pd.ExcelFile(EXCEL_FILE)

        mahalle_sheet = next(
            (
                s for s in xls.sheet_names
                if "MAHALLE" in str(s).upper()
            ),
            None
        )

        madde_sheet = next(
            (
                s for s in xls.sheet_names
                if "MADDE" in str(s).upper()
            ),
            None
        )

        if mahalle_sheet is None or madde_sheet is None:
            return None, None, (
                "Excel içinde 'Mahalle' ve 'Madde' sayfaları bulunamadı."
            )

        df_mahalle = pd.read_excel(
            EXCEL_FILE,
            sheet_name=mahalle_sheet
        )

        df_madde = pd.read_excel(
            EXCEL_FILE,
            sheet_name=madde_sheet
        )

        return df_mahalle, df_madde, None

    except Exception as e:
        return None, None, str(e)


df_mahalle, df_madde, excel_error = load_data()

if excel_error:
    st.error(f"Excel yüklenemedi: {excel_error}")
    st.stop()

if df_mahalle is None or df_madde is None:
    st.error("veri.xlsx dosyası bulunamadı.")
    st.stop()

# =========================================================
# TÜRKÇE ARAMA
# =========================================================

def tr_upper(value):
    if pd.isna(value):
        return ""

    text = str(value)

    return (
        text
        .replace("i", "İ")
        .replace("ı", "I")
        .upper()
    )


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
        key="search_query",
        placeholder="Örneğin: Kepez, Ahatlı, hırsızlık, TCK..."
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

search_upper = tr_upper(search_text)

st.markdown("---")

# =========================================================
# MAHALLE ARAMA
# =========================================================

if "Mahalle" in mode:

    bulunan_sayi = 0

    # Dosyadaki gerçek sütun adlarını kullan
    columns = list(df_mahalle.columns)

    # Beklenen sütunları başlık adına göre bul
    mahalle_col = next(
        (
            c for c in columns
            if "MAHALLE" in str(c).upper()
        ),
        columns[0] if len(columns) > 0 else None
    )

    kolluk_col = next(
        (
            c for c in columns
            if "KOLLUK" in str(c).upper()
        ),
        columns[2] if len(columns) > 2 else None
    )

    ilce_col = next(
        (
            c for c in columns
            if "İLÇE" in str(c).upper()
            or "ILCE" in str(c).upper()
        ),
        columns[3] if len(columns) > 3 else None
    )

    for _, row in df_mahalle.iterrows():

        val_mahalle = (
            "" if mahalle_col is None
            else str(row.get(mahalle_col, ""))
        )

        val_kolluk = (
            "" if kolluk_col is None
            else str(row.get(kolluk_col, ""))
        )

        val_ilce = (
            "" if ilce_col is None
            else str(row.get(ilce_col, ""))
        )

        # NaN temizliği
        if val_mahalle == "nan":
            val_mahalle = ""

        if val_kolluk == "nan":
            val_kolluk = ""

        if val_ilce == "nan":
            val_ilce = ""

        # Arama yalnızca mahalle, ilçe ve kolluk alanlarında
        aranacak = " ".join(
            [
                tr_upper(val_mahalle),
                tr_upper(val_ilce),
                tr_upper(val_kolluk)
            ]
        )

        if not search_upper or search_upper in aranacak:

            bulunan_sayi += 1

            with st.container(border=True):

                st.markdown(
                    f"### 📍 {val_mahalle}"
                )

                st.write(
                    f"**İlçe:** {val_ilce}"
                )

                st.write(
                    f"**Kolluk Birimi:** {val_kolluk}"
                )

    if bulunan_sayi == 0:
        st.info(
            "🔎 Aranan kriterlere uygun mahalle bulunamadı."
        )
    else:
        st.caption(
            f"Toplam {bulunan_sayi} sonuç bulundu."
        )

# =========================================================
# MADDE ARAMA
# =========================================================

else:

    bulunan_sayi = 0

    columns = list(df_madde.columns)

    # Sütunları başlıklarına göre bul
    madde_col = next(
        (
            c for c in columns
            if "MADDE" in str(c).upper()
        ),
        columns[0] if len(columns) > 0 else None
    )

    suc_col = next(
        (
            c for c in columns
            if "SUÇ" in str(c).upper()
            or "SUC" in str(c).upper()
        ),
        columns[1] if len(columns) > 1 else None
    )

    kanun_col = next(
        (
            c for c in columns
            if "KANUN" in str(c).upper()
        ),
        columns[2] if len(columns) > 2 else None
    )

    for _, row in df_madde.iterrows():

        val_madde = (
            "" if madde_col is None
            else str(row.get(madde_col, ""))
        )

        val_suc = (
            "" if suc_col is None
            else str(row.get(suc_col, ""))
        )

        val_kanun = (
            "" if kanun_col is None
            else str(row.get(kanun_col, ""))
        )

        if val_madde == "nan":
            val_madde = ""

        if val_suc == "nan":
            val_suc = ""

        if val_kanun == "nan":
            val_kanun = ""

        # Tüm alanlarda arama
        aranacak = " ".join(
            [
                tr_upper(val_madde),
                tr_upper(val_suc),
                tr_upper(val_kanun)
            ]
        )

        if not search_upper or search_upper in aranacak:

            bulunan_sayi += 1

            with st.container(border=True):

                st.markdown(
                    f"### ⚖️ Madde {val_madde}"
                )

                st.write(
                    f"**Suç Tanımı:** {val_suc}"
                )

                st.write(
                    f"**Kanun:** {val_kanun}"
                )

    if bulunan_sayi == 0:
        st.info(
            "🔎 Aranan kriterlere uygun madde bulunamadı."
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
