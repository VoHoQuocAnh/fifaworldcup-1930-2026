import os
import sys
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from predict import load_resources, predict_match
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


if __name__ == "__main__":
    print("=" * 64)
    print("⚽ FIFA WORLD CUP 2026 ML WEB APPLICATION")
    print("📂 Database SQLite : UI/worldcup.db")
    print("🌐 Truy cập giao diện tại: http://127.0.0.1:5000")
    print("=" * 64)
    app.run(host="127.0.0.1", port=5000, debug=False)
