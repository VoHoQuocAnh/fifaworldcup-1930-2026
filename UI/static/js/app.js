let appMetadata = {
    teams: [],
    iso_map: {},
    wc2026_groups: [],
    stages: [],
    stadiums: [],
    years: [],
};

// Biến theo dõi lượt chọn đội khi click vào Bảng đấu A - L (1 = Đội 1, 2 = Đội 2)
let nextSlotToFill = 1;

document.addEventListener("DOMContentLoaded", async () => {
    await initDashboard();
    bindEvents();
});

async function initDashboard() {
    try {
        const res = await fetch("/api/metadata");
        const data = await res.json();
        appMetadata = data;

        if (data.db_overview) {
            document.getElementById("kpiMatches").textContent =
                data.db_overview.total_matches.toLocaleString();
            renderModelBenchmark(data.db_overview.model_metrics || []);
        }
        if (data.best_model_name) {
            document.getElementById("kpiBestModel").textContent =
                `${data.best_model_name} (${data.best_accuracy}%)`;
        }

        populateSelectors(data);
        renderFlagArchRibbon(data.wc2026_groups || []);
        renderWC2026GroupsBoard(data.wc2026_groups || []);

        await runPrediction(false);
        await loadHistory();
        await loadHistoricalMatches();
    } catch (err) {
        console.error("Lỗi khởi tạo dashboard:", err);
    }
}

function getFlagUrl(teamName, width = 80) {
    const code = (appMetadata.iso_map && appMetadata.iso_map[teamName]) || "un";
    return `https://flagcdn.com/w${width}/${code}.png`;
}

function populateSelectors(data) {
    const t1Select = document.getElementById("team1Select");
    const t2Select = document.getElementById("team2Select");
    const archiveTeam = document.getElementById("archiveTeamFilter");

    t1Select.innerHTML = "";
    t2Select.innerHTML = "";

    data.teams.forEach((t) => {
        t1Select.add(new Option(t.name, t.name));
        t2Select.add(new Option(t.name, t.name));
        archiveTeam.add(new Option(t.name, t.name));
    });

    t1Select.value = "Argentina";
    t2Select.value = "France";

    const stageSelect = document.getElementById("stageSelect");
    stageSelect.innerHTML = "";
    data.stages.forEach((stg) => {
        stageSelect.add(new Option(stg, stg));
    });
    stageSelect.value = "Final";

    const yearSelect = document.getElementById("yearSelect");
    const archiveYear = document.getElementById("archiveYearFilter");
    yearSelect.innerHTML = "";
    data.years.forEach((yr) => {
        yearSelect.add(new Option(`World Cup ${yr}`, yr));
        archiveYear.add(new Option(`World Cup ${yr}`, yr));
    });
    yearSelect.value = "2026";

    const stadiumSelect = document.getElementById("stadiumSelect");
    stadiumSelect.innerHTML = "";
    data.stadiums.forEach((std) => {
        stadiumSelect.add(new Option(std, std));
    });

    syncSelectedTeamsUI();
}

function renderFlagArchRibbon(groups) {
    const ribbon = document.getElementById("flagArchRibbon");
    if (!ribbon) return;
    const allGroupTeams = [];
    groups.forEach((g) => {
        g.teams.forEach((t) => allGroupTeams.push(t));
    });

    ribbon.innerHTML = allGroupTeams
        .slice(0, 28)
        .map(
            (t) => `
        <img
            src="${t.flag_url}"
            alt="${t.name}"
            title="Chọn ${t.name}"
            class="arch-flag-item"
            onclick="selectTeamFromBoard('${t.name.replace(/'/g, "\\'")}')"
        />
    `
        )
        .join("");
}

function renderWC2026GroupsBoard(groups) {
    const colLeft = document.getElementById("groupsColLeft");
    const colRight = document.getElementById("groupsColRight");
    if (!colLeft || !colRight) return;

    const leftGroups = groups.filter((g) => g.side === "left");
    const rightGroups = groups.filter((g) => g.side === "right");

    const buildGroupHTML = (g) => {
        const sideClass = g.side === "right" ? "side-right" : "side-left";
        const letterClass = g.text_dark ? "dark-letter" : "";
        const teamsHTML = g.teams
            .map(
                (t) => `
            <div class="wc26-team-row" data-team="${t.name}" onclick="selectTeamFromBoard('${t.name.replace(/'/g, "\\'")}', 'Group ${g.group}')">
                <img src="${t.flag_url}" alt="${t.display}" class="wc26-flag" />
                <span class="wc26-team-name">${t.display}</span>
            </div>
        `
            )
            .join("");

        return `
            <div class="wc26-group-card ${sideClass}" style="--grp-color: ${g.color}">
                <div class="wc26-group-letter ${letterClass}" title="Nhấn để dự đoán cặp đấu Bảng ${g.group}" onclick="selectGroupMatchup('${g.group}')">
                    ${g.group}
                </div>
                <div class="wc26-group-teams">
                    ${teamsHTML}
                </div>
            </div>
        `;
    };

    colLeft.innerHTML = leftGroups.map(buildGroupHTML).join("");
    colRight.innerHTML = rightGroups.map(buildGroupHTML).join("");
    highlightSelectedOnBoard();
}

window.selectTeamFromBoard = function (teamName, groupName = null) {
    const t1Select = document.getElementById("team1Select");
    const t2Select = document.getElementById("team2Select");
    const indicator = document.getElementById("slotIndicatorText");

    if (nextSlotToFill === 1) {
        if (t2Select.value === teamName) {
            t2Select.value = t1Select.value;
        }
        t1Select.value = teamName;
        nextSlotToFill = 2;
        if (indicator) indicator.textContent = "ĐỘI TUYỂN 2";
    } else {
        if (t1Select.value === teamName) {
            t1Select.value = t2Select.value;
        }
        t2Select.value = teamName;
        nextSlotToFill = 1;
        if (indicator) indicator.textContent = "ĐỘI TUYỂN 1";
    }

    if (groupName) {
        document.getElementById("stageSelect").value = "Group Stage";
    }

    syncSelectedTeamsUI();
};

window.selectGroupMatchup = function (groupLetter) {
    const grp = (appMetadata.wc2026_groups || []).find((g) => g.group === groupLetter);
    if (!grp || grp.teams.length < 2) return;

    document.getElementById("team1Select").value = grp.teams[0].name;
    document.getElementById("team2Select").value = grp.teams[1].name;
    document.getElementById("stageSelect").value = "Group Stage";
    document.getElementById("yearSelect").value = "2026";
    syncSelectedTeamsUI();
    runPrediction(true);
    document.getElementById("predictionResultSection").scrollIntoView({ behavior: "smooth" });
};

function syncSelectedTeamsUI() {
    const t1 = document.getElementById("team1Select").value;
    const t2 = document.getElementById("team2Select").value;

    document.getElementById("team1FlagImg").src = getFlagUrl(t1, 160);
    document.getElementById("team2FlagImg").src = getFlagUrl(t2, 160);

    const pFlag1 = document.getElementById("posterFlag1");
    const pFlag2 = document.getElementById("posterFlag2");
    const pName1 = document.getElementById("posterName1");
    const pName2 = document.getElementById("posterName2");
    if (pFlag1) pFlag1.src = getFlagUrl(t1, 80);
    if (pFlag2) pFlag2.src = getFlagUrl(t2, 80);
    if (pName1) pName1.textContent = t1.toUpperCase();
    if (pName2) pName2.textContent = t2.toUpperCase();

    highlightSelectedOnBoard();
}

function highlightSelectedOnBoard() {
    const t1 = document.getElementById("team1Select").value;
    const t2 = document.getElementById("team2Select").value;
    document.querySelectorAll(".wc26-team-row").forEach((row) => {
        const rowTeam = row.getAttribute("data-team");
        if (rowTeam === t1 || rowTeam === t2) {
            row.classList.add("selected-team");
        } else {
            row.classList.remove("selected-team");
        }
    });
}

function bindEvents() {
    document.getElementById("predictBtn").addEventListener("click", () => runPrediction(true));
    document.getElementById("posterPredictBtn").addEventListener("click", () => {
        runPrediction(true);
        document.getElementById("predictionResultSection").scrollIntoView({ behavior: "smooth" });
    });

    document.getElementById("team1Select").addEventListener("change", () => {
        syncSelectedTeamsUI();
    });

    document.getElementById("team2Select").addEventListener("change", () => {
        syncSelectedTeamsUI();
    });

    document.getElementById("swapTeamsBtn").addEventListener("click", () => {
        const t1 = document.getElementById("team1Select");
        const t2 = document.getElementById("team2Select");
        const tmp = t1.value;
        t1.value = t2.value;
        t2.value = tmp;
        syncSelectedTeamsUI();
        runPrediction(true);
    });

    document.querySelectorAll(".preset-chip").forEach((btn) => {
        btn.addEventListener("click", () => {
            const t1 = btn.getAttribute("data-t1");
            const t2 = btn.getAttribute("data-t2");
            const stg = btn.getAttribute("data-stage");
            document.getElementById("team1Select").value = t1;
            document.getElementById("team2Select").value = t2;
            document.getElementById("stageSelect").value = stg;
            syncSelectedTeamsUI();
            runPrediction(true);
        });
    });

    document.getElementById("clearHistoryBtn").addEventListener("click", async () => {
        await fetch("/api/history", { method: "DELETE" });
        await loadHistory();
    });

    document.getElementById("archiveYearFilter").addEventListener("change", loadHistoricalMatches);
    document.getElementById("archiveTeamFilter").addEventListener("change", loadHistoricalMatches);
}

async function runPrediction(saveToDb = true) {
    const team1 = document.getElementById("team1Select").value;
    const team2 = document.getElementById("team2Select").value;
    const stage = document.getElementById("stageSelect").value;
    const year = parseInt(document.getElementById("yearSelect").value, 10) || 2026;
    const stadium = document.getElementById("stadiumSelect").value;
    const modelName = document.getElementById("modelSelect").value;
    const errBox = document.getElementById("errorAlert");

    if (team1 === team2) {
        errBox.textContent = "⚠️ Vui lòng chọn 2 đội tuyển khác nhau để phân tích & dự đoán!";
        errBox.classList.remove("hidden");
        return;
    }
    errBox.classList.add("hidden");

    const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            team1,
            team2,
            stage,
            world_cup_year: year,
            stadium,
            model_name: modelName || null,
            save_to_db: saveToDb,
        }),
    });

    const data = await res.json();
    if (!res.ok) {
        errBox.textContent = data.error || "Có lỗi xảy ra khi dự đoán.";
        errBox.classList.remove("hidden");
        return;
    }

    renderPredictionResult(data);
    if (data.history) {
        renderHistoryTable(data.history);
    }
}

function renderPredictionResult(data) {
    const t1 = data.team1;
    const t2 = data.team2;
    const probs = data.probabilities;
    const xg = data.expected_goals;

    syncSelectedTeamsUI();

    if (data.team1_stats) {
        document.getElementById("team1MiniStats").innerHTML =
            `<span>Tỉ lệ thắng: <strong>${data.team1_stats.win_rate}%</strong></span>` +
            `<span>•</span>` +
            `<span>Số trận WC: <strong>${data.team1_stats.played}</strong></span>`;
    }
    if (data.team2_stats) {
        document.getElementById("team2MiniStats").innerHTML =
            `<span>Tỉ lệ thắng: <strong>${data.team2_stats.win_rate}%</strong></span>` +
            `<span>•</span>` +
            `<span>Số trận WC: <strong>${data.team2_stats.played}</strong></span>`;
    }

    document.getElementById("activeModelTag").textContent = `Pipeline: ${data.model_used}`;
    document.getElementById("resFlag1").src = getFlagUrl(t1, 80);
    document.getElementById("resFlag2").src = getFlagUrl(t2, 80);
    document.getElementById("resTeam1").textContent = t1;
    document.getElementById("resTeam2").textContent = t2;
    document.getElementById("resXg1").textContent = `xG: ${xg.team1_xg}`;
    document.getElementById("resXg2").textContent = `xG: ${xg.team2_xg}`;
    document.getElementById("resScore").textContent = xg.suggested_score;
    document.getElementById("resMeta").textContent =
        `${data.stage} • WC ${data.world_cup_year} • ${data.stadium}`;

    const pill = document.getElementById("resWinnerPill");
    if (data.prediction_code === 2) {
        pill.textContent = `🏆 DỰ ĐOÁN: ${t1.toUpperCase()} THẮNG`;
    } else if (data.prediction_code === 0) {
        pill.textContent = `🏆 DỰ ĐOÁN: ${t2.toUpperCase()} THẮNG`;
    } else {
        pill.textContent = `⚖️ DỰ ĐOÁN: HAI ĐỘI HÒA`;
    }

    document.getElementById("probLabelT1").textContent = `${t1} Thắng`;
    document.getElementById("probLabelT2").textContent = `${t2} Thắng`;
    document.getElementById("probValT1").textContent = `${probs.team1_win}%`;
    document.getElementById("probValDraw").textContent = `${probs.draw}%`;
    document.getElementById("probValT2").textContent = `${probs.team2_win}%`;

    document.getElementById("barWin").style.width = `${probs.team1_win}%`;
    document.getElementById("barDraw").style.width = `${probs.draw}%`;
    document.getElementById("barLoss").style.width = `${probs.team2_win}%`;

    renderTeamComparison(data.team1_stats, data.team2_stats);
    renderCouncilVotes(data.council_votes, t1, t2);
    renderH2H(data.head_to_head, t1, t2);
}

function renderTeamComparison(s1, s2) {
    if (!s1 || !s2) return;
    const container = document.getElementById("comparisonBars");
    const metrics = [
        { label: "Tỉ lệ thắng lịch sử (%)", v1: s1.win_rate, v2: s2.win_rate, suffix: "%" },
        { label: "Bàn thắng trung bình / trận", v1: s1.avg_goals_for, v2: s2.avg_goals_for, suffix: "" },
        { label: "Tổng số trận tại World Cup", v1: s1.played, v2: s2.played, suffix: " trận" },
        { label: "Tổng số bàn thắng ghi được", v1: s1.goals_for, v2: s2.goals_for, suffix: " bàn" },
    ];

    container.innerHTML = metrics
        .map((m) => {
            const total = (m.v1 + m.v2) || 1;
            const p1 = Math.round((m.v1 / total) * 100);
            const p2 = 100 - p1;
            return `
            <div class="comp-row">
                <div class="comp-row-top">
                    <span style="color:#00d66c">${m.v1}${m.suffix}</span>
                    <span>${m.label}</span>
                    <span style="color:#38b6ff">${m.v2}${m.suffix}</span>
                </div>
                <div class="comp-dual-bar">
                    <div class="comp-fill-left" style="width:${p1}%"></div>
                    <div class="comp-fill-right" style="width:${p2}%"></div>
                </div>
            </div>
        `;
        })
        .join("");
}

function renderCouncilVotes(votes, t1, t2) {
    const container = document.getElementById("councilList");
    if (!votes) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = Object.entries(votes)
        .map(([modelName, v]) => {
            let badgeClass = "outcome-draw";
            if (v.label === 2) badgeClass = "outcome-t1";
            else if (v.label === 0) badgeClass = "outcome-t2";

            return `
            <div class="council-item">
                <div>
                    <div class="council-model-name">🤖 ${modelName}</div>
                    <div class="council-probs">
                        ${t1}: <strong>${v.win_prob}%</strong> • Hòa: <strong>${v.draw_prob}%</strong> • ${t2}: <strong>${v.loss_prob}%</strong>
                    </div>
                </div>
                <span class="council-outcome-badge ${badgeClass}">${v.outcome}</span>
            </div>
        `;
        })
        .join("");
}

function renderH2H(h2h, t1, t2) {
    const badge = document.getElementById("h2hSummaryBadge");
    const list = document.getElementById("h2hList");
    if (!h2h || h2h.total === 0) {
        badge.textContent = "Chưa gặp nhau tại WC";
        list.innerHTML = `<div class="h2h-item"><span>Hai đội chưa từng chạm trán trực tiếp tại VCK World Cup.</span></div>`;
        return;
    }

    badge.textContent = `${h2h.total} trận (${t1} thắng ${h2h.team1_wins} - Hòa ${h2h.draws} - ${t2} thắng ${h2h.team2_wins})`;
    list.innerHTML = h2h.matches
        .map(
            (m) => `
        <div class="h2h-item">
            <span><strong>WC ${m.year}</strong> (${m.stage})</span>
            <span>
                <img src="${getFlagUrl(m.team1, 40)}" class="inline-flag" alt="" />
                ${m.team1}
                <span class="h2h-score-pill">${m.score}</span>
                ${m.team2}
                <img src="${getFlagUrl(m.team2, 40)}" class="inline-flag" alt="" />
            </span>
        </div>
    `
        )
        .join("");
}

async function loadHistory() {
    const res = await fetch("/api/history");
    const data = await res.json();
    renderHistoryTable(data.history || []);
}

function renderHistoryTable(rows) {
    const tbody = document.getElementById("historyTableBody");
    if (!rows.length) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:#94a3b8;">Chưa có lịch sử dự đoán nào trong Database.</td></tr>`;
        return;
    }

    tbody.innerHTML = rows
        .map(
            (r) => `
        <tr class="clickable-row" onclick="reloadFromHistory('${r.team1.replace(/'/g, "\\'")}', '${r.team2.replace(/'/g, "\\'")}', '${r.stage}', ${r.world_cup_year})">
            <td style="color:#94a3b8;font-size:12px;">${r.created_at}</td>
            <td>
                <img src="${getFlagUrl(r.team1, 40)}" class="inline-flag" alt="" />
                <strong>${r.team1}</strong> vs
                <img src="${getFlagUrl(r.team2, 40)}" class="inline-flag" alt="" />
                <strong>${r.team2}</strong>
            </td>
            <td>${r.stage} (${r.world_cup_year})</td>
            <td><span class="h2h-score-pill">${r.suggested_score}</span></td>
            <td><strong style="color:#b8ff01">${r.predicted_winner}</strong></td>
            <td>${r.team1_win_prob}% / ${r.draw_prob}% / ${r.team2_win_prob}%</td>
            <td><span class="sub-badge">${r.model_used}</span></td>
            <td>
                <button class="del-row-btn" onclick="deleteHistoryItem(event, ${r.id})" title="Xóa bản ghi này">✕</button>
            </td>
        </tr>
    `
        )
        .join("");
}

window.reloadFromHistory = function (t1, t2, stage, year) {
    document.getElementById("team1Select").value = t1;
    document.getElementById("team2Select").value = t2;
    document.getElementById("stageSelect").value = stage;
    document.getElementById("yearSelect").value = String(year);
    syncSelectedTeamsUI();
    runPrediction(false);
    document.getElementById("predictionResultSection").scrollIntoView({ behavior: "smooth" });
};

window.deleteHistoryItem = async function (event, id) {
    event.stopPropagation();
    const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
    const data = await res.json();
    renderHistoryTable(data.history || []);
};

function renderModelBenchmark(metrics) {
    const container = document.getElementById("modelMetricsList");
    if (!metrics.length) return;

    container.innerHTML = metrics
        .map(
            (m) => `
        <div class="metric-card ${m.is_best ? "best-model-card" : ""}">
            <div class="metric-top">
                <div class="metric-name">
                    ${m.is_best ? "🥇" : "🤖"} ${m.model_name}
                    ${m.is_best ? '<span class="sub-badge">BEST MODEL</span>' : ""}
                </div>
                <div class="metric-acc">${m.accuracy}%</div>
            </div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: ${m.accuracy}%"></div>
            </div>
            <div class="metric-sub-row">
                <span>Precision: <strong>${m.precision_score}%</strong></span>
                <span>Recall: <strong>${m.recall_score}%</strong></span>
                <span>F1-Score: <strong>${m.f1_score}%</strong></span>
            </div>
        </div>
    `
        )
        .join("");
}

async function loadHistoricalMatches() {
    const year = document.getElementById("archiveYearFilter").value;
    const team = document.getElementById("archiveTeamFilter").value;
    const params = new URLSearchParams({ limit: "25" });
    if (year) params.set("year", year);
    if (team) params.set("team", team);

    const res = await fetch(`/api/matches?${params.toString()}`);
    const data = await res.json();
    const tbody = document.getElementById("archiveTableBody");

    if (!data.matches || !data.matches.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#94a3b8;">Không tìm thấy trận đấu phù hợp.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.matches
        .map(
            (m) => `
        <tr>
            <td><strong>${m.world_cup_year}</strong></td>
            <td>${m.host_country}</td>
            <td>${m.stage}</td>
            <td><img src="${m.team1_flag_url}" class="inline-flag" alt="" /> <strong>${m.team1}</strong></td>
            <td><span class="h2h-score-pill">${m.goals_team1} - ${m.goals_team2}</span></td>
            <td><img src="${m.team2_flag_url}" class="inline-flag" alt="" /> <strong>${m.team2}</strong></td>
            <td style="color:#94a3b8;">${m.stadium}, ${m.city}</td>
        </tr>
    `
        )
        .join("");
}
