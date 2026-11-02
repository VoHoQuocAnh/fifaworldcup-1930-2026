import os
import sqlite3
from datetime import datetime
import joblib
import pandas as pd

import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Models.preprocessor import clean_fifa_dataframe

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worldcup.db")
DATA_CSV_PATH = os.path.join(BASE_DIR, "Data", "fifa.csv")
BUNDLE_PATH = os.path.join(BASE_DIR, "saved_models", "model_bundle.pkl")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Khởi tạo cơ sở dữ liệu SQLite (UI/worldcup.db) và nạp dữ liệu lịch sử World Cup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # 1. Bảng lưu lịch sử các trận đấu World Cup (1930 - 2026)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY,
            world_cup_year INTEGER,
            host_country TEXT,
            date TEXT,
            stage TEXT,
            group_name TEXT,
            team1 TEXT,
            team2 TEXT,
            goals_team1 INTEGER,
            goals_team2 INTEGER,
            winner TEXT,
            result_method TEXT,
            stadium TEXT,
            city TEXT
        )
        """
    )

    # 2. Bảng lưu lịch sử dự đoán của người dùng trên giao diện Web
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            team1 TEXT NOT NULL,
            team2 TEXT NOT NULL,
            world_cup_year INTEGER NOT NULL,
            stage TEXT NOT NULL,
            stadium TEXT,
            model_used TEXT NOT NULL,
            predicted_winner TEXT NOT NULL,
            suggested_score TEXT NOT NULL,
            team1_win_prob REAL NOT NULL,
            draw_prob REAL NOT NULL,
            team2_win_prob REAL NOT NULL,
            team1_xg REAL,
            team2_xg REAL
        )
        """
    )

    # 3. Bảng lưu độ chính xác và chỉ số đánh giá các mô hình ML
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS model_metrics (
            model_name TEXT PRIMARY KEY,
            accuracy REAL,
            precision_score REAL,
            recall_score REAL,
            f1_score REAL,
            is_best INTEGER DEFAULT 0
        )
        """
    )

    # Nạp dữ liệu từ Data/fifa.csv nếu bảng matches đang trống
    cur.execute("SELECT COUNT(*) FROM matches")
    if cur.fetchone()[0] == 0 and os.path.exists(DATA_CSV_PATH):
        raw_df = pd.read_csv(DATA_CSV_PATH)
        df = clean_fifa_dataframe(raw_df)
        rows_to_insert = []
        for idx, row in df.iterrows():
            rows_to_insert.append(
                (
                    int(row.get("match_id", idx + 1)),
                    int(row["world_cup_year"]),
                    str(row.get("host_country", "")),
                    str(row.get("date", "")),
                    str(row.get("stage", "Group Stage")),
                    str(row.get("group", "Knockout")),
                    str(row["team1"]),
                    str(row["team2"]),
                    int(row["total_goals_team1"]),
                    int(row["total_goals_team2"]),
                    str(row.get("winner", "")),
                    str(row.get("result_method", "Normal Time")),
                    str(row.get("stadium", "")),
                    str(row.get("city", "")),
                )
            )
        cur.executemany(
            """
            INSERT OR REPLACE INTO matches (
                match_id, world_cup_year, host_country, date, stage, group_name,
                team1, team2, goals_team1, goals_team2, winner, result_method, stadium, city
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )

    # Đồng bộ bảng model_metrics từ saved_models/model_bundle.pkl
    if os.path.exists(BUNDLE_PATH):
        bundle = joblib.load(BUNDLE_PATH)
        metrics = bundle.get("model_metrics", {})
        best_name = bundle.get("best_model_name", "XGBoost")
        if metrics:
            cur.execute("DELETE FROM model_metrics")
            for m_name, m_vals in metrics.items():
                cur.execute(
                    """
                    INSERT INTO model_metrics (model_name, accuracy, precision_score, recall_score, f1_score, is_best)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m_name,
                        m_vals.get("accuracy", 0.0),
                        m_vals.get("precision", 0.0),
                        m_vals.get("recall", 0.0),
                        m_vals.get("f1_score", 0.0),
                        1 if m_name == best_name else 0,
                    ),
                )

    conn.commit()
    conn.close()


def save_prediction_to_db(pred_result: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    probs = pred_result["probabilities"]
    xg = pred_result["expected_goals"]

    cur.execute(
        """
        INSERT INTO predictions_history (
            created_at, team1, team2, world_cup_year, stage, stadium,
            model_used, predicted_winner, suggested_score,
            team1_win_prob, draw_prob, team2_win_prob, team1_xg, team2_xg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now_str,
            pred_result["team1"],
            pred_result["team2"],
            pred_result["world_cup_year"],
            pred_result["stage"],
            pred_result["stadium"],
            pred_result["model_used"],
            pred_result["predicted_winner"],
            xg["suggested_score"],
            probs["team1_win"],
            probs["draw"],
            probs["team2_win"],
            xg["team1_xg"],
            xg["team2_xg"],
        ),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_prediction_history(limit: int = 20) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM predictions_history ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_prediction(pred_id: int | None = None):
    conn = get_connection()
    cur = conn.cursor()
    if pred_id is None:
        cur.execute("DELETE FROM predictions_history")
    else:
        cur.execute("DELETE FROM predictions_history WHERE id = ?", (pred_id,))
    conn.commit()
    conn.close()


def get_team_summary(team_name: str) -> dict:
    """Truy vấn thống kê tổng hợp của 1 đội tuyển từ bảng matches trong SQLite."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT world_cup_year, stage, team1, team2, goals_team1, goals_team2
        FROM matches
        WHERE team1 = ? OR team2 = ?
        ORDER BY world_cup_year DESC, match_id DESC
        """,
        (team_name, team_name),
    )
    rows = cur.fetchall()
    conn.close()

    played = len(rows)
    wins, draws, losses = 0, 0, 0
    goals_for, goals_against = 0, 0
    years_played = set()
    finals_reached = 0

    for r in rows:
        years_played.add(r["world_cup_year"])
        if str(r["stage"]).lower() == "final":
            finals_reached += 1
        if r["team1"] == team_name:
            gf, ga = int(r["goals_team1"]), int(r["goals_team2"])
        else:
            gf, ga = int(r["goals_team2"]), int(r["goals_team1"])

        goals_for += gf
        goals_against += ga
        if gf > ga:
            wins += 1
        elif gf < ga:
            losses += 1
        else:
            draws += 1

    win_rate = round((wins / played) * 100, 1) if played > 0 else 0.0
    avg_gf = round(goals_for / played, 2) if played > 0 else 0.0
    avg_ga = round(goals_against / played, 2) if played > 0 else 0.0

    return {
        "team": team_name,
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "win_rate": win_rate,
        "avg_goals_for": avg_gf,
        "avg_goals_against": avg_ga,
        "tournaments": len(years_played),
        "finals_reached": finals_reached,
    }


def get_db_overview() -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM matches")
    total_matches = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT world_cup_year) FROM matches")
    total_tournaments = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM predictions_history")
    total_predictions = cur.fetchone()[0]
    cur.execute("SELECT * FROM model_metrics ORDER BY accuracy DESC")
    metrics = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "total_matches": total_matches,
        "total_tournaments": total_tournaments,
        "total_predictions": total_predictions,
        "model_metrics": metrics,
    }


if __name__ == "__main__":
    init_db()
    print(f"Đã khởi tạo thành công cơ sở dữ liệu tại: {DB_PATH}")
