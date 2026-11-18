
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = r"D:\cơ sở dữ liệu\Robot_Warehouse\warehouse_robot.db"

random.seed(42)


def insert_data(conn, table, data):
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    cursor = conn.execute(sql, tuple(data.values()))
    return cursor.lastrowid


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        print("Loi: Chua bat duoc khoa ngoai!")
        conn.close()
        return

    tables = [
        "ThietBiRobot",
        "ThongSoKyThuat",
        "MaHang",
        "NhatKyHoatDong",
        "NhatKyGocKhop",
        "NhatKyCanhBao",
        "CamBien",
        "NhatKyCamBien"
    ]

    # Khong ghi de du lieu cu
    for table in tables:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        if count > 0:
            print(f"Bang {table} da co du lieu.")
            print("Dung chuong trinh de tranh nhap trung.")
            conn.close()
            return

    now = datetime.now().replace(microsecond=0)

    try:
        with conn:

            # ==================================
            # 1. THIET BI ROBOT
            # ==================================

            robots = []

            robot_info = [
                ("ROBOT_01", "ARM-6DOF-01", "Khu phan loai A"),
                ("ROBOT_02", "ARM-6DOF-02", "Khu phan loai B"),
                ("ROBOT_03", "ARM-6DOF-03", "Khu phan loai C")
            ]

            statuses = [
                "Hoat dong",
                "Canh bao",
                "Bao tri"
            ]

            for i, (name, model, location) in enumerate(robot_info):
                robot_id = insert_data(conn, "ThietBiRobot", {
                    "TenRobot": name,
                    "LoaiRobot": "Canh tay robot cong nghiep",
                    "HangSanXuat": "Mo phong",
                    "ModelRobot": model,
                    "ViTriLapDat": location,
                    "NgayLapDat": (now - timedelta(days=180)).strftime(
                        "%Y-%m-%d"
                    ),
                    "TrangThaiHoatDong": statuses[i],
                    "GhiChu": "Du lieu robot mo phong"
                })

                robots.append(robot_id)

            print("Da tao 3 robot.")

            # ==================================
            # 2. THONG SO KY THUAT
            # ==================================

            for i, robot_id in enumerate(robots):
                insert_data(conn, "ThongSoKyThuat", {
                    "RobotID": robot_id,
                    "SoBacTuDo": 6,
                    "SoLuongKhop": 6,
                    "TaiTrongToiDa": 5.0 + i,
                    "TamVoiToiDa": 0.8 + i * 0.1,
                    "DoChinhXacLapLai": 0.05,
                    "TocDoToiDa": 180.0,
                    "BoDieuKhien": "PLC mo phong",
                    "GiaoThucKetNoi": "TCP/IP",
                    "NgayCapNhat": now.strftime("%Y-%m-%d"),
                    "GhiChu": "Robot 6 bac tu do"
                })

            # ==================================
            # 3. MA HANG
            # ==================================

            products = [
                ("MH001", "San pham A", "Loai A", 1.2),
                ("MH002", "San pham B", "Loai B", 2.5),
                ("MH003", "San pham C", "Loai C", 0.8),
                ("MH004", "San pham D", "Loai A", 3.0),
                ("MH005", "San pham E", "Loai B", 1.5)
            ]

            product_ids = []

            for code, name, category, weight in products:
                product_id = insert_data(conn, "MaHang", {
                    "MaHang": code,
                    "TenSanPham": name,
                    "LoaiSanPham": category,
                    "KhoiLuong": weight,
                    "ChieuDai": 10.0,
                    "ChieuRong": 8.0,
                    "ChieuCao": 5.0,
                    "GhiChu": "Du lieu san pham mo phong"
                })
                product_ids.append(product_id)

            # ==================================
            # 4. CAM BIEN
            # ==================================

            sensor_types = [
                ("LiDAR", "Cam bien khoang cach", "m"),
                ("Encoder", "Cam bien vi tri", "xung"),
                ("Ultrasonic", "Cam bien vat can", "cm")
            ]

            sensors_by_robot = {}

            for i, robot_id in enumerate(robots):
                sensors_by_robot[robot_id] = []

                for sensor_type, sensor_name, unit in sensor_types:
                    sensor_id = insert_data(conn, "CamBien", {
                        "RobotID": robot_id,
                        "TenCamBien": sensor_name,
                        "LoaiCamBien": sensor_type,
                        "HangSanXuat": "Mo phong",
                        "ModelCamBien": sensor_type + "-SIM",
                        "ViTriLapDat": "Vi tri " + sensor_type,
                        "DonViDo": unit,
                        "TrangThai": "Hoat dong",
                        "GhiChu": "Cam bien ao trong CoppeliaSim"
                    })

                    sensors_by_robot[robot_id].append(
                        (sensor_id, sensor_type, unit)
                    )

            # ==================================
            # 5. NHAT KY HOAT DONG
            # ==================================

            activity_ids = {}
            activity_types = [
                "Gap san pham",
                "Phan loai san pham",
                "Di chuyen san pham",
                "Dat san pham",
                "Kiem tra san pham"
            ]

            for r_index, robot_id in enumerate(robots):
                activity_ids[robot_id] = []

                for j in range(5):
                    start = now - timedelta(
                        hours=3,
                        minutes=r_index * 30 + j * 10
                    )
                    end = start + timedelta(seconds=30 + j * 5)

                    result = (
                        "That bai" if (r_index == 1 and j == 4)
                        else "Thanh cong"
                    )

                    activity_id = insert_data(
                        conn, "NhatKyHoatDong", {
                            "RobotID": robot_id,
                            "MaHangID": product_ids[j % 5],
                            "ThoiGianBatDau": start.isoformat(
                                sep=" "
                            ),
                            "ThoiGianKetThuc": end.isoformat(
                                sep=" "
                            ),
                            "LoaiThaoTac": activity_types[j],
                            "KetQua": result,
                            "ThoiGianXuLy": (
                                end - start
                            ).total_seconds(),
                            "GhiChu": "Nhat ky hoat dong mo phong"
                        }
                    )

                    activity_ids[robot_id].append(activity_id)

            # ==================================
            # 6. NHAT KY GOC KHOP
            # ==================================

            for robot_id in robots:
                for activity_index, activity_id in enumerate(
                    activity_ids[robot_id]
                ):
                    for sample in range(3):
                        angles = [
                            round(random.uniform(-90, 90), 2)
                            for _ in range(6)
                        ]

                        log_time = now - timedelta(
                            hours=3,
                            minutes=activity_index * 10,
                            seconds=sample * 5
                        )

                        insert_data(conn, "NhatKyGocKhop", {
                            "RobotID": robot_id,
                            "HoatDongID": activity_id,
                            "ThoiGian": log_time.isoformat(sep=" "),
                            "Goc_J1": angles[0],
                            "Goc_J2": angles[1],
                            "Goc_J3": angles[2],
                            "Goc_J4": angles[3],
                            "Goc_J5": angles[4],
                            "Goc_J6": angles[5],
                            "TrangThai": "Hoat dong"
                        })

            # ==================================
            # 7. NHAT KY CANH BAO
            # ==================================

            warning_data = [
                (0, 1, "W001", "Thap",
                 "Khoang cach vat can gan"),
                (0, 3, "W002", "Trung binh",
                 "Canh bao sai lech vi tri"),
                (1, 2, "E001", "Cao",
                 "Thao tac gap san pham that bai"),
                (1, 4, "E002", "Cao",
                 "Canh bao qua tai mo phong"),
                (2, 0, "W003", "Thap",
                 "Can kiem tra cam bien")
            ]

            for r_index, activity_index, code, level, message in warning_data:
                robot_id = robots[r_index]
                activity_id = activity_ids[robot_id][activity_index]

                insert_data(conn, "NhatKyCanhBao", {
                    "RobotID": robot_id,
                    "HoatDongID": activity_id,
                    "ThoiGian": now.isoformat(sep=" "),
                    "MaLoi": code,
                    "MucDo": level,
                    "NoiDung": message,
                    "TrangThaiXuLy": (
                        "Da xu ly" if r_index == 0
                        else "Dang xu ly" if r_index == 1
                        else "Chua xu ly"
                    ),
                    "GhiChu": "Canh bao du lieu mo phong"
                })

            # ==================================
            # 8. NHAT KY CAM BIEN
            # ==================================

            for robot_id in robots:
                activities = activity_ids[robot_id]

                for sensor_id, sensor_type, unit in sensors_by_robot[robot_id]:
                    for j in range(10):

                        if sensor_type == "LiDAR":
                            value = round(
                                random.uniform(0.5, 4.0), 2
                            )
                        elif sensor_type == "Encoder":
                            value = random.randint(500, 3000)
                        else:
                            value = round(
                                random.uniform(10, 150), 2
                            )

                        status = (
                            "Canh bao" if j in (7, 8)
                            else "Binh thuong"
                        )

                        log_time = now - timedelta(
                            minutes=30,
                            seconds=j * 5
                        )

                        insert_data(conn, "NhatKyCamBien", {
                            "CamBienID": sensor_id,
                            "HoatDongID": activities[j % 5],
                            "ThoiGian": log_time.isoformat(sep=" "),
                            "GiaTri": value,
                            "DonViDo": unit,
                            "TrangThaiDuLieu": status,
                            "GhiChu": "Du lieu cam bien mo phong"
                        })

            # ==================================
            # KIEM TRA KHOA NGOAI
            # ==================================

            violations = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

            if violations:
                raise Exception(
                    f"Phat hien loi khoa ngoai: {violations}"
                )

        print("\nHOAN THANH NHAP DU LIEU!")

        print("\nSO LUONG BAN GHI:")
        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count}")

        print("\nKhong phat hien loi khoa ngoai.")

    except Exception as e:
        print("\nLOI KHI NHAP DU LIEU:", e)
        print("Giao dich da duoc rollback neu chua commit.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
