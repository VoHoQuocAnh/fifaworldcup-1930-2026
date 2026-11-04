import argparse
import difflib
import math
import os
import sys
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

_RESOURCE_CACHE = None


def load_resources():
    global _RESOURCE_CACHE
    if _RESOURCE_CACHE is not None:
        return _RESOURCE_CACHE

    if not os.path.exists(BEST_MODEL_PATH):
        raise FileNotFoundError(
            f"Chưa tìm thấy mô hình tại '{BEST_MODEL_PATH}'. Hãy chạy 'python Main.py' trước!"
        )
    best_model = joblib.load(BEST_MODEL_PATH)
    bundle = joblib.load(BUNDLE_PATH) if os.path.exists(BUNDLE_PATH) else {}
    df = clean_fifa_dataframe(pd.read_csv(DATA_PATH))
    all_teams = sorted(set(df["team1"].dropna()).union(set(df["team2"].dropna())))
    _RESOURCE_CACHE = (best_model, bundle, df, all_teams)
    return _RESOURCE_CACHE


def _poisson_pmf(k: int, lam: float) -> float:
    lam = max(0.05, float(lam))
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def compute_poisson_scorelines(xg1: float, xg2: float, max_goals: int = 4) -> dict:
    """
    Tính ma trận xác suất tỉ số chính xác (Poisson Distribution 5x5)
    từ số bàn thắng kỳ vọng xG của 2 đội.
    """
    matrix = []
    flat_scores = []
    total_prob = 0.0

    for g1 in range(max_goals + 1):
        row = []
        p1 = _poisson_pmf(g1, xg1)
        for g2 in range(max_goals + 1):
            p2 = _poisson_pmf(g2, xg2)
            p_joint = p1 * p2
            total_prob += p_joint
            row.append(p_joint)
        matrix.append(row)

    norm = total_prob if total_prob > 0 else 1.0
    normalized_matrix = []
    for g1 in range(max_goals + 1):
        norm_row = []
        for g2 in range(max_goals + 1):
            pct = round((matrix[g1][g2] / norm) * 100, 1)
            norm_row.append(pct)
            outcome_type = "t1" if g1 > g2 else ("t2" if g2 > g1 else "draw")
            flat_scores.append(
                {
                    "score": f"{g1} - {g2}",
                    "g1": g1,
                    "g2": g2,
                    "prob": pct,
                    "type": outcome_type,
                }
            )
        normalized_matrix.append(norm_row)

    flat_scores.sort(key=lambda x: x["prob"], reverse=True)
    return {
        "matrix": normalized_matrix,
        "top_scores": flat_scores[:6],
        "max_goals": max_goals,
    }


def build_explainable_ai(
    df: pd.DataFrame,
    t1: str,
    t2: str,
    stage: str,
    host_country: str,
    p_win: float,
    p_draw: float,
    p_loss: float,
    xg1: float,
    xg2: float,
    h2h: dict,
) -> dict:
    """
    Giải thích lý do mô hình AI đưa ra quyết định dự đoán (Explainable AI - XAI)
    và sinh bản tin nhận định chiến thuật tự động.
    """
    m1_df = df[(df["team1"] == t1) | (df["team2"] == t1)]
    m2_df = df[(df["team1"] == t2) | (df["team2"] == t2)]

    def _quick_stats(sub_df, team):
        total = len(sub_df)
        if total == 0:
            return {"played": 0, "win_rate": 30.0, "avg_gf": 1.1}
        wins = 0
        gf = 0
        for _, r in sub_df.iterrows():
            g_a = int(r["total_goals_team1"])
            g_b = int(r["total_goals_team2"])
            if r["team1"] == team:
                gf += g_a
                if g_a > g_b:
                    wins += 1
            else:
                gf += g_b
                if g_b > g_a:
                    wins += 1
        return {
            "played": total,
            "win_rate": round((wins / total) * 100, 1),
            "avg_gf": round(gf / total, 2),
        }

    st1 = _quick_stats(m1_df, t1)
    st2 = _quick_stats(m2_df, t2)

    wr_diff = round(st1["win_rate"] - st2["win_rate"], 1)
    xg_diff = round(xg1 - xg2, 2)
    exp_diff = st1["played"] - st2["played"]

    factors = []

    # 1. Yếu tố Tỉ lệ thắng lịch sử
    if abs(wr_diff) >= 2.0:
        fav = t1 if wr_diff > 0 else t2
        factors.append(
            {
                "icon": "📈",
                "title": "Hiệu suất Thắng Lịch sử (Historical Win Rate)",
                "impact": f"+{abs(wr_diff)}% nghiêng về {fav}",
                "favor": "t1" if wr_diff > 0 else "t2",
                "weight": min(100, int(45 + abs(wr_diff) * 1.4)),
                "desc": f"{t1} có tỉ lệ thắng {st1['win_rate']}% ({st1['played']} trận) so với {st2['win_rate']}% ({st2['played']} trận) của {t2}.",
            }
        )
    else:
        factors.append(
            {
                "icon": "⚖️",
                "title": "Hiệu suất Thắng Cân Bằng",
                "impact": f"Chênh lệch chỉ {abs(wr_diff)}%",
                "favor": "neutral",
                "weight": 50,
                "desc": f"Hai đội có tỉ lệ thắng lịch sử rất sát nhau ({st1['win_rate']}% vs {st2['win_rate']}%).",
            }
        )

    # 2. Yếu tố Bàn thắng kỳ vọng (xG Offensive Power)
    if abs(xg_diff) >= 0.12:
        fav_xg = t1 if xg_diff > 0 else t2
        factors.append(
            {
                "icon": "🎯",
                "title": "Sức mạnh Tấn công & Bàn thắng Kỳ vọng (xG)",
                "impact": f"+{abs(xg_diff)} xG cho {fav_xg}",
                "favor": "t1" if xg_diff > 0 else "t2",
                "weight": min(100, int(45 + abs(xg_diff) * 45)),
                "desc": f"Mô hình Ridge Regression dự báo {t1} đạt {xg1} xG (TB {st1['avg_gf']} bàn/trận) so với {xg2} xG (TB {st2['avg_gf']} bàn/trận) của {t2}.",
            }
        )
    else:
        factors.append(
            {
                "icon": "🛡️",
                "title": "Thế trận Giằng co (Tight xG Margin)",
                "impact": f"xG sát nút ({xg1} vs {xg2})",
                "favor": "neutral",
                "weight": 52,
                "desc": f"Hiệu suất ghi bàn kỳ vọng của hai đội gần như tương đương ({xg1} và {xg2} bàn).",
            }
        )

    # 3. Kinh nghiệm đấu trường World Cup
    if abs(exp_diff) >= 8:
        fav_exp = t1 if exp_diff > 0 else t2
        factors.append(
            {
                "icon": "🏛️",
                "title": "Bản lĩnh & Kinh nghiệm World Cup",
                "impact": f"+{abs(exp_diff)} trận cho {fav_exp}",
                "favor": "t1" if exp_diff > 0 else "t2",
                "weight": min(95, int(40 + min(50, abs(exp_diff) * 0.8))),
                "desc": f"{fav_exp} sở hữu bề dày kinh nghiệm vượt trội tại các vòng chung kết ({max(st1['played'], st2['played'])} trận đã đấu).",
            }
        )

    # 4. Lịch sử đối đầu trực tiếp (H2H)
    if h2h["total"] > 0:
        if h2h["team1_wins"] != h2h["team2_wins"]:
            fav_h2h = t1 if h2h["team1_wins"] > h2h["team2_wins"] else t2
            w_cnt = max(h2h["team1_wins"], h2h["team2_wins"])
            factors.append(
                {
                    "icon": "⚔️",
                    "title": "Ưu thế Đối đầu Trực tiếp (Head-to-Head)",
                    "impact": f"{fav_h2h} thắng {w_cnt}/{h2h['total']} trận",
                    "favor": "t1" if h2h["team1_wins"] > h2h["team2_wins"] else "t2",
                    "weight": min(90, 50 + abs(h2h["team1_wins"] - h2h["team2_wins"]) * 15),
                    "desc": f"Trong {h2h['total']} lần chạm trán tại World Cup, {t1} thắng {h2h['team1_wins']}, hòa {h2h['draws']}, {t2} thắng {h2h['team2_wins']}.",
                }
            )
        else:
            factors.append(
                {
                    "icon": "🤝",
                    "title": "Lịch sử Đối đầu Cân tài Cân sức",
                    "impact": f"Bất phân thắng bại ({h2h['total']} trận)",
                    "favor": "neutral",
                    "weight": 50,
                    "desc": f"Hai đội từng gặp nhau {h2h['total']} lần tại World Cup với thành tích ngang ngửa ({h2h['team1_wins']} thắng - {h2h['draws']} hòa - {h2h['team2_wins']} thua).",
                }
            )

    # 5. Lợi thế sân nhà (Host Advantage)
    t1_host = str(t1).lower() in str(host_country).lower() or (
        t1 == "USA" and "united states" in str(host_country).lower()
    )
    t2_host = str(t2).lower() in str(host_country).lower() or (
        t2 == "USA" and "united states" in str(host_country).lower()
    )
    if t1_host or t2_host:
        host_team = t1 if t1_host else t2
        factors.append(
            {
                "icon": "🏟️",
                "title": "Lợi thế Quốc gia Chủ nhà (Host Nation Boost)",
                "impact": f"Sân nhà {host_team}",
                "favor": "t1" if t1_host else "t2",
                "weight": 78,
                "desc": f"{host_team} thi đấu với tư cách đồng chủ nhà ({host_country}), nhận lợi thế lớn từ khán giả và điều kiện sân bãi.",
            }
        )

    # Kịch bản đá luân lưu (nếu là vòng Knockout)
    is_knockout = "group" not in str(stage).lower()
    penalty_info = None
    if is_knockout:
        # Tính xác suất thắng luân lưu dựa trên kinh nghiệm + tỉ lệ thắng
        pen_score1 = 50.0 + (st1["played"] - st2["played"]) * 0.12 + (st1["win_rate"] - st2["win_rate"]) * 0.18
        pen_prob1 = round(min(72.0, max(28.0, pen_score1)), 1)
        pen_prob2 = round(100.0 - pen_prob1, 1)
        penalty_info = {
            "enabled": True,
            "draw_trigger_prob": round(p_draw * 100, 1),
            "team1_pen_prob": pen_prob1,
            "team2_pen_prob": pen_prob2,
            "recommended_taker": t1 if pen_prob1 >= pen_prob2 else t2,
        }

    # Tổng hợp nhận định từ AI Bình luận viên
    win_pct = round(p_win * 100, 1)
    loss_pct = round(p_loss * 100, 1)
    draw_pct = round(p_draw * 100, 1)
    if p_win > p_loss and p_win > p_draw:
        commentary = (
            f"Dựa trên Pipeline học máy, {t1} được đánh giá nhỉnh hơn với {win_pct}% cơ hội giành chiến thắng "
            f"(so với {loss_pct}% của {t2}). Sức mạnh hàng công kỳ vọng đạt {xg1} xG cùng bề dày thành tích "
            f"({st1['win_rate']}% tỉ lệ thắng qua {st1['played']} trận WC) là điểm tựa giúp {t1} làm chủ thế trận tại {stage}."
        )
    elif p_loss > p_win and p_loss > p_draw:
        commentary = (
            f"Hệ thống AI nghiêng cán cân chiến thắng về phía {t2} với xác suất {loss_pct}% (trong khi {t1} là {win_pct}%). "
            f"Với chỉ số bàn thắng kỳ vọng {xg2} xG và hiệu suất thi đấu ổn định ({st2['win_rate']}% thắng tại WC), "
            f"{t2} có nhiều phương án khoan thủng hàng phòng ngự đối phương."
        )
    else:
        commentary = (
            f"Đây là cuộc đối đầu cực kỳ cân tài cân sức khi xác suất Hòa lên tới {draw_pct}% "
            f"({t1} {win_pct}% - {t2} {loss_pct}%). Chỉ số bàn thắng kỳ vọng sát nút ({xg1} vs {xg2} xG) "
            f"báo hiệu một thế trận chặt chẽ và có thể phải phân định thắng thua bằng hiệp phụ hoặc loạt sút luân lưu."
        )

    return {
        "factors": factors[:4],
        "commentary": commentary,
        "penalty_shootout": penalty_info,
    }


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
    poisson_data = compute_poisson_scorelines(xg1, xg2, max_goals=4)
    xai_data = build_explainable_ai(
        df=df,
        t1=t1,
        t2=t2,
        stage=stage,
        host_country=host_country,
        p_win=p_win,
        p_draw=p_draw,
        p_loss=p_loss,
        xg1=xg1,
        xg2=xg2,
        h2h=h2h,
    )

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
        "poisson_scorelines": poisson_data,
        "explainable_ai": xai_data,
        "council_votes": council_votes,
        "head_to_head": h2h,
    }


def predict_batch_matches(
    matches_spec: list[dict],
    model_name: str | None = None,
    monte_carlo: bool = False,
) -> list[dict]:
    """
    Dự đoán hàng loạt trận đấu cùng lúc (Batch Vectorized Inference)
    phục vụ giả lập toàn bộ Vòng Bảng & Vòng Knockout World Cup 2026 cực nhanh.
    """
    if not matches_spec:
        return []

    best_model, bundle, _, all_teams = load_resources()
    all_models = bundle.get("all_models", {})
    active_model = (
        all_models[model_name]
        if (model_name and model_name in all_models)
        else best_model
    )
    gm1 = bundle.get("goal_model_team1")

    fwd_rows = []
    rev_rows = []
    cleaned_teams = []

    for m in matches_spec:
        t1 = match_team_name(m["team1"], all_teams)
        t2 = match_team_name(m["team2"], all_teams)
        cleaned_teams.append((t1, t2))
        stg = m.get("stage", "Group Stage")
        grp = m.get("group", "Group A" if stg == "Group Stage" else "Knockout")
        yr = int(m.get("world_cup_year", 2026))
        host = m.get("host_country", "Canada, Mexico, United States")
        std = m.get("stadium", "MetLife Stadium")

        fwd_rows.append(
            {
                "world_cup_year": yr,
                "team1": t1,
                "team2": t2,
                "stage": stg,
                "group": grp,
                "host_country": host,
                "stadium": std,
            }
        )
        rev_rows.append(
            {
                "world_cup_year": yr,
                "team1": t2,
                "team2": t1,
                "stage": stg,
                "group": grp,
                "host_country": host,
                "stadium": std,
            }
        )

    fwd_df = pd.DataFrame(fwd_rows)
    rev_df = pd.DataFrame(rev_rows)

    probs_fwd = active_model.predict_proba(fwd_df)
    probs_rev = active_model.predict_proba(rev_df)

    g1_preds = gm1.predict(fwd_df) if gm1 is not None else np.full(len(matches_spec), 1.35)
    g2_preds = gm1.predict(rev_df) if gm1 is not None else np.full(len(matches_spec), 1.15)

    results = []
    rng = np.random.default_rng()

    for i, m in enumerate(matches_spec):
        t1, t2 = cleaned_teams[i]
        pf = probs_fwd[i]
        pr = probs_rev[i]
        p_loss = float((pf[0] + pr[2]) / 2.0)
        p_draw = float((pf[1] + pr[1]) / 2.0)
        p_win = float((pf[2] + pr[0]) / 2.0)
        tot = p_win + p_draw + p_loss
        p_win, p_draw, p_loss = p_win / tot, p_draw / tot, p_loss / tot

        g1_raw = max(0.2, float(g1_preds[i]))
        g2_raw = max(0.2, float(g2_preds[i]))
        tot_xg = max(0.8, g1_raw + g2_raw)
        xg1 = round(0.5 * g1_raw + 0.5 * (tot_xg * (p_win + 0.5 * p_draw)), 2)
        xg2 = round(0.5 * g2_raw + 0.5 * (tot_xg * (p_loss + 0.5 * p_draw)), 2)

        if monte_carlo:
            # Chế độ Monte Carlo: Lấy mẫu ngẫu nhiên theo xác suất thực tế của AI
            pred_label = int(rng.choice([0, 1, 2], p=[p_loss, p_draw, p_win]))
            s1 = int(rng.poisson(max(0.3, xg1)))
            s2 = int(rng.poisson(max(0.3, xg2)))
            if pred_label == 2 and s1 <= s2:
                s1 = s2 + 1
            elif pred_label == 0 and s2 <= s1:
                s2 = s1 + 1
            elif pred_label == 1:
                s1 = s2 = max(0, int(round((s1 + s2) / 2)))
        else:
            # Chế độ AI Chuẩn (Deterministic): Chọn phương án xác suất cao nhất
            pred_label = int(np.argmax([p_loss, p_draw, p_win]))
            s1 = max(0, int(round(xg1)))
            s2 = max(0, int(round(xg2)))
            if pred_label == 2 and s1 <= s2:
                s1 = s2 + 1
            elif pred_label == 0 and s2 <= s1:
                s2 = s1 + 1
            elif pred_label == 1 and s1 != s2:
                s1 = s2 = max(1, int(round((xg1 + xg2) / 2)))

        # Nếu là vòng loại trực tiếp (Knockout) và tỉ số Hòa -> phân định thắng thua (Hiệp phụ / Penalty)
        is_ko = m.get("stage", "Group Stage") != "Group Stage"
        pen_winner = None
        if is_ko and s1 == s2:
            if monte_carlo:
                t1_adv = p_win / max(0.01, p_win + p_loss)
                pen_winner = t1 if rng.random() < t1_adv else t2
            else:
                pen_winner = t1 if (p_win > p_loss or (p_win == p_loss and xg1 >= xg2)) else t2

        winner = (
            t1
            if s1 > s2
            else (t2 if s2 > s1 else (pen_winner if pen_winner else "Draw"))
        )

        results.append(
            {
                "team1": m["team1"],
                "team2": m["team2"],
                "score1": s1,
                "score2": s2,
                "xg1": xg1,
                "xg2": xg2,
                "prob1": round(p_win * 100, 1),
                "prob_draw": round(p_draw * 100, 1),
                "prob2": round(p_loss * 100, 1),
                "winner": winner,
                "penalty_winner": pen_winner,
            }
        )

    return results


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
