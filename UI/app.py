import os
import sys
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from predict import load_resources, predict_batch_matches, predict_match
from UI.database import (
    delete_prediction,
    get_connection,
    get_db_overview,
    get_prediction_history,
    get_team_summary,
    init_db,
    save_prediction_to_db,
)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# Mã ISO quốc kỳ chuẩn (hiển thị cờ màu sắc nét trên mọi trình duyệt Windows/macOS)
TEAM_ISO_CODES = {
    "Algeria": "dz",
    "Angola": "ao",
    "Argentina": "ar",
    "Australia": "au",
    "Austria": "at",
    "Belgium": "be",
    "Bolivia": "bo",
    "Bosnia & Herzegovina": "ba",
    "Bosnia and Herzegovina": "ba",
    "Brazil": "br",
    "Bulgaria": "bg",
    "Cameroon": "cm",
    "Canada": "ca",
    "Cape Verde": "cv",
    "Chile": "cl",
    "China": "cn",
    "China PR": "cn",
    "Colombia": "co",
    "Costa Rica": "cr",
    "Croatia": "hr",
    "Cuba": "cu",
    "Curaçao": "cw",
    "Czech Republic": "cz",
    "Czechoslovakia": "cz",
    "Denmark": "dk",
    "DR Congo": "cd",
    "Dutch East Indies": "id",
    "East Germany": "de",
    "Ecuador": "ec",
    "Egypt": "eg",
    "El Salvador": "sv",
    "England": "gb-eng",
    "France": "fr",
    "Germany": "de",
    "West Germany": "de",
    "Ghana": "gh",
    "Greece": "gr",
    "Haiti": "ht",
    "Honduras": "hn",
    "Hungary": "hu",
    "Iceland": "is",
    "Iran": "ir",
    "Iraq": "iq",
    "Israel": "il",
    "Italy": "it",
    "Ivory Coast": "ci",
    "Jamaica": "jm",
    "Japan": "jp",
    "Jordan": "jo",
    "Kuwait": "kw",
    "Mexico": "mx",
    "Morocco": "ma",
    "Netherlands": "nl",
    "New Zealand": "nz",
    "Nigeria": "ng",
    "North Korea": "kp",
    "Northern Ireland": "gb-nir",
    "Norway": "no",
    "Panama": "pa",
    "Paraguay": "py",
    "Peru": "pe",
    "Poland": "pl",
    "Portugal": "pt",
    "Qatar": "qa",
    "Republic of Ireland": "ie",
    "Romania": "ro",
    "Russia": "ru",
    "Soviet Union": "ru",
    "Saudi Arabia": "sa",
    "Scotland": "gb-sct",
    "Senegal": "sn",
    "Serbia": "rs",
    "Serbia and Montenegro": "rs",
    "Yugoslavia": "rs",
    "Slovakia": "sk",
    "Slovenia": "si",
    "South Africa": "za",
    "South Korea": "kr",
    "Spain": "es",
    "Sweden": "se",
    "Switzerland": "ch",
    "Togo": "tg",
    "Trinidad and Tobago": "tt",
    "Tunisia": "tn",
    "Turkey": "tr",
    "UAE": "ae",
    "United Arab Emirates": "ae",
    "Ukraine": "ua",
    "United States": "us",
    "USA": "us",
    "Uruguay": "uy",
    "Uzbekistan": "uz",
    "Wales": "gb-wls",
    "Zaire": "cd",
}

# Cấu trúc 12 bảng đấu FIFA World Cup 2026 đúng theo Poster mẫu (Ảnh 1)
WC2026_GROUPS = [
    {
        "group": "A",
        "side": "left",
        "color": "#00d66c",
        "text_dark": False,
        "teams": [
            {"name": "Mexico", "display": "MEXICO"},
            {"name": "South Africa", "display": "SOUTH AFRICA"},
            {"name": "South Korea", "display": "KOREA REPUBLIC"},
            {"name": "Czech Republic", "display": "CZECHIA"},
        ],
    },
    {
        "group": "B",
        "side": "left",
        "color": "#ee1d36",
        "text_dark": False,
        "teams": [
            {"name": "Canada", "display": "CANADA"},
            {"name": "Bosnia & Herzegovina", "display": "BOSNIA AND HERZEGOVINA"},
            {"name": "Qatar", "display": "QATAR"},
            {"name": "Switzerland", "display": "SWITZERLAND"},
        ],
    },
    {
        "group": "C",
        "side": "left",
        "color": "#ff8a00",
        "text_dark": False,
        "teams": [
            {"name": "Brazil", "display": "BRAZIL"},
            {"name": "Morocco", "display": "MOROCCO"},
            {"name": "Haiti", "display": "HAITI"},
            {"name": "Scotland", "display": "SCOTLAND"},
        ],
    },
    {
        "group": "D",
        "side": "left",
        "color": "#1d5bff",
        "text_dark": False,
        "teams": [
            {"name": "USA", "display": "USA"},
            {"name": "Paraguay", "display": "PARAGUAY"},
            {"name": "Australia", "display": "AUSTRALIA"},
            {"name": "Turkey", "display": "TÜRKIYE"},
        ],
    },
    {
        "group": "E",
        "side": "left",
        "color": "#5e17eb",
        "text_dark": False,
        "teams": [
            {"name": "Germany", "display": "GERMANY"},
            {"name": "Curaçao", "display": "CURAÇAO"},
            {"name": "Ivory Coast", "display": "CÔTE D'IVOIRE"},
            {"name": "Ecuador", "display": "ECUADOR"},
        ],
    },
    {
        "group": "F",
        "side": "left",
        "color": "#b8ff01",
        "text_dark": True,
        "teams": [
            {"name": "Netherlands", "display": "NETHERLANDS"},
            {"name": "Japan", "display": "JAPAN"},
            {"name": "Sweden", "display": "SWEDEN"},
            {"name": "Tunisia", "display": "TUNISIA"},
        ],
    },
    {
        "group": "G",
        "side": "right",
        "color": "#f25c93",
        "text_dark": False,
        "teams": [
            {"name": "Belgium", "display": "BELGIUM"},
            {"name": "Egypt", "display": "EGYPT"},
            {"name": "Iran", "display": "IR IRAN"},
            {"name": "New Zealand", "display": "NEW ZEALAND"},
        ],
    },
    {
        "group": "H",
        "side": "right",
        "color": "#4ae8c2",
        "text_dark": True,
        "teams": [
            {"name": "Spain", "display": "SPAIN"},
            {"name": "Cape Verde", "display": "CABO VERDE"},
            {"name": "Saudi Arabia", "display": "SAUDI ARABIA"},
            {"name": "Uruguay", "display": "URUGUAY"},
        ],
    },
    {
        "group": "I",
        "side": "right",
        "color": "#9b30ff",
        "text_dark": False,
        "teams": [
            {"name": "France", "display": "FRANCE"},
            {"name": "Senegal", "display": "SENEGAL"},
            {"name": "Iraq", "display": "IRAQ"},
            {"name": "Norway", "display": "NORWAY"},
        ],
    },
    {
        "group": "J",
        "side": "right",
        "color": "#2f6e7e",
        "text_dark": False,
        "teams": [
            {"name": "Argentina", "display": "ARGENTINA"},
            {"name": "Algeria", "display": "ALGERIA"},
            {"name": "Austria", "display": "AUSTRIA"},
            {"name": "Jordan", "display": "JORDAN"},
        ],
    },
    {
        "group": "K",
        "side": "right",
        "color": "#ff4500",
        "text_dark": False,
        "teams": [
            {"name": "Portugal", "display": "PORTUGAL"},
            {"name": "DR Congo", "display": "CONGO DR"},
            {"name": "Uzbekistan", "display": "UZBEKISTAN"},
            {"name": "Colombia", "display": "COLOMBIA"},
        ],
    },
    {
        "group": "L",
        "side": "right",
        "color": "#38b6ff",
        "text_dark": True,
        "teams": [
            {"name": "England", "display": "ENGLAND"},
            {"name": "Croatia", "display": "CROATIA"},
            {"name": "Ghana", "display": "GHANA"},
            {"name": "Panama", "display": "PANAMA"},
        ],
    },
]


def get_flag_url(team_name: str) -> str:
    code = TEAM_ISO_CODES.get(team_name, "un")
    return f"https://flagcdn.com/w80/{code}.png"


def ensure_seeded_predictions():
    init_db()
    history = get_prediction_history(limit=5)
    if not history:
        showcase = [
            ("Argentina", "France", 2026, "Final", "MetLife Stadium"),
            ("Brazil", "Morocco", 2026, "Group Stage", "MetLife Stadium"),
            ("Spain", "England", 2026, "Semi-final", "SoFi Stadium"),
        ]
        for t1, t2, yr, stg, std in showcase:
            res = predict_match(
                team1=t1,
                team2=t2,
                world_cup_year=yr,
                stage=stg,
                stadium=std,
            )
            save_prediction_to_db(res)


ensure_seeded_predictions()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/metadata", methods=["GET"])
def api_metadata():
    _, bundle, df, all_teams = load_resources()
    stages = [
        "Group Stage",
        "Round of 32",
        "Round of 16",
        "Quarter-final",
        "Semi-final",
        "Third Place Play-off",
        "Final",
    ]
    stadiums_2026 = sorted(
        df[df["world_cup_year"] == 2026]["stadium"].dropna().unique().tolist()
    )
    if not stadiums_2026:
        stadiums_2026 = [
            "MetLife Stadium",
            "Estadio Azteca",
            "SoFi Stadium",
            "AT&T Stadium",
        ]

    years = sorted(
        df["world_cup_year"].dropna().unique().astype(int).tolist(), reverse=True
    )
    db_info = get_db_overview()

    teams_list = [
        {
            "name": t,
            "iso": TEAM_ISO_CODES.get(t, "un"),
            "flag_url": get_flag_url(t),
        }
        for t in all_teams
    ]

    groups_enriched = []
    for g in WC2026_GROUPS:
        g_copy = dict(g)
        g_copy["teams"] = [
            {
                "name": item["name"],
                "display": item["display"],
                "iso": TEAM_ISO_CODES.get(item["name"], "un"),
                "flag_url": get_flag_url(item["name"]),
            }
            for item in g["teams"]
        ]
        groups_enriched.append(g_copy)

    return jsonify(
        {
            "teams": teams_list,
            "iso_map": TEAM_ISO_CODES,
            "wc2026_groups": groups_enriched,
            "stages": stages,
            "stadiums": stadiums_2026,
            "years": years,
            "best_model_name": bundle.get("best_model_name", "XGBoost"),
            "best_accuracy": bundle.get("best_accuracy", 55.61),
            "db_overview": db_info,
        }
    )


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True) or {}
    team1 = data.get("team1", "Argentina")
    team2 = data.get("team2", "France")
    year = int(data.get("world_cup_year", 2026))
    stage = data.get("stage", "Final")
    group = data.get("group", "Group A")
    host_country = data.get("host_country", "Canada, Mexico, United States")
    stadium = data.get("stadium", "MetLife Stadium")
    model_name = data.get("model_name") or None
    save_to_db = data.get("save_to_db", True)

    if team1 == team2:
        return jsonify({"error": "Vui lòng chọn 2 đội tuyển khác nhau để dự đoán!"}), 400

    res = predict_match(
        team1=team1,
        team2=team2,
        world_cup_year=year,
        stage=stage,
        group=group,
        host_country=host_country,
        stadium=stadium,
        model_name=model_name,
    )

    if save_to_db:
        save_prediction_to_db(res)

    res["team1_flag_url"] = get_flag_url(res["team1"])
    res["team2_flag_url"] = get_flag_url(res["team2"])
    res["team1_stats"] = get_team_summary(res["team1"])
    res["team2_stats"] = get_team_summary(res["team2"])
    res["history"] = get_prediction_history(limit=15)
    return jsonify(res)


@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    if request.method == "DELETE":
        delete_prediction(None)
        return jsonify({"status": "cleared", "history": []})
    return jsonify({"history": get_prediction_history(limit=20)})


@app.route("/api/history/<int:pred_id>", methods=["DELETE"])
def api_delete_history_item(pred_id: int):
    delete_prediction(pred_id)
    return jsonify({"status": "deleted", "history": get_prediction_history(limit=20)})


@app.route("/api/matches", methods=["GET"])
def api_matches():
    year = request.args.get("year", type=int)
    team = request.args.get("team", type=str)
    stage = request.args.get("stage", type=str)
    limit = request.args.get("limit", default=30, type=int)

    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM matches WHERE 1=1"
    params = []
    if year:
        query += " AND world_cup_year = ?"
        params.append(year)
    if team:
        query += " AND (team1 = ? OR team2 = ?)"
        params.extend([team, team])
    if stage:
        query += " AND stage = ?"
        params.append(stage)

    query += " ORDER BY world_cup_year DESC, match_id DESC LIMIT ?"
    params.append(limit)
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    for r in rows:
        r["team1_flag_url"] = get_flag_url(r["team1"])
        r["team2_flag_url"] = get_flag_url(r["team2"])
    return jsonify({"matches": rows})


@app.route("/api/simulate_tournament", methods=["POST"])
def api_simulate_tournament():
    """
    Giả lập toàn bộ Vòng Bảng (12 bảng A-L, 72 trận) và Nhánh đấu Knockout
    (Vòng 1/8 -> Tứ kết -> Bán kết -> Tranh Hạng 3 -> Chung kết) của FIFA World Cup 2026.
    """
    data = request.get_json(force=True) or {}
    model_name = data.get("model_name") or None
    mode = data.get("mode", "ai")  # "ai" (Deterministic) hoặc "montecarlo" (Ngẫu nhiên theo xác suất)
    monte_carlo = mode == "montecarlo"

    # 1. Tạo danh sách 72 trận vòng bảng (6 trận / bảng x 12 bảng)
    group_specs = []
    group_meta = []
    for g in WC2026_GROUPS:
        g_letter = g["group"]
        t_list = [item["name"] for item in g["teams"]]
        pairs = [
            (t_list[0], t_list[1]),
            (t_list[2], t_list[3]),
            (t_list[0], t_list[2]),
            (t_list[1], t_list[3]),
            (t_list[0], t_list[3]),
            (t_list[1], t_list[2]),
        ]
        for t1, t2 in pairs:
            group_specs.append(
                {
                    "team1": t1,
                    "team2": t2,
                    "stage": "Group Stage",
                    "group": f"Group {g_letter}",
                    "world_cup_year": 2026,
                }
            )
            group_meta.append(g_letter)

    group_preds = predict_batch_matches(
        group_specs, model_name=model_name, monte_carlo=monte_carlo
    )

    # 2. Tính bảng xếp hạng cho từng bảng A - L
    standings_by_group = {}
    matches_by_group = {g["group"]: [] for g in WC2026_GROUPS}
    total_goals_tournament = 0
    team_goals_counter = {}

    for g in WC2026_GROUPS:
        g_letter = g["group"]
        standings_by_group[g_letter] = {}
        for item in g["teams"]:
            t_name = item["name"]
            standings_by_group[g_letter][t_name] = {
                "team": t_name,
                "display": item["display"],
                "flag_url": get_flag_url(t_name),
                "group": g_letter,
                "played": 0,
                "w": 0,
                "d": 0,
                "l": 0,
                "gf": 0,
                "ga": 0,
                "gd": 0,
                "pts": 0,
                "xg_total": 0.0,
            }

    for idx, res in enumerate(group_preds):
        g_letter = group_meta[idx]
        t1, t2 = res["team1"], res["team2"]
        s1, s2 = int(res["score1"]), int(res["score2"])
        total_goals_tournament += s1 + s2
        team_goals_counter[t1] = team_goals_counter.get(t1, 0) + s1
        team_goals_counter[t2] = team_goals_counter.get(t2, 0) + s2

        st1 = standings_by_group[g_letter][t1]
        st2 = standings_by_group[g_letter][t2]
        st1["played"] += 1
        st2["played"] += 1
        st1["gf"] += s1
        st1["ga"] += s2
        st2["gf"] += s2
        st2["ga"] += s1
        st1["gd"] = st1["gf"] - st1["ga"]
        st2["gd"] = st2["gf"] - st2["ga"]
        st1["xg_total"] = round(st1["xg_total"] + res["xg1"], 2)
        st2["xg_total"] = round(st2["xg_total"] + res["xg2"], 2)

        if s1 > s2:
            st1["w"] += 1
            st1["pts"] += 3
            st2["l"] += 1
        elif s2 > s1:
            st2["w"] += 1
            st2["pts"] += 3
            st1["l"] += 1
        else:
            st1["d"] += 1
            st2["d"] += 1
            st1["pts"] += 1
            st2["pts"] += 1

        matches_by_group[g_letter].append(
            {
                "team1": t1,
                "team2": t2,
                "flag1": get_flag_url(t1),
                "flag2": get_flag_url(t2),
                "score": f"{s1} - {s2}",
                "winner": res["winner"],
            }
        )

    # Sắp xếp BXH từng bảng (Ưu tiên: Điểm -> Hiệu số -> Bàn thắng -> xG)
    groups_output = []
    group_winners = {}
    runners_up_pool = []

    for g in WC2026_GROUPS:
        g_letter = g["group"]
        table = list(standings_by_group[g_letter].values())
        table.sort(
            key=lambda x: (x["pts"], x["gd"], x["gf"], x["xg_total"]),
            reverse=True,
        )
        for rank_idx, row in enumerate(table):
            row["rank"] = rank_idx + 1
            row["qualified"] = rank_idx == 0  # Mặc định nhất bảng vào thẳng R16

        group_winners[g_letter] = table[0]
        runners_up_pool.append(table[1])
        groups_output.append(
            {
                "group": g_letter,
                "color": g["color"],
                "standings": table,
                "matches": matches_by_group[g_letter],
            }
        )

    # Lấy 4 đội Nhì bảng xuất sắc nhất cùng 12 đội Nhất bảng tạo thành 16 đội mạnh nhất (Round of 16)
    runners_up_pool.sort(
        key=lambda x: (x["pts"], x["gd"], x["gf"], x["xg_total"]),
        reverse=True,
    )
    best_runners = runners_up_pool[:4]
    best_runner_teams = {r["team"] for r in best_runners}
    for g_out in groups_output:
        for row in g_out["standings"]:
            if row["team"] in best_runner_teams:
                row["qualified"] = True

    # 3. Thiết lập 8 cặp đấu Vòng 1/8 (Round of 16) cân xứng 2 nhánh Trái - Phải
    r16_pairings = [
        (group_winners["A"]["team"], best_runners[0]["team"]),
        (group_winners["C"]["team"], group_winners["D"]["team"]),
        (group_winners["E"]["team"], group_winners["F"]["team"]),
        (group_winners["B"]["team"], best_runners[1]["team"]),
        (group_winners["G"]["team"], best_runners[2]["team"]),
        (group_winners["I"]["team"], group_winners["J"]["team"]),
        (group_winners["K"]["team"], group_winners["L"]["team"]),
        (group_winners["H"]["team"], best_runners[3]["team"]),
    ]

    def _run_ko_round(pairs, stage_name):
        nonlocal total_goals_tournament
        specs = [
            {
                "team1": p[0],
                "team2": p[1],
                "stage": stage_name,
                "group": "Knockout",
                "world_cup_year": 2026,
            }
            for p in pairs
        ]
        preds = predict_batch_matches(
            specs, model_name=model_name, monte_carlo=monte_carlo
        )
        round_matches = []
        winners = []
        losers = []
        for r in preds:
            t1, t2 = r["team1"], r["team2"]
            s1, s2 = int(r["score1"]), int(r["score2"])
            total_goals_tournament += s1 + s2
            team_goals_counter[t1] = team_goals_counter.get(t1, 0) + s1
            team_goals_counter[t2] = team_goals_counter.get(t2, 0) + s2
            w = r["winner"]
            l = t2 if w == t1 else t1
            winners.append(w)
            losers.append(l)
            round_matches.append(
                {
                    "stage": stage_name,
                    "team1": t1,
                    "team2": t2,
                    "flag1": get_flag_url(t1),
                    "flag2": get_flag_url(t2),
                    "score1": s1,
                    "score2": s2,
                    "xg1": r["xg1"],
                    "xg2": r["xg2"],
                    "prob1": r["prob1"],
                    "prob2": r["prob2"],
                    "winner": w,
                    "penalty_winner": r["penalty_winner"],
                }
            )
        return round_matches, winners, losers

    r16_matches, r16_winners, _ = _run_ko_round(r16_pairings, "Round of 16")
    qf_pairings = [
        (r16_winners[0], r16_winners[1]),
        (r16_winners[2], r16_winners[3]),
        (r16_winners[4], r16_winners[5]),
        (r16_winners[6], r16_winners[7]),
    ]
    qf_matches, qf_winners, _ = _run_ko_round(qf_pairings, "Quarter-final")

    sf_pairings = [
        (qf_winners[0], qf_winners[1]),
        (qf_winners[2], qf_winners[3]),
    ]
    sf_matches, sf_winners, sf_losers = _run_ko_round(sf_pairings, "Semi-final")

    third_matches, third_winners, _ = _run_ko_round(
        [(sf_losers[0], sf_losers[1])], "Third Place Play-off"
    )
    final_matches, final_winners, final_losers = _run_ko_round(
        [(sf_winners[0], sf_winners[1])], "Final"
    )

    champion = final_winners[0]
    runner_up = final_losers[0]
    third_place = third_winners[0]

    top_scorer_team = max(team_goals_counter.items(), key=lambda x: x[1]) if team_goals_counter else (champion, 14)

    return jsonify(
        {
            "mode": mode,
            "model_used": model_name or "XGBoost (Best Pipeline)",
            "groups": groups_output,
            "knockout": {
                "r16": r16_matches,
                "qf": qf_matches,
                "sf": sf_matches,
                "third_place": third_matches[0],
                "final": final_matches[0],
            },
            "summary": {
                "champion": champion,
                "champion_flag": get_flag_url(champion),
                "runner_up": runner_up,
                "runner_up_flag": get_flag_url(runner_up),
                "third_place": third_place,
                "third_place_flag": get_flag_url(third_place),
                "top_scoring_team": top_scorer_team[0],
                "top_scoring_flag": get_flag_url(top_scorer_team[0]),
                "top_scoring_goals": top_scorer_team[1],
                "total_goals": total_goals_tournament,
                "total_matches": 72 + 16,
            },
        }
    )


if __name__ == "__main__":
    print("=" * 64)
    print("⚽ FIFA WORLD CUP 2026 ML WEB APPLICATION")
    print("📂 Database SQLite : UI/worldcup.db")
    print("🌐 Truy cập giao diện tại: http://0.0.0.0:5000")
    print("=" * 64)
    app.run(host="0.0.0.0", port=5000, debug=False)
