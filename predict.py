import argparse
import os
import sys
import difflib
import joblib
import numpy as np
import pandas as pd

from Models.preprocessor import clean_fifa_dataframe

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Data", "fifa.csv")
BEST_MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "best_model.pkl")
BUNDLE_PATH = os.path.join(BASE_DIR, "saved_models", "model_bundle.pkl")

LABEL_MAP = {
    2: "THẮNG (Đội 1 thắng)",
    1: "HÒA (Hai đội hòa)",
    0: "THUA (Đội 2 thắng)",
}


def load_resources():
    if not os.path.exists(BEST_MODEL_PATH):
        raise FileNotFoundError(
            f"Chưa tìm thấy mô hình tại '{BEST_MODEL_PATH}'. Hãy chạy 'python Main.py' trước!"
        )
    best_model = joblib.load(BEST_MODEL_PATH)
    bundle = joblib.load(BUNDLE_PATH) if os.path.exists(BUNDLE_PATH) else {}
    df = clean_fifa_dataframe(pd.read_csv(DATA_PATH))
    all_teams = sorted(set(df["team1"].dropna()).union(set(df["team2"].dropna())))
    return best_model, bundle, df, all_teams


def match_team_name(user_input: str, all_teams: list[str]) -> str:
    """Tìm tên đội bóng khớp nhất (không phân biệt hoa thường hoặc gợi ý gần đúng)."""
    clean_in = user_input.strip()
    for t in all_teams:
        if t.lower() == clean_in.lower():
            return t
    matches = difflib.get_close_matches(clean_in, all_teams, n=1, cutoff=0.5)
    if matches:
        return matches[0]
    return clean_in


def get_head_to_head(df: pd.DataFrame, team1: str, team2: str) -> dict:
    """Thống kê lịch sử đối đầu giữa 2 đội tại các kỳ World Cup."""
    cond = ((df["team1"] == team1) & (df["team2"] == team2)) | (
        (df["team1"] == team2) & (df["team2"] == team1)
    )
    h2h_df = df[cond].copy()
    t1_wins, draws, t2_wins = 0, 0, 0
    recent_matches = []

    for _, row in h2h_df.sort_values("world_cup_year", ascending=False).iterrows():
        g1 = int(row["total_goals_team1"])
        g2 = int(row["total_goals_team2"])
        if row["team1"] == team1:
            s1, s2 = g1, g2
        else:
            s1, s2 = g2, g1

        if s1 > s2:
            t1_wins += 1
        elif s1 < s2:
            t2_wins += 1
        else:
            draws += 1

        recent_matches.append(
            {
                "year": int(row["world_cup_year"]),
                "stage": str(row["stage"]),
                "team1": str(row["team1"]),
                "team2": str(row["team2"]),
                "score": f"{int(row['total_goals_team1'])} - {int(row['total_goals_team2'])}",
                "winner": str(row.get("winner", "")),
            }
        )

    return {
        "total": len(h2h_df),
        "team1_wins": t1_wins,
        "draws": draws,
        "team2_wins": t2_wins,
        "matches": recent_matches[:5],
    }


def predict_match(
    team1: str,
    team2: str,
    world_cup_year: int = 2026,
    stage: str = "Group Stage",
    group: str = "Group A",
    host_country: str = "Canada, Mexico, United States",
    stadium: str = "MetLife Stadium",
    model_name: str | None = None,
) -> dict:
    """Dự đoán kết quả trận đấu bất kỳ bằng Pipeline(OneHotEncoder + Model)."""
    best_model, bundle, df, all_teams = load_resources()

    t1 = match_team_name(team1, all_teams)
    t2 = match_team_name(team2, all_teams)

    if stage.lower() != "group stage" and group == "Group A":
        group = "Knockout"

    input_df = pd.DataFrame(
        [
            {
                "world_cup_year": int(world_cup_year),
                "team1": t1,
                "team2": t2,
                "stage": stage,
                "group": group,
                "host_country": host_country,
                "stadium": stadium,
            }
        ]
    )

    all_models = bundle.get("all_models", {})
    if model_name and model_name in all_models:
        active_model = all_models[model_name]
        used_model_name = model_name
    else:
        active_model = best_model
        used_model_name = bundle.get("best_model_name", "Best Model")

    # Để xác suất đối xứng khi đảo vị trí Đội 1 và Đội 2 trên sân trung lập,
    # kết hợp dự đoán xuôi (team1 vs team2) và ngược (team2 vs team1)
    reverse_df = input_df.copy()
    reverse_df["team1"] = t2
    reverse_df["team2"] = t1

    if hasattr(active_model, "predict_proba"):
        probs_fwd = active_model.predict_proba(input_df)[0]
        probs_rev = active_model.predict_proba(reverse_df)[0]
        # Lớp: 0 = Thua (Đội 2 thắng), 1 = Hòa, 2 = Thắng (Đội 1 thắng)
        p_loss = float((probs_fwd[0] + probs_rev[2]) / 2.0)
        p_draw = float((probs_fwd[1] + probs_rev[1]) / 2.0)
        p_win = float((probs_fwd[2] + probs_rev[0]) / 2.0)
        total_p = p_win + p_draw + p_loss
        p_win, p_draw, p_loss = p_win / total_p, p_draw / total_p, p_loss / total_p
        pred_label = int(np.argmax([p_loss, p_draw, p_win]))
    else:
        pred_label = int(active_model.predict(input_df)[0])
        p_win = 1.0 if pred_label == 2 else 0.0
        p_draw = 1.0 if pred_label == 1 else 0.0
        p_loss = 1.0 if pred_label == 0 else 0.0

    # Dự đoán số bàn thắng từ Linear Regression Pipeline kết hợp xác suất thắng/thua
    xg1, xg2 = 1.4, 1.1
    if "goal_model_team1" in bundle:
        gm1 = bundle["goal_model_team1"]
        g1_pred = max(0.2, float(gm1.predict(input_df)[0]))
        g2_pred = max(0.2, float(gm1.predict(reverse_df)[0]))
        total_xg = max(0.8, g1_pred + g2_pred)
        strength_t1 = p_win + 0.5 * p_draw
        strength_t2 = p_loss + 0.5 * p_draw
        xg1 = round(0.5 * g1_pred + 0.5 * (total_xg * strength_t1), 2)
        xg2 = round(0.5 * g2_pred + 0.5 * (total_xg * strength_t2), 2)
        if pred_label == 2 and xg1 <= xg2:
            xg1 = round(xg2 + 0.25, 2)
        elif pred_label == 0 and xg2 <= xg1:
            xg2 = round(xg1 + 0.25, 2)

    # Gợi ý tỉ số hợp lý nhất với kết quả phân loại
    score_t1 = max(0, int(round(xg1)))
    score_t2 = max(0, int(round(xg2)))
    if pred_label == 2 and score_t1 <= score_t2:
        score_t1 = score_t2 + 1
    elif pred_label == 0 and score_t2 <= score_t1:
        score_t2 = score_t1 + 1
    elif pred_label == 1 and score_t1 != score_t2:
        avg_g = max(1, int(round((xg1 + xg2) / 2)))
        score_t1 = score_t2 = avg_g

    winner_text = t1 if pred_label == 2 else (t2 if pred_label == 0 else "Hòa (Draw)")

    # Dự đoán từ toàn bộ các mô hình để so sánh
    council_votes = {}
    for m_name, m_pipe in all_models.items():
        if hasattr(m_pipe, "predict_proba"):
            pf = m_pipe.predict_proba(input_df)[0]
            pr = m_pipe.predict_proba(reverse_df)[0]
            mp_loss = (pf[0] + pr[2]) / 2.0
            mp_draw = (pf[1] + pr[1]) / 2.0
            mp_win = (pf[2] + pr[0]) / 2.0
            m_lbl = int(np.argmax([mp_loss, mp_draw, mp_win]))
        else:
            m_lbl = int(m_pipe.predict(input_df)[0])
            mp_win, mp_draw, mp_loss = (
                (1, 0, 0) if m_lbl == 2 else ((0, 1, 0) if m_lbl == 1 else (0, 0, 1))
            )
        council_votes[m_name] = {
            "label": m_lbl,
            "outcome": f"{t1} thắng"
            if m_lbl == 2
            else (f"{t2} thắng" if m_lbl == 0 else "Hòa"),
            "win_prob": round(float(mp_win) * 100, 1),
            "draw_prob": round(float(mp_draw) * 100, 1),
            "loss_prob": round(float(mp_loss) * 100, 1),
        }

    h2h = get_head_to_head(df, t1, t2)

    return {
        "team1": t1,
        "team2": t2,
        "world_cup_year": int(world_cup_year),
        "stage": stage,
        "group": group,
        "host_country": host_country,
        "stadium": stadium,
        "model_used": used_model_name,
        "prediction_code": pred_label,
        "prediction_text": LABEL_MAP[pred_label],
        "predicted_winner": winner_text,
        "probabilities": {
            "team1_win": round(p_win * 100, 1),
            "draw": round(p_draw * 100, 1),
            "team2_win": round(p_loss * 100, 1),
        },
        "expected_goals": {
            "team1_xg": xg1,
            "team2_xg": xg2,
            "suggested_score": f"{score_t1} - {score_t2}",
        },
        "council_votes": council_votes,
        "head_to_head": h2h,
    }


def render_bar(percent: float, width: int = 25) -> str:
    filled = int(round((percent / 100.0) * width))
    return "█" * filled + "░" * (width - filled)


def print_prediction_report(res: dict):
    t1, t2 = res["team1"], res["team2"]
    probs = res["probabilities"]
    xg = res["expected_goals"]
    h2h = res["head_to_head"]

    print("\n" + "═" * 64)
    print(f"⚽ DỰ ĐOÁN TRẬN ĐẤU FIFA WORLD CUP {res['world_cup_year']}")
    print("═" * 64)
    print(f"🏟️  Cặp đấu     : {t1.upper()}  vs  {t2.upper()}")
    print(f"🏆 Vòng đấu    : {res['stage']} ({res['group']})")
    print(f"📍 Sân vận động: {res['stadium']} ({res['host_country']})")
    print(f"🤖 Mô hình chính: {res['model_used']} (Pipeline OneHotEncoder + Model)")
    print("─" * 64)
    print(f"🎯 KẾT QUẢ DỰ ĐOÁN : {res['prediction_text']} -> [{res['predicted_winner']}]")
    print(
        f"🔢 TỈ SỐ KỲ VỌNG   : {t1} {xg['suggested_score']} {t2}  (xG: {xg['team1_xg']} - {xg['team2_xg']})"
    )
    print("─" * 64)
    print("📊 XÁC SUẤT CHI TIẾT:")
    print(
        f"  • {t1:18s} Thắng : {render_bar(probs['team1_win'])} {probs['team1_win']:5.1f}%"
    )
    print(
        f"  • {'Hòa (Draw)':18s}       : {render_bar(probs['draw'])} {probs['draw']:5.1f}%"
    )
    print(
        f"  • {t2:18s} Thắng : {render_bar(probs['team2_win'])} {probs['team2_win']:5.1f}%"
    )

    if res["council_votes"]:
        print("─" * 64)
        print("🗳️  Ý KIẾN HỘI ĐỒNG 5 MÔ HÌNH ML:")
        for m_name, vote in res["council_votes"].items():
            print(
                f"  - {m_name:20s}: {vote['outcome']:18s} "
                f"(Thắng {vote['win_prob']}% | Hòa {vote['draw_prob']}% | Thua {vote['loss_prob']}%)"
            )

    print("─" * 64)
    print(
        f"📜 LỊCH SỬ ĐỐI ĐẦU WORLD CUP ({h2h['total']} trận): "
        f"{t1} thắng {h2h['team1_wins']} | Hòa {h2h['draws']} | {t2} thắng {h2h['team2_wins']}"
    )
    for m in h2h["matches"]:
        print(
            f"  • WC {m['year']} ({m['stage']}): {m['team1']} {m['score']} {m['team2']}"
        )
    print("═" * 64 + "\n")


def interactive_cli():
    _, _, _, all_teams = load_resources()
    print("=" * 64)
    print("⚽ CHƯƠNG TRÌNH DỰ ĐOÁN KẾT QUẢ FIFA WORLD CUP (TERMINAL CLI)")
    print("=" * 64)
    print(f"Đã tải {len(all_teams)} đội tuyển quốc gia trong lịch sử World Cup.")
    print("Một số đội tiêu biểu: Brazil, Argentina, France, Germany, Spain, England,")
    print("Portugal, Netherlands, Italy, Croatia, Morocco, Japan, South Korea, USA...")
    print("(Nhấn Enter hoặc gõ 'q' để thoát)\n")

    while True:
        try:
            t1_in = input("👉 Nhập tên Đội 1 (VD: Brazil): ").strip()
            if not t1_in or t1_in.lower() in {"q", "quit", "exit"}:
                print("Cảm ơn bạn đã sử dụng chương trình dự đoán World Cup!")
                break

            t2_in = input("👉 Nhập tên Đội 2 (VD: France): ").strip()
            if not t2_in or t2_in.lower() in {"q", "quit", "exit"}:
                print("Cảm ơn bạn đã sử dụng chương trình dự đoán World Cup!")
                break

            stage_in = input(
                "👉 Vòng đấu [Mặc định: Group Stage / Final / Semi-final / Quarter-final]: "
            ).strip()
            if not stage_in:
                stage_in = "Group Stage"

            year_in = input("👉 Năm World Cup [Mặc định: 2026]: ").strip()
            year_val = int(year_in) if year_in.isdigit() else 2026

            result = predict_match(
                team1=t1_in,
                team2=t2_in,
                world_cup_year=year_val,
                stage=stage_in,
            )
            print_prediction_report(result)
        except KeyboardInterrupt:
            print("\nĐã thoát chương trình.")
            break
        except Exception as exc:
            print(f"⚠️ Lỗi khi dự đoán: {exc}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Dự đoán kết quả trận đấu FIFA World Cup bằng Pipeline ML."
    )
    parser.add_argument("--team1", type=str, help="Tên đội bóng 1 (VD: Argentina)")
    parser.add_argument("--team2", type=str, help="Tên đội bóng 2 (VD: France)")
    parser.add_argument(
        "--year", type=int, default=2026, help="Năm World Cup (Mặc định: 2026)"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="Final",
        help="Vòng đấu (VD: Group Stage, Round of 16, Quarter-final, Semi-final, Final)",
    )
    parser.add_argument(
        "--group", type=str, default="Group A", help="Bảng đấu (VD: Group A, Knockout)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="Canada, Mexico, United States",
        help="Quốc gia đăng cai",
    )
    parser.add_argument(
        "--stadium", type=str, default="MetLife Stadium", help="Sân vận động"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Tên mô hình cụ thể (XGBoost, Random Forest, KNN, Logistic Regression, Decision Tree)",
    )

    args = parser.parse_args()

    if args.team1 and args.team2:
        res = predict_match(
            team1=args.team1,
            team2=args.team2,
            world_cup_year=args.year,
            stage=args.stage,
            group=args.group,
            host_country=args.host,
            stadium=args.stadium,
            model_name=args.model,
        )
        print_prediction_report(res)
    else:
        interactive_cli()


if __name__ == "__main__":
    main()
