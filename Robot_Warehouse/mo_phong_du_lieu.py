
import sqlite3
import random
import time
import math
from pathlib import Path
from datetime import datetime

# Luôn sử dụng database cùng thư mục với file Python
DB_PATH = Path(__file__).resolve().with_name("warehouse_robot.db")

INTERVAL = 1  # Chu kỳ cập nhật: 1 giây


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def simulate_joint_data(conn, robots, activity_ids, step):
    """Tạo dữ liệu góc cho 6 khớp của từng robot."""

    for index, robot_id in enumerate(robots):
        phase = step * 0.12 + index

        angles = [
            round(60 * math.sin(phase), 2),
            round(45 * math.sin(phase + 0.5), 2),
            round(50 * math.cos(phase + 0.8), 2),
            round(70 * math.sin(phase + 1.2), 2),
            round(40 * math.cos(phase + 1.5), 2),
            round(90 * math.sin(phase + 2), 2)
        ]

        conn.execute("""
            INSERT INTO NhatKyGocKhop (
                RobotID, HoatDongID, ThoiGian,
                Goc_J1, Goc_J2, Goc_J3,
                Goc_J4, Goc_J5, Goc_J6,
                TrangThai
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            robot_id,
            activity_ids[robot_id],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            *angles,
            "Mo phong"
        ))


def simulate_sensor_data(conn, sensors, activity_ids, step):
    """Tạo dữ liệu cho các cảm biến."""

    for sensor in sensors:
        sensor_id = sensor["CamBienID"]
        robot_id = sensor["RobotID"]
        sensor_type = sensor["LoaiCamBien"]
        unit = sensor["DonViDo"]

        if sensor_type == "LiDAR":
            value = round(
                2.0 + 1.2 * math.sin(step * 0.15 + robot_id),
                2
            )
            value = max(0.5, min(value, 4.0))

        elif sensor_type == "Encoder":
            value = (step * 25 + robot_id * 500) % 5000

        elif sensor_type == "Ultrasonic":
            value = round(
                80 + 40 * math.sin(step * 0.2 + robot_id),
                2
            )
            value = max(10, min(value, 150))

        else:
            value = round(random.uniform(10, 100), 2)

        status = "Binh thuong"

        if sensor_type in ("LiDAR", "Ultrasonic") and value < 30:
            status = "Canh bao"

        conn.execute("""
            INSERT INTO NhatKyCamBien (
                CamBienID, HoatDongID, ThoiGian,
                GiaTri, DonViDo, TrangThaiDuLieu, GhiChu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            sensor_id,
            activity_ids[robot_id],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            value,
            unit,
            status,
            "Du lieu mo phong"
        ))


def main():
    print("======================================")
    print("   MO PHONG DU LIEU ROBOT WAREHOUSE")
    print("======================================")
    print("Database:", DB_PATH)

    if not DB_PATH.exists():
        print("LOI: Khong tim thay warehouse_robot.db")
        return

    step = 0

    try:
        with get_connection() as conn:

            # Lấy danh sách robot
            robots = [
                row[0] for row in conn.execute(
                    "SELECT RobotID FROM ThietBiRobot"
                ).fetchall()
            ]

            if not robots:
                print("LOI: Chua co robot trong database.")
                return

            # Lấy hoạt động gần nhất của từng robot
            activity_ids = {}

            for robot_id in robots:
                row = conn.execute("""
                    SELECT HoatDongID
                    FROM NhatKyHoatDong
                    WHERE RobotID = ?
                    ORDER BY HoatDongID DESC
                    LIMIT 1
                """, (robot_id,)).fetchone()

                if row is None:
                    print(
                        f"LOI: Robot {robot_id} chua co nhat ky hoat dong."
                    )
                    return

                activity_ids[robot_id] = row[0]

            # Lấy danh sách cảm biến
            rows = conn.execute("""
                SELECT CamBienID, RobotID, LoaiCamBien, DonViDo
                FROM CamBien
            """).fetchall()

            sensors = [
                {
                    "CamBienID": row[0],
                    "RobotID": row[1],
                    "LoaiCamBien": row[2],
                    "DonViDo": row[3]
                }
                for row in rows
            ]

            if not sensors:
                print("LOI: Chua co cam bien trong database.")
                return

        print(f"So robot: {len(robots)}")
        print(f"So cam bien: {len(sensors)}")
        print("Bat dau mo phong moi 1 giay...")
        print("Nhan Ctrl + C de dung.\n")

        while True:
            with get_connection() as conn:
                simulate_joint_data(
                    conn, robots, activity_ids, step
                )

                simulate_sensor_data(
                    conn, sensors, activity_ids, step
                )

            step += 1

            print(
                f"Lan {step}: Da ghi {len(robots)} ban ghi goc khop "
                f"va {len(sensors)} ban ghi cam bien."
            )

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\nDa dung mo phong.")

    except sqlite3.Error as error:
        print("\nLOI DATABASE:", error)

    except Exception as error:
        print("\nLOI:", error)


if __name__ == "__main__":
    main()
