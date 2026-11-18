
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

from realtime_page import render_realtime


# ==========================================
# 1. KET NOI CO SO DU LIEU
# ==========================================

DB_PATH = Path(__file__).resolve().with_name("warehouse_robot.db")

st.set_page_config(
    page_title="Quản lý hệ thống robot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(120,120,120,0.08);
        padding: 14px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


if not DB_PATH.exists():
    st.error(f"Không tìm thấy database: {DB_PATH}")
    st.info(
        "Hãy đặt file app.py cùng thư mục "
        "với warehouse_robot.db."
    )
    st.stop()


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@st.cache_data(ttl=5)
def load_data(query: str, params=()):
    conn = get_connection()

    try:
        return pd.read_sql_query(
            query,
            conn,
            params=params
        )
    finally:
        conn.close()


def count_rows(table: str) -> int:
    df = load_data(
        f"SELECT COUNT(*) AS total FROM {table}"
    )
    return int(df.iloc[0]["total"])


# ==========================================
# 2. MENU CHUYEN TRANG
# ==========================================

st.sidebar.header("🤖 ROBOT WAREHOUSE")

page = st.sidebar.radio(
    "Chọn chức năng",
    [
        "📊 Quản lý dữ liệu",
        "📡 Giám sát Real-time"
    ],
    key="main_page"
)


# Neu chon Real-time thi hien thi giao dien rieng
if page == "📡 Giám sát Real-time":

    render_realtime(DB_PATH)

    st.stop()


# ==========================================
# 3. DASHBOARD QUAN LY DU LIEU
# ==========================================

st.title("🤖 DASHBOARD QUẢN LÝ HỆ THỐNG ROBOT")

st.caption(
    "Theo dõi thiết bị, thông số kỹ thuật, "
    "hoạt động, cảm biến và cảnh báo"
)


# ==========================================
# 4. BO LOC DASHBOARD
# ==========================================

st.sidebar.divider()
st.sidebar.header("Bộ lọc dashboard")

robot_df = load_data("""
    SELECT RobotID, TenRobot, LoaiRobot,
           HangSanXuat, ModelRobot,
           ViTriLapDat, NgayLapDat,
           TrangThaiHoatDong, GhiChu
    FROM ThietBiRobot
    ORDER BY RobotID
""")

if robot_df.empty:
    st.warning("Chưa có dữ liệu robot.")
    st.stop()


robot_options = (
    ["Tất cả robot"]
    + robot_df["TenRobot"].astype(str).tolist()
)

selected_robot = st.sidebar.selectbox(
    "Chọn robot",
    robot_options
)

selected_robot_id = None

if selected_robot != "Tất cả robot":

    selected_robot_id = int(
        robot_df.loc[
            robot_df["TenRobot"] == selected_robot,
            "RobotID"
        ].iloc[0]
    )


if st.sidebar.button("🔄 Làm mới dữ liệu"):

    st.cache_data.clear()
    st.rerun()


# ==========================================
# 5. CAC CHI SO TONG QUAN
# ==========================================

robot_count = count_rows("ThietBiRobot")
sensor_count = count_rows("CamBien")
activity_count = count_rows("NhatKyHoatDong")
alert_count = count_rows("NhatKyCanhBao")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Tổng số robot", robot_count)
col2.metric("Tổng số cảm biến", sensor_count)
col3.metric("Tổng hoạt động", activity_count)
col4.metric("Tổng cảnh báo", alert_count)


# ==========================================
# 6. CAC TAB CHUC NANG
# ==========================================

(
    tab_overview,
    tab_robots,
    tab_activities,
    tab_sensors,
    tab_alerts,
    tab_tables
) = st.tabs([
    "📊 Tổng quan",
    "🤖 Robot",
    "🧾 Hoạt động",
    "📡 Cảm biến",
    "⚠️ Cảnh báo",
    "🗃️ Dữ liệu bảng"
])


# ==========================================
# 7. TAB TONG QUAN
# ==========================================

with tab_overview:

    st.subheader("Tình trạng các robot")

    status_counts = (
        robot_df["TrangThaiHoatDong"]
        .fillna("Chưa xác định")
        .value_counts()
        .rename_axis("Trạng thái")
        .reset_index(name="Số lượng")
    )

    left, right = st.columns(2)

    with left:

        st.dataframe(
            robot_df[
                [
                    "TenRobot",
                    "ModelRobot",
                    "ViTriLapDat",
                    "TrangThaiHoatDong"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    with right:

        st.bar_chart(
            status_counts.set_index("Trạng thái")
        )


    st.subheader("Số hoạt động theo robot")

    activity_by_robot = load_data("""
        SELECT r.TenRobot,
               COUNT(a.HoatDongID) AS SoHoatDong
        FROM ThietBiRobot r
        LEFT JOIN NhatKyHoatDong a
            ON r.RobotID = a.RobotID
        GROUP BY r.RobotID, r.TenRobot
        ORDER BY r.RobotID
    """)

    st.bar_chart(
        activity_by_robot.set_index("TenRobot")
    )


    st.subheader("Tình trạng cảnh báo")

    alert_status = load_data("""
        SELECT TrangThaiXuLy AS TrangThai,
               COUNT(*) AS SoLuong
        FROM NhatKyCanhBao
        GROUP BY TrangThaiXuLy
        ORDER BY SoLuong DESC
    """)

    if not alert_status.empty:

        st.bar_chart(
            alert_status.set_index("TrangThai")
        )

    else:

        st.info("Chưa có cảnh báo.")


# ==========================================
# 8. TAB QUAN LY ROBOT
# ==========================================

with tab_robots:

    st.subheader(
        "Danh sách robot và thông số kỹ thuật"
    )

    robot_details = load_data("""
        SELECT
            r.RobotID,
            r.TenRobot,
            r.LoaiRobot,
            r.HangSanXuat,
            r.ModelRobot,
            r.ViTriLapDat,
            r.NgayLapDat,
            r.TrangThaiHoatDong,
            t.SoBacTuDo,
            t.SoLuongKhop,
            t.TaiTrongToiDa,
            t.TamVoiToiDa,
            t.DoChinhXacLapLai,
            t.TocDoToiDa,
            t.BoDieuKhien,
            t.GiaoThucKetNoi
        FROM ThietBiRobot r
        LEFT JOIN ThongSoKyThuat t
            ON r.RobotID = t.RobotID
        ORDER BY r.RobotID
    """)

    if selected_robot_id is not None:

        robot_details = robot_details[
            robot_details["RobotID"]
            == selected_robot_id
        ]

    st.dataframe(
        robot_details,
        use_container_width=True,
        hide_index=True
    )


    st.subheader("Cảm biến được lắp trên robot")

    sensor_inventory = load_data("""
        SELECT
            r.TenRobot,
            c.TenCamBien,
            c.LoaiCamBien,
            c.HangSanXuat,
            c.ModelCamBien,
            c.ViTriLapDat,
            c.DonViDo,
            c.TrangThai
        FROM CamBien c
        JOIN ThietBiRobot r
            ON c.RobotID = r.RobotID
        ORDER BY r.RobotID, c.CamBienID
    """)

    if selected_robot_id is not None:

        chosen_name = robot_df.loc[
            robot_df["RobotID"] == selected_robot_id,
            "TenRobot"
        ].iloc[0]

        sensor_inventory = sensor_inventory[
            sensor_inventory["TenRobot"] == chosen_name
        ]

    st.dataframe(
        sensor_inventory,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 9. TAB LICH SU HOAT DONG
# ==========================================

with tab_activities:

    st.subheader("Lịch sử hoạt động")

    activities = load_data("""
        SELECT
            a.HoatDongID,
            r.TenRobot,
            m.MaHang,
            m.TenSanPham,
            a.ThoiGianBatDau,
            a.ThoiGianKetThuc,
            a.LoaiThaoTac,
            a.KetQua,
            a.ThoiGianXuLy,
            a.GhiChu
        FROM NhatKyHoatDong a
        JOIN ThietBiRobot r
            ON a.RobotID = r.RobotID
        LEFT JOIN MaHang m
            ON a.MaHangID = m.MaHangID
        ORDER BY
            a.ThoiGianBatDau DESC,
            a.HoatDongID DESC
    """)

    if selected_robot_id is not None:

        chosen_name = robot_df.loc[
            robot_df["RobotID"] == selected_robot_id,
            "TenRobot"
        ].iloc[0]

        activities = activities[
            activities["TenRobot"] == chosen_name
        ]

    st.dataframe(
        activities,
        use_container_width=True,
        hide_index=True
    )


    st.subheader("Thống kê kết quả hoạt động")

    if not activities.empty:

        result_counts = (
            activities["KetQua"]
            .fillna("Chưa cập nhật")
            .value_counts()
            .rename_axis("Kết quả")
            .reset_index(name="Số lượng")
        )

        st.bar_chart(
            result_counts.set_index("Kết quả")
        )


# ==========================================
# 10. TAB DU LIEU CAM BIEN
# ==========================================

with tab_sensors:

    st.subheader("Dữ liệu cảm biến")

    sensor_data = load_data("""
        SELECT
            d.DuLieuCamBienID,
            r.TenRobot,
            c.TenCamBien,
            c.LoaiCamBien,
            d.ThoiGian,
            d.GiaTri,
            COALESCE(d.DonViDo, c.DonViDo) AS DonViDo,
            d.TrangThaiDuLieu,
            d.GhiChu
        FROM NhatKyCamBien d
        JOIN CamBien c
            ON d.CamBienID = c.CamBienID
        JOIN ThietBiRobot r
            ON c.RobotID = r.RobotID
        ORDER BY
            d.ThoiGian DESC,
            d.DuLieuCamBienID DESC
    """)

    if selected_robot_id is not None:

        chosen_name = robot_df.loc[
            robot_df["RobotID"] == selected_robot_id,
            "TenRobot"
        ].iloc[0]

        sensor_data = sensor_data[
            sensor_data["TenRobot"] == chosen_name
        ]

    if not sensor_data.empty:

        sensor_names = (
            ["Tất cả cảm biến"]
            + sorted(
                sensor_data["TenCamBien"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

        chosen_sensor = st.selectbox(
            "Lọc theo cảm biến",
            sensor_names,
            key="sensor_filter"
        )

        if chosen_sensor != "Tất cả cảm biến":

            sensor_data = sensor_data[
                sensor_data["TenCamBien"] == chosen_sensor
            ]

        st.dataframe(
            sensor_data,
            use_container_width=True,
            hide_index=True
        )


        chart_data = sensor_data.copy()

        chart_data["GiaTri"] = pd.to_numeric(
            chart_data["GiaTri"],
            errors="coerce"
        )

        chart_data = chart_data.dropna(
            subset=["GiaTri"]
        )

        if not chart_data.empty:

            st.subheader(
                "Biểu đồ giá trị cảm biến"
            )

            chart_data["Nhãn"] = (
                chart_data["TenRobot"].astype(str)
                + " - "
                + chart_data["TenCamBien"].astype(str)
            )

            chart_pivot = chart_data.pivot_table(
                index="ThoiGian",
                columns="Nhãn",
                values="GiaTri",
                aggfunc="mean"
            ).sort_index()

            st.line_chart(chart_pivot)

    else:

        st.info(
            "Không có dữ liệu cảm biến phù hợp với bộ lọc."
        )


# ==========================================
# 11. TAB CANH BAO
# ==========================================

with tab_alerts:

    st.subheader("Nhật ký cảnh báo và lỗi")

    alerts = load_data("""
        SELECT
            a.CanhBao_ID,
            r.TenRobot,
            a.ThoiGian,
            a.MaLoi,
            a.MucDo,
            a.NoiDung,
            a.TrangThaiXuLy,
            a.GhiChu
        FROM NhatKyCanhBao a
        JOIN ThietBiRobot r
            ON a.RobotID = r.RobotID
        ORDER BY
            a.ThoiGian DESC,
            a.CanhBao_ID DESC
    """)

    if selected_robot_id is not None:

        chosen_name = robot_df.loc[
            robot_df["RobotID"] == selected_robot_id,
            "TenRobot"
        ].iloc[0]

        alerts = alerts[
            alerts["TenRobot"] == chosen_name
        ]

    st.dataframe(
        alerts,
        use_container_width=True,
        hide_index=True
    )

    if not alerts.empty:

        severity_counts = (
            alerts["MucDo"]
            .fillna("Chưa xác định")
            .value_counts()
            .rename_axis("Mức độ")
            .reset_index(name="Số lượng")
        )

        st.bar_chart(
            severity_counts.set_index("Mức độ")
        )


# ==========================================
# 12. TAB XEM DU LIEU CAC BANG
# ==========================================

with tab_tables:

    st.subheader(
        "Xem dữ liệu gốc của từng bảng"
    )

    table_names = [
        "ThietBiRobot",
        "ThongSoKyThuat",
        "MaHang",
        "NhatKyHoatDong",
        "NhatKyGocKhop",
        "NhatKyCanhBao",
        "CamBien",
        "NhatKyCamBien"
    ]

    selected_table = st.selectbox(
        "Chọn bảng dữ liệu",
        table_names
    )

    raw_df = load_data(
        f'SELECT * FROM "{selected_table}"'
    )

    st.caption(
        f"Số bản ghi: {len(raw_df)}"
    )

    st.dataframe(
        raw_df,
        use_container_width=True,
        hide_index=True
    )

    csv_data = raw_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Tải bảng này về CSV",
        data=csv_data,
        file_name=f"{selected_table}.csv",
        mime="text/csv"
    )


# ==========================================
# 13. PHAN TICH BIEU DO
# ==========================================

st.divider()

st.header("📈 PHÂN TÍCH VÀ TRỰC QUAN HÓA DỮ LIỆU")


# ------------------------------------------
# A. BIEU DO SO HOAT DONG THEO ROBOT
# ------------------------------------------

st.subheader("1. Thống kê hoạt động của robot")

activity_chart = load_data("""
    SELECT
        r.TenRobot,
        COUNT(a.HoatDongID) AS SoHoatDong
    FROM ThietBiRobot r
    LEFT JOIN NhatKyHoatDong a
        ON r.RobotID = a.RobotID
    GROUP BY r.RobotID, r.TenRobot
    ORDER BY r.RobotID
""")

if selected_robot_id is not None:

    chosen_name = robot_df.loc[
        robot_df["RobotID"] == selected_robot_id,
        "TenRobot"
    ].iloc[0]

    activity_chart = activity_chart[
        activity_chart["TenRobot"] == chosen_name
    ]


if not activity_chart.empty:

    fig_activity = px.bar(
        activity_chart,
        x="TenRobot",
        y="SoHoatDong",
        color="TenRobot",
        text="SoHoatDong",
        title="Số lượng hoạt động theo robot",
        labels={
            "TenRobot": "Tên robot",
            "SoHoatDong": "Số hoạt động"
        }
    )

    fig_activity.update_layout(
        showlegend=False,
        xaxis_title="Robot",
        yaxis_title="Số hoạt động"
    )

    st.plotly_chart(
        fig_activity,
        use_container_width=True
    )


# ------------------------------------------
# B. BIEU DO CAM BIEN THEO THOI GIAN
# ------------------------------------------

st.subheader("2. Theo dõi dữ liệu cảm biến")

sensor_chart = load_data("""
    SELECT
        r.TenRobot,
        c.TenCamBien,
        c.LoaiCamBien,
        d.ThoiGian,
        d.GiaTri,
        COALESCE(d.DonViDo, c.DonViDo) AS DonViDo
    FROM NhatKyCamBien d
    JOIN CamBien c
        ON d.CamBienID = c.CamBienID
    JOIN ThietBiRobot r
        ON c.RobotID = r.RobotID
    ORDER BY d.ThoiGian
""")

if selected_robot_id is not None:

    chosen_name = robot_df.loc[
        robot_df["RobotID"] == selected_robot_id,
        "TenRobot"
    ].iloc[0]

    sensor_chart = sensor_chart[
        sensor_chart["TenRobot"] == chosen_name
    ]


if not sensor_chart.empty:

    sensor_options = sorted(
        sensor_chart["TenCamBien"].dropna().unique().tolist()
    )

    chosen_sensor = st.selectbox(
        "Chọn cảm biến cần phân tích",
        sensor_options,
        key="plotly_sensor"
    )

    selected_sensor_data = sensor_chart[
        sensor_chart["TenCamBien"] == chosen_sensor
    ].copy()

    selected_sensor_data["GiaTri"] = pd.to_numeric(
        selected_sensor_data["GiaTri"],
        errors="coerce"
    )

    selected_sensor_data = selected_sensor_data.dropna(
        subset=["GiaTri"]
    )

    if not selected_sensor_data.empty:

        fig_sensor = px.line(
            selected_sensor_data,
            x="ThoiGian",
            y="GiaTri",
            color="TenRobot",
            markers=True,
            title=f"Biến thiên dữ liệu cảm biến: {chosen_sensor}",
            labels={
                "ThoiGian": "Thời gian",
                "GiaTri": "Giá trị đo",
                "TenRobot": "Robot"
            }
        )

        st.plotly_chart(
            fig_sensor,
            use_container_width=True
        )

else:

    st.info("Chưa có dữ liệu cảm biến.")


# ------------------------------------------
# C. HEATMAP GOC KHOP J1-J6
# ------------------------------------------

st.subheader("3. Heatmap phân tích góc khớp J1–J6")

joint_chart = load_data("""
    SELECT
        r.TenRobot,
        g.ThoiGian,
        g.Goc_J1,
        g.Goc_J2,
        g.Goc_J3,
        g.Goc_J4,
        g.Goc_J5,
        g.Goc_J6
    FROM NhatKyGocKhop g
    JOIN ThietBiRobot r
        ON g.RobotID = r.RobotID
    ORDER BY g.ThoiGian
""")

if selected_robot_id is not None:

    chosen_name = robot_df.loc[
        robot_df["RobotID"] == selected_robot_id,
        "TenRobot"
    ].iloc[0]

    joint_chart = joint_chart[
        joint_chart["TenRobot"] == chosen_name
    ]


if not joint_chart.empty:

    joint_columns = [
        "Goc_J1",
        "Goc_J2",
        "Goc_J3",
        "Goc_J4",
        "Goc_J5",
        "Goc_J6"
    ]

    joint_values = joint_chart[
        joint_columns
    ].apply(pd.to_numeric, errors="coerce")

    joint_values = joint_values.tail(30)

    fig_heatmap, ax = plt.subplots(figsize=(12, 6))

    sns.heatmap(
        joint_values,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        linewidths=0.5,
        xticklabels=[
            "J1", "J2", "J3", "J4", "J5", "J6"
        ],
        yticklabels=True,
        ax=ax,
        cbar_kws={"label": "Giá trị góc"}
    )

    ax.set_title("Heatmap giá trị góc của 6 khớp robot")
    ax.set_xlabel("Các khớp robot")
    ax.set_ylabel("Thứ tự mẫu dữ liệu")

    plt.tight_layout()

    st.pyplot(fig_heatmap)
    plt.close(fig_heatmap)

else:

    st.info("Chưa có dữ liệu góc khớp.")


st.divider()

st.caption(
    f"Nguồn dữ liệu: {DB_PATH.name} "
    "· Dashboard quản lý dữ liệu."
)
