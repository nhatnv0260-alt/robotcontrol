
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

from streamlit_autorefresh import st_autorefresh


def render_realtime(DB_PATH):

    # Tu dong cap nhat moi 1 giay
    st_autorefresh(
        interval=1000,
        key="realtime_refresh"
    )

    def read_sql(query, params=()):
        with sqlite3.connect(DB_PATH, timeout=5) as conn:
            conn.execute("PRAGMA busy_timeout = 5000")
            return pd.read_sql_query(
                query,
                conn,
                params=params
            )

    st.title("📡 GIÁM SÁT ROBOT REAL-TIME")
    st.caption("Dữ liệu mô phỏng được cập nhật liên tục mỗi giây.")

    # --------------------------------
    # 1. CHON ROBOT
    # --------------------------------

    robots = read_sql("""
        SELECT RobotID, TenRobot, TrangThaiHoatDong
        FROM ThietBiRobot
        ORDER BY RobotID
    """)

    if robots.empty:
        st.warning("Chưa có dữ liệu robot.")
        return

    robot_options = {
        f"{row['TenRobot']} (ID: {row['RobotID']})":
        int(row["RobotID"])
        for _, row in robots.iterrows()
    }

    selected_name = st.selectbox(
        "Chọn robot giám sát",
        list(robot_options.keys()),
        key="realtime_robot"
    )

    robot_id = robot_options[selected_name]

    robot_status = robots.loc[
        robots["RobotID"] == robot_id,
        "TrangThaiHoatDong"
    ].iloc[0]

    # --------------------------------
    # 2. THONG KE
    # --------------------------------

    joint_count = read_sql("""
        SELECT COUNT(*) AS total
        FROM NhatKyGocKhop
        WHERE RobotID = ?
          AND TrangThai = 'Mo phong'
    """, (robot_id,)).iloc[0]["total"]

    sensor_count = read_sql("""
        SELECT COUNT(*) AS total
        FROM NhatKyCamBien d
        JOIN CamBien c ON d.CamBienID = c.CamBienID
        WHERE c.RobotID = ?
          AND d.GhiChu = 'Du lieu mo phong'
    """, (robot_id,)).iloc[0]["total"]

    latest_time = read_sql("""
        SELECT MAX(ThoiGian) AS latest
        FROM NhatKyGocKhop
        WHERE RobotID = ?
          AND TrangThai = 'Mo phong'
    """, (robot_id,)).iloc[0]["latest"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Robot đang chọn", f"Robot {robot_id}")
    c2.metric("Trạng thái", str(robot_status))
    c3.metric("Bản ghi góc khớp", int(joint_count))
    c4.metric("Bản ghi cảm biến", int(sensor_count))

    st.caption(
        f"Thời điểm ghi góc khớp gần nhất: "
        f"{latest_time or 'Chưa có dữ liệu'}"
    )

    st.divider()

    # --------------------------------
    # 3. GOC 6 KHOP
    # --------------------------------

    st.subheader("1. Theo dõi góc 6 khớp J1–J6")

    joints = read_sql("""
        SELECT
            Goc_ID,
            ThoiGian,
            Goc_J1,
            Goc_J2,
            Goc_J3,
            Goc_J4,
            Goc_J5,
            Goc_J6
        FROM NhatKyGocKhop
        WHERE RobotID = ?
          AND TrangThai = 'Mo phong'
        ORDER BY Goc_ID DESC
        LIMIT 60
    """, (robot_id,))

    if not joints.empty:

        joints = joints.sort_values("Goc_ID")

        joint_columns = [
            "Goc_J1", "Goc_J2", "Goc_J3",
            "Goc_J4", "Goc_J5", "Goc_J6"
        ]

        joint_long = joints.melt(
            id_vars=["ThoiGian"],
            value_vars=joint_columns,
            var_name="Khớp",
            value_name="Góc"
        )

        joint_long["Góc"] = pd.to_numeric(
            joint_long["Góc"],
            errors="coerce"
        )

        fig = px.line(
            joint_long,
            x="ThoiGian",
            y="Góc",
            color="Khớp",
            markers=True,
            title="Biến thiên góc các khớp theo thời gian"
        )

        fig.update_layout(
            xaxis_title="Thời gian",
            yaxis_title="Góc (độ)",
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        latest = joints.iloc[-1]

        st.markdown("**Góc khớp mới nhất**")

        cols = st.columns(6)

        for i, col in enumerate(cols):
            value = latest[f"Goc_J{i + 1}"]

            col.metric(
                f"J{i + 1}",
                f"{value:.2f}°"
            )

        with st.expander("Xem lịch sử góc khớp"):
            st.dataframe(
                joints.sort_values(
                    "Goc_ID",
                    ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )

        st.markdown("**Heatmap góc khớp**")

        heatmap_data = joints[joint_columns].tail(20)
        heatmap_data.columns = [
            "J1", "J2", "J3", "J4", "J5", "J6"
        ]

        fig_heatmap, ax = plt.subplots(figsize=(10, 4))

        sns.heatmap(
            heatmap_data,
            cmap="coolwarm",
            linewidths=0.3,
            ax=ax
        )

        ax.set_title("Góc 6 khớp trong 20 lần ghi gần nhất")
        ax.set_xlabel("Khớp")
        ax.set_ylabel("Lần ghi dữ liệu")

        st.pyplot(fig_heatmap)
        plt.close(fig_heatmap)

    else:
        st.info(
            "Chưa có dữ liệu góc khớp mô phỏng. "
            "Hãy chạy mo_phong_du_lieu.py."
        )

    st.divider()

    # --------------------------------
    # 4. DU LIEU CAM BIEN
    # --------------------------------

    st.subheader("2. Theo dõi dữ liệu cảm biến")

    sensors = read_sql("""
        SELECT
            d.DuLieuCamBienID,
            d.ThoiGian,
            c.TenCamBien,
            c.LoaiCamBien,
            d.GiaTri,
            COALESCE(d.DonViDo, c.DonViDo) AS DonViDo,
            d.TrangThaiDuLieu
        FROM NhatKyCamBien d
        JOIN CamBien c
            ON d.CamBienID = c.CamBienID
        WHERE c.RobotID = ?
          AND d.GhiChu = 'Du lieu mo phong'
        ORDER BY d.DuLieuCamBienID DESC
        LIMIT 150
    """, (robot_id,))

    if not sensors.empty:

        sensor_names = sorted(
            sensors["TenCamBien"].dropna().unique().tolist()
        )

        selected_sensor = st.selectbox(
            "Chọn cảm biến",
            sensor_names,
            key="realtime_sensor"
        )

        sensor_view = sensors[
            sensors["TenCamBien"] == selected_sensor
        ].copy()

        sensor_view = sensor_view.sort_values(
            "DuLieuCamBienID"
        )

        sensor_view["GiaTri"] = pd.to_numeric(
            sensor_view["GiaTri"],
            errors="coerce"
        )

        sensor_view = sensor_view.dropna(
            subset=["GiaTri"]
        )

        if not sensor_view.empty:

            fig_sensor = px.line(
                sensor_view,
                x="ThoiGian",
                y="GiaTri",
                markers=True,
                title=f"Dữ liệu cảm biến: {selected_sensor}"
            )

            fig_sensor.update_layout(
                xaxis_title="Thời gian",
                yaxis_title="Giá trị đo",
                hovermode="x unified"
            )

            st.plotly_chart(
                fig_sensor,
                use_container_width=True
            )

            latest_sensor = sensor_view.iloc[-1]

            a, b, c = st.columns(3)

            a.metric("Cảm biến", selected_sensor)
            b.metric(
                "Giá trị mới nhất",
                f"{latest_sensor['GiaTri']} "
                f"{latest_sensor['DonViDo'] or ''}"
            )
            c.metric(
                "Trạng thái dữ liệu",
                str(latest_sensor["TrangThaiDuLieu"])
            )

        with st.expander("Xem lịch sử dữ liệu cảm biến"):
            st.dataframe(
                sensors,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.info("Chưa có dữ liệu cảm biến mô phỏng.")

    st.divider()

    st.caption(
        "Dữ liệu được đọc trực tiếp từ warehouse_robot.db. "
        "Đây là dữ liệu mô phỏng, không phải dữ liệu robot thật."
    )
