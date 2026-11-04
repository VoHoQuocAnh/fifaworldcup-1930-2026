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
let currentStageIndex = 0;

const DECK_STAGES_META = [
    { code: "01 / 05", title: "MATCH ARENA" },
    { code: "02 / 05", title: "AI VERDICT & COUNCIL" },
    { code: "03 / 05", title: "RADAR & POISSON MATRIX" },
    { code: "04 / 05", title: "2026 BRACKET SIMULATOR" },
    { code: "05 / 05", title: "GROUPS A–L & DATA VAULT" },
];

window.switchStage = function (targetIdx) {
    const total = DECK_STAGES_META.length;
    const nextIdx = ((targetIdx % total) + total) % total;
    currentStageIndex = nextIdx;

    const stages = document.querySelectorAll(".deck-stage");
    stages.forEach((section) => {
        const idx = parseInt(section.getAttribute("data-stage-index"), 10);
        section.classList.remove("active", "stage-exit-left", "stage-exit-right");
        if (idx === nextIdx) {
            section.classList.add("active");
        } else if (idx < nextIdx) {
            section.classList.add("stage-exit-left");
        } else {
            section.classList.add("stage-exit-right");
        }
    });

    document.querySelectorAll(".dock-item[data-target-stage]").forEach((btn) => {
        const bIdx = parseInt(btn.getAttribute("data-target-stage"), 10);
        btn.classList.toggle("active", bIdx === nextIdx);
    });

    const counterBadge = document.getElementById("stageCounterBadge");
    const titleBadge = document.getElementById("stageTitleBadge");
    if (counterBadge && DECK_STAGES_META[nextIdx]) {
        counterBadge.textContent = DECK_STAGES_META[nextIdx].code;
    }
    if (titleBadge && DECK_STAGES_META[nextIdx]) {
        titleBadge.textContent = DECK_STAGES_META[nextIdx].title;
    }

    const viewport = document.getElementById("deckViewport");
    if (viewport) {
        viewport.scrollTo({ top: 0, behavior: "smooth" });
    }
    triggerConfettiBurst();
};

window.toggleVaultSubtab = function (sub, btnEl) {
    document.querySelectorAll(".vault-sub-btn").forEach((b) => b.classList.remove("active"));
    if (btnEl) btnEl.classList.add("active");
    const posterSub = document.getElementById("vaultPosterSub");
    const dbSub = document.getElementById("vaultDbSub");
    if (!posterSub || !dbSub) return;

    if (sub === "poster") {
        posterSub.classList.remove("hidden");
        dbSub.classList.add("hidden");
    } else {
        posterSub.classList.add("hidden");
        dbSub.classList.remove("hidden");
    }
};

document.addEventListener("DOMContentLoaded", async () => {
    initStadiumParticles();
    init3DTiltCards();
    initScrollReveal();
    await initDashboard();
    bindEvents();
});

function animateNumber(elId, targetValue, prefix = "", suffix = "", decimals = 1, duration = 680) {
    const el = typeof elId === "string" ? document.getElementById(elId) : elId;
    if (!el) return;
    const startVal = 0;
    const startTime = performance.now();

    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = startVal + (targetValue - startVal) * eased;
        el.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`;
        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            el.textContent = `${prefix}${Number(targetValue).toFixed(decimals)}${suffix}`;
        }
    }
    requestAnimationFrame(step);
}

function triggerElementAnim(elId, animClass) {
    const el = typeof elId === "string" ? document.getElementById(elId) : elId;
    if (!el) return;
    el.classList.remove(animClass);
    void el.offsetWidth;
    el.classList.add(animClass);
}

let stadiumParticles = [];
let burstParticles = [];

function initStadiumParticles() {
    const canvas = document.getElementById("stadiumParticlesCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const resize = () => {
        canvas.width = canvas.parentElement.clientWidth || window.innerWidth;
        canvas.height = canvas.parentElement.clientHeight || 620;
    };
    resize();
    window.addEventListener("resize", resize);

    const pastelColors = ["#76c8b2", "#b39ddb", "#f4a498", "#8aa6f7", "#e5b567"];
    stadiumParticles = Array.from({ length: 36 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 3.2 + 1.2,
        vx: (Math.random() - 0.5) * 0.4,
        vy: -Math.random() * 0.45 - 0.12,
        alpha: Math.random() * 0.45 + 0.2,
        color: pastelColors[Math.floor(Math.random() * pastelColors.length)],
    }));

    function drawFrame() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Ambient floating sparks
        for (const p of stadiumParticles) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.y < -10) {
                p.y = canvas.height + 10;
                p.x = Math.random() * canvas.width;
            }
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.alpha;
            ctx.fill();
        }

        // Celebratory burst particles on prediction
        for (let i = burstParticles.length - 1; i >= 0; i--) {
            const b = burstParticles[i];
            b.x += b.vx;
            b.y += b.vy;
            b.vy += 0.08;
            b.alpha -= 0.014;
            if (b.alpha <= 0) {
                burstParticles.splice(i, 1);
                continue;
            }
            ctx.beginPath();
            ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
            ctx.fillStyle = b.color;
            ctx.globalAlpha = Math.max(0, b.alpha);
            ctx.fill();
        }
        ctx.globalAlpha = 1;
        requestAnimationFrame(drawFrame);
    }
    requestAnimationFrame(drawFrame);
}

function triggerConfettiBurst() {
    const canvas = document.getElementById("stadiumParticlesCanvas");
    if (!canvas) return;
    const cx = canvas.width / 2;
    const cy = canvas.height * 0.55;
    const palette = ["#5bb89d", "#6c8eef", "#ea8a7e", "#9d80d9", "#dfab56"];

    for (let i = 0; i < 45; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 5.5 + 1.8;
        burstParticles.push({
            x: cx,
            y: cy,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 2.2,
            r: Math.random() * 3.2 + 1.5,
            alpha: 1,
            color: palette[Math.floor(Math.random() * palette.length)],
        });
    }
}

function init3DTiltCards() {
    const cards = document.querySelectorAll(".contender-card");
    cards.forEach((card) => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const rotY = ((x / rect.width) - 0.5) * 10;
            const rotX = ((0.5 - (y / rect.height))) * 10;
            card.style.transform = `perspective(700px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-3px)`;
        });
        card.addEventListener("mouseleave", () => {
            card.style.transform = "perspective(700px) rotateX(0deg) rotateY(0deg) translateY(0)";
        });
    });
}

function initScrollReveal() {
    const panels = document.querySelectorAll(".glass-panel, .wc26-poster-section");
    if (!("IntersectionObserver" in window)) return;

    const obs = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("reveal-visible");
                }
            });
        },
        { threshold: 0.08 }
    );

    panels.forEach((p) => {
        p.classList.add("reveal-hidden");
        obs.observe(p);
    });
}

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
        await runTournamentSimulation("ai");
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
    switchStage(1);
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
    document.getElementById("predictBtn").addEventListener("click", async () => {
        await runPrediction(true);
        switchStage(1);
    });
    document.getElementById("posterPredictBtn").addEventListener("click", async () => {
        await runPrediction(true);
        switchStage(1);
    });

    const prevStageBtn = document.getElementById("prevStageBtn");
    const nextStageBtn = document.getElementById("nextStageBtn");
    if (prevStageBtn) {
        prevStageBtn.addEventListener("click", () => switchStage(currentStageIndex - 1));
    }
    if (nextStageBtn) {
        nextStageBtn.addEventListener("click", () => switchStage(currentStageIndex + 1));
    }

    document.addEventListener("keydown", (e) => {
        const tag = (e.target && e.target.tagName) || "";
        if (tag === "SELECT" || tag === "INPUT" || tag === "TEXTAREA") return;
        if (e.key === "ArrowRight") {
            switchStage(currentStageIndex + 1);
        } else if (e.key === "ArrowLeft") {
            switchStage(currentStageIndex - 1);
        }
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

    const randomBtn = document.getElementById("randomMatchBtn");
    if (randomBtn) {
        randomBtn.addEventListener("click", () => {
            const topTeams = [
                "Argentina", "France", "Brazil", "England", "Spain", "Germany",
                "Portugal", "Netherlands", "Croatia", "Morocco", "Uruguay",
                "Colombia", "Japan", "USA", "Belgium", "Senegal", "Mexico", "Switzerland"
            ];
            const i1 = Math.floor(Math.random() * topTeams.length);
            let i2 = Math.floor(Math.random() * topTeams.length);
            if (i2 === i1) i2 = (i1 + 1) % topTeams.length;
            const stages = ["Group Stage", "Round of 16", "Quarter-final", "Semi-final", "Final"];
            document.getElementById("team1Select").value = topTeams[i1];
            document.getElementById("team2Select").value = topTeams[i2];
            document.getElementById("stageSelect").value = stages[Math.floor(Math.random() * stages.length)];
            syncSelectedTeamsUI();
            runPrediction(true);
        });
    }

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

    // Tournament Simulator Controls
    const simAiBtn = document.getElementById("simAiBtn");
    const simMcBtn = document.getElementById("simMonteCarloBtn");
    if (simAiBtn) {
        simAiBtn.addEventListener("click", () => runTournamentSimulation("ai"));
    }
    if (simMcBtn) {
        simMcBtn.addEventListener("click", () => runTournamentSimulation("montecarlo"));
    }

    document.querySelectorAll(".sim-tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".sim-tab-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            const tab = btn.getAttribute("data-simtab");
            const bracketEl = document.getElementById("simBracketView");
            const groupsEl = document.getElementById("simGroupsView");
            if (tab === "bracket") {
                bracketEl.classList.remove("hidden");
                groupsEl.classList.add("hidden");
            } else {
                bracketEl.classList.add("hidden");
                groupsEl.classList.remove("hidden");
            }
        });
    });

    document.getElementById("clearHistoryBtn").addEventListener("click", async () => {
        await fetch("/api/history", { method: "DELETE" });
        await loadHistory();
    });

    document.getElementById("archiveYearFilter").addEventListener("change", loadHistoricalMatches);
    document.getElementById("archiveTeamFilter").addEventListener("change", loadHistoricalMatches);

    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            document.body.classList.toggle("light-mode");
            const isLight = document.body.classList.contains("light-mode");
            themeBtn.textContent = isLight ? "☀️ LIGHT" : "🌙 DARK";
        });
    }
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
            `<span>WIN <strong>${data.team1_stats.win_rate}%</strong></span>` +
            `<span>•</span>` +
            `<span>MP <strong>${data.team1_stats.played}</strong></span>`;
    }
    if (data.team2_stats) {
        document.getElementById("team2MiniStats").innerHTML =
            `<span>WIN <strong>${data.team2_stats.win_rate}%</strong></span>` +
            `<span>•</span>` +
            `<span>MP <strong>${data.team2_stats.played}</strong></span>`;
    }

    document.getElementById("activeModelTag").textContent = data.model_used;
    document.getElementById("resFlag1").src = getFlagUrl(t1, 80);
    document.getElementById("resFlag2").src = getFlagUrl(t2, 80);
    document.getElementById("resTeam1").textContent = t1;
    document.getElementById("resTeam2").textContent = t2;
    animateNumber("resXg1", xg.team1_xg, "xG ", "", 2, 650);
    animateNumber("resXg2", xg.team2_xg, "xG ", "", 2, 650);
    document.getElementById("resScore").textContent = xg.suggested_score;
    triggerElementAnim("resScore", "score-pop-anim");
    triggerElementAnim("resFlag1", "flag-flip-anim");
    triggerElementAnim("resFlag2", "flag-flip-anim");
    triggerConfettiBurst();

    document.getElementById("resMeta").textContent =
        `${data.stage} • ${data.world_cup_year} • ${data.stadium}`;

    const pill = document.getElementById("resWinnerPill");
    if (data.prediction_code === 2) {
        pill.textContent = `🏆 ${t1.toUpperCase()} WIN`;
    } else if (data.prediction_code === 0) {
        pill.textContent = `🏆 ${t2.toUpperCase()} WIN`;
    } else {
        pill.textContent = `⚖️ DRAW`;
    }
    triggerElementAnim(pill, "score-pop-anim");

    document.getElementById("probLabelT1").textContent = t1.toUpperCase();
    document.getElementById("probLabelT2").textContent = t2.toUpperCase();
    animateNumber("probValT1", probs.team1_win, "", "%", 1, 720);
    animateNumber("probValDraw", probs.draw, "", "%", 1, 720);
    animateNumber("probValT2", probs.team2_win, "", "%", 1, 720);

    document.getElementById("barWin").style.width = `${probs.team1_win}%`;
    document.getElementById("barDraw").style.width = `${probs.draw}%`;
    document.getElementById("barLoss").style.width = `${probs.team2_win}%`;

    renderTeamComparison(data.team1_stats, data.team2_stats);
    renderCouncilVotes(data.council_votes, t1, t2);
    renderH2H(data.head_to_head, t1, t2);

    // 3 Tính năng Nâng cao Mới:
    renderRadarChart(data.team1_stats, data.team2_stats, t1, t2);
    renderPoissonScorelines(data.poisson_scorelines, t1, t2);
    renderExplainableAI(data.explainable_ai, t1, t2);
}

/* =========================================================================
   1. BIỂU ĐỒ RADAR 5 CẠNH (5-AXIS TACTICAL RADAR SVG)
   ========================================================================= */
function renderRadarChart(s1, s2, t1, t2) {
    const container = document.getElementById("radarChartContainer");
    const legendEl = document.getElementById("radarLegend");
    if (!container || !s1 || !s2) return;

    const r1 = s1.radar || { attack: 60, defense: 60, win_efficiency: 55, knockout: 50, experience: 55 };
    const r2 = s2.radar || { attack: 60, defense: 60, win_efficiency: 55, knockout: 50, experience: 55 };

    legendEl.innerHTML = `
        <div class="radar-leg-item">
            <span class="radar-dot" style="background:#00f5a0"></span>
            <img src="${getFlagUrl(t1, 40)}" class="inline-flag" alt="" />
            <strong>${t1}</strong>
        </div>
        <div class="radar-leg-item">
            <span class="radar-dot" style="background:#00f0ff"></span>
            <img src="${getFlagUrl(t2, 40)}" class="inline-flag" alt="" />
            <strong>${t2}</strong>
        </div>
    `;

    const axes = [
        { key: "attack", label: "Tấn công", v1: r1.attack, v2: r2.attack },
        { key: "defense", label: "Phòng ngự", v1: r1.defense, v2: r2.defense },
        { key: "win_efficiency", label: "Hiệu suất Thắng", v1: r1.win_efficiency, v2: r2.win_efficiency },
        { key: "knockout", label: "Bản lĩnh Knockout", v1: r1.knockout, v2: r2.knockout },
        { key: "experience", label: "Kinh nghiệm WC", v1: r1.experience, v2: r2.experience },
    ];

    const size = 310;
    const cx = size / 2;
    const cy = size / 2 + 6;
    const radius = 104;
    const levels = [25, 50, 75, 100];

    const getPoint = (idx, val) => {
        const angle = (Math.PI * 2 * idx) / axes.length - Math.PI / 2;
        const r = (val / 100) * radius;
        return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
    };

    const gridPolygons = levels
        .map((lvl) => {
            const pts = axes.map((_, i) => getPoint(i, lvl).join(",")).join(" ");
            return `<polygon points="${pts}" fill="none" stroke="rgba(0,240,255,0.25)" stroke-width="1" />`;
        })
        .join("");

    const axisLines = axes
        .map((ax, i) => {
            const [x, y] = getPoint(i, 100);
            const [lx, ly] = getPoint(i, 127);
            return `
                <line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="rgba(0,240,255,0.3)" stroke-width="1" />
                <text x="${lx}" y="${ly}" fill="var(--text-primary)" font-size="11" font-weight="700" text-anchor="middle" dominant-baseline="middle">
                    ${ax.label}
                </text>
                <text x="${lx}" y="${ly + 13}" fill="var(--text-muted)" font-size="10" font-weight="700" text-anchor="middle">
                    (${ax.v1} vs ${ax.v2})
                </text>
            `;
        })
        .join("");

    const poly1Pts = axes.map((ax, i) => getPoint(i, ax.v1).join(",")).join(" ");
    const poly2Pts = axes.map((ax, i) => getPoint(i, ax.v2).join(",")).join(" ");

    const dots1 = axes
        .map((ax, i) => {
            const [x, y] = getPoint(i, ax.v1);
            return `<circle cx="${x}" cy="${y}" r="4.5" fill="#00f5a0" stroke="#ffffff" stroke-width="1.8" />`;
        })
        .join("");

    const dots2 = axes
        .map((ax, i) => {
            const [x, y] = getPoint(i, ax.v2);
            return `<circle cx="${x}" cy="${y}" r="4.5" fill="#00f0ff" stroke="#ffffff" stroke-width="1.8" />`;
        })
        .join("");

    container.innerHTML = `
        <svg viewBox="0 0 ${size} ${size}" class="radar-svg">
            ${gridPolygons}
            ${axisLines}
            <g class="radar-poly-anim">
                <polygon points="${poly2Pts}" fill="rgba(0, 240, 255, 0.25)" stroke="#00f0ff" stroke-width="2.5" />
                <polygon points="${poly1Pts}" fill="rgba(0, 245, 160, 0.28)" stroke="#00f5a0" stroke-width="2.5" />
                ${dots2}
                ${dots1}
            </g>
        </svg>
    `;
}

/* =========================================================================
   2. MA TRẬN XÁC SUẤT TỈ SỐ CHÍNH XÁC (POISSON SCORELINE HEATMAP)
   ========================================================================= */
function renderPoissonScorelines(poissonData, t1, t2) {
    const topStrip = document.getElementById("topScorelinesStrip");
    const matrixWrap = document.getElementById("poissonMatrixContainer");
    if (!topStrip || !matrixWrap || !poissonData) return;

    const topScores = poissonData.top_scores || [];
    topStrip.innerHTML = topScores
        .map((item, idx) => {
            const cls =
                item.type === "t1"
                    ? "score-chip-t1"
                    : item.type === "t2"
                    ? "score-chip-t2"
                    : "score-chip-draw";
            return `
            <div class="top-score-chip stagger-item ${cls} ${idx === 0 ? "most-likely-score" : ""}" style="animation-delay:${idx * 55}ms">
                <span class="top-score-rank">#${idx + 1}</span>
                <strong class="top-score-val">${item.score}</strong>
                <span class="top-score-prob">${item.prob}%</span>
            </div>
        `;
        })
        .join("");

    const matrix = poissonData.matrix || [];
    const maxProb = Math.max(...topScores.map((s) => s.prob), 12);

    let tableHTML = `
        <div class="matrix-axis-note">
            <span>⬇️ Bàn thắng <strong>${t1}</strong> (Hàng)</span>
            <span>➡️ Bàn thắng <strong>${t2}</strong> (Cột)</span>
        </div>
        <table class="poisson-table">
            <thead>
                <tr>
                    <th>${t1.slice(0, 3).toUpperCase()} \\ ${t2.slice(0, 3).toUpperCase()}</th>
                    <th>0 bàn</th>
                    <th>1 bàn</th>
                    <th>2 bàn</th>
                    <th>3 bàn</th>
                    <th>4+ bàn</th>
                </tr>
            </thead>
            <tbody>
    `;

    matrix.forEach((row, g1) => {
        tableHTML += `<tr><th class="row-goal-hdr">${g1}${g1 === 4 ? "+" : ""} bàn</th>`;
        row.forEach((prob, g2) => {
            const intensity = Math.min(0.85, Math.max(0.14, (prob / maxProb) * 0.78));
            let bg = `rgba(229, 181, 103, ${intensity * 0.65})`;
            if (g1 > g2) {
                bg = `rgba(91, 184, 157, ${intensity})`;
            } else if (g2 > g1) {
                bg = `rgba(108, 142, 239, ${intensity})`;
            }
            tableHTML += `
                <td style="background:${bg}" title="${t1} ${g1} - ${g2} ${t2}: ${prob}%">
                    <div class="cell-score">${g1}-${g2}</div>
                    <div class="cell-prob">${prob}%</div>
                </td>
            `;
        });
        tableHTML += `</tr>`;
    });

    tableHTML += `</tbody></table>`;
    matrixWrap.innerHTML = tableHTML;
}

/* =========================================================================
   3. GIẢI THÍCH MÔ HÌNH AI (EXPLAINABLE AI & PENALTY SHOOTOUT)
   ========================================================================= */
function renderExplainableAI(xaiData, t1, t2) {
    const commentaryEl = document.getElementById("aiCommentaryText");
    const penBox = document.getElementById("penaltyScenarioBox");
    const factorsWrap = document.getElementById("xaiFactorsContainer");

    if (!xaiData) return;

    if (commentaryEl && xaiData.commentary) {
        commentaryEl.textContent = xaiData.commentary;
    }

    if (penBox) {
        const pen = xaiData.penalty_shootout;
        if (pen && pen.enabled) {
            penBox.classList.remove("hidden");
            penBox.innerHTML = `
                <div class="pen-title">
                    <span>🥅 KỊCH BẢN HIỆP PHỤ &amp; LUÂN LƯU 11M (KNOCKOUT STAGE)</span>
                    <span class="pen-trigger">Xác suất kéo vào Hiệp phụ: <strong>${pen.draw_trigger_prob}%</strong></span>
                </div>
                <div class="pen-bar-wrap">
                    <div class="pen-side pen-left" style="width:${pen.team1_pen_prob}%">
                        ${t1}: ${pen.team1_pen_prob}%
                    </div>
                    <div class="pen-side pen-right" style="width:${pen.team2_pen_prob}%">
                        ${t2}: ${pen.team2_pen_prob}%
                    </div>
                </div>
            `;
        } else {
            penBox.classList.add("hidden");
        }
    }

    if (factorsWrap && xaiData.factors) {
        factorsWrap.innerHTML = xaiData.factors
            .map((f, idx) => {
                let badgeClass = "xai-neutral";
                if (f.favor === "t1") badgeClass = "xai-t1";
                else if (f.favor === "t2") badgeClass = "xai-t2";

                return `
                <div class="xai-factor-card stagger-item" style="animation-delay:${idx * 70}ms">
                    <div class="xai-factor-top">
                        <span class="xai-factor-title">${f.icon} ${f.title}</span>
                        <span class="xai-impact-pill ${badgeClass}">${f.impact}</span>
                    </div>
                    <p class="xai-factor-desc">${f.desc}</p>
                    <div class="xai-weight-bar">
                        <div class="xai-weight-fill ${badgeClass}" style="width:${f.weight}%"></div>
                    </div>
                </div>
            `;
            })
            .join("");
    }
}

/* =========================================================================
   4. TRÌNH GIẢ LẬP TOÀN BỘ WORLD CUP 2026 (TOURNAMENT SIMULATOR)
   ========================================================================= */
async function runTournamentSimulation(mode = "ai") {
    const podiumEl = document.getElementById("simPodiumBanner");
    const bracketEl = document.getElementById("simBracketView");
    const groupsEl = document.getElementById("simGroupsView");
    const modelName = document.getElementById("modelSelect")?.value || null;

    if (!podiumEl || !bracketEl) return;

    podiumEl.innerHTML = `<div class="sim-loading">⚡ Đang giả lập 72 trận Vòng Bảng &amp; 16 trận Knockout bằng Pipeline AI...</div>`;

    try {
        const res = await fetch("/api/simulate_tournament", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode, model_name: modelName }),
        });
        const data = await res.json();
        renderSimPodium(data.summary, data.mode, data.model_used);
        renderSimKnockoutBracket(data.knockout);
        renderSimGroupsStandings(data.groups);
        triggerConfettiBurst();
    } catch (err) {
        console.error("Lỗi giả lập giải đấu:", err);
        podiumEl.innerHTML = `<div class="sim-loading">⚠️ Không thể tải dữ liệu giả lập giải đấu.</div>`;
    }
}

function renderSimPodium(sum, mode, modelUsed) {
    const podiumEl = document.getElementById("simPodiumBanner");
    if (!podiumEl || !sum) return;

    const modeBadge =
        mode === "montecarlo"
            ? "🎲 Chế độ Monte Carlo (Có yếu tố bất ngờ)"
            : "🤖 Chế độ AI Chuẩn (Xác suất tối ưu)";

    podiumEl.innerHTML = `
        <div class="podium-card champion-card stagger-item" style="animation-delay:0ms">
            <div class="podium-rank-tag">👑 NHÀ VÔ ĐỊCH WORLD CUP 2026</div>
            <div class="podium-team-main">
                <img src="${sum.champion_flag}" alt="${sum.champion}" class="podium-flag-lg flag-flip-anim" />
                <div>
                    <div class="podium-team-name">${sum.champion.toUpperCase()}</div>
                    <div class="podium-sub-meta">${modeBadge} • ${modelUsed}</div>
                </div>
            </div>
        </div>

        <div class="podium-card stagger-item" style="animation-delay:75ms">
            <div class="podium-rank-tag silver-tag">🥈 Á QUÂN (RUNNER-UP)</div>
            <div class="podium-team-row">
                <img src="${sum.runner_up_flag}" alt="${sum.runner_up}" class="podium-flag-sm" />
                <strong>${sum.runner_up}</strong>
            </div>
        </div>

        <div class="podium-card stagger-item" style="animation-delay:150ms">
            <div class="podium-rank-tag bronze-tag">🥉 HẠNG BA (THIRD PLACE)</div>
            <div class="podium-team-row">
                <img src="${sum.third_place_flag}" alt="${sum.third_place}" class="podium-flag-sm" />
                <strong>${sum.third_place}</strong>
            </div>
        </div>

        <div class="podium-card stagger-item" style="animation-delay:225ms">
            <div class="podium-rank-tag boot-tag">⚽ HÀNG CÔNG MẠNH NHẤT GIẢI</div>
            <div class="podium-team-row">
                <img src="${sum.top_scoring_flag}" alt="${sum.top_scoring_team}" class="podium-flag-sm" />
                <strong>${sum.top_scoring_team} (${sum.top_scoring_goals} bàn)</strong>
            </div>
            <div class="podium-sub-meta" style="margin-top:4px;">Tổng bàn thắng cả giải: ${sum.total_goals} bàn / ${sum.total_matches} trận</div>
        </div>
    `;
}

function renderSimKnockoutBracket(ko) {
    const bracketEl = document.getElementById("simBracketView");
    if (!bracketEl || !ko) return;

    const buildMatchBox = (m, highlightFinal = false) => {
        const w1 = m.winner === m.team1 ? "ko-team-win" : "";
        const w2 = m.winner === m.team2 ? "ko-team-win" : "";
        const penBadge = m.penalty_winner
            ? `<div class="ko-pen-note">🎯 Pen: ${m.penalty_winner} thắng</div>`
            : "";

        return `
            <div class="ko-match-card ${highlightFinal ? "ko-final-card" : ""}"
                 title="Nhấn để phân tích sâu trận ${m.team1} vs ${m.team2}"
                 onclick="inspectSimulatedMatch('${m.team1.replace(/'/g, "\\'")}', '${m.team2.replace(/'/g, "\\'")}', '${m.stage}')">
                <div class="ko-team-line ${w1}">
                    <span class="ko-team-info">
                        <img src="${m.flag1}" alt="" class="ko-flag" />
                        <span>${m.team1}</span>
                    </span>
                    <strong class="ko-score">${m.score1}</strong>
                </div>
                <div class="ko-team-line ${w2}">
                    <span class="ko-team-info">
                        <img src="${m.flag2}" alt="" class="ko-flag" />
                        <span>${m.team2}</span>
                    </span>
                    <strong class="ko-score">${m.score2}</strong>
                </div>
                ${penBadge}
            </div>
        `;
    };

    bracketEl.innerHTML = `
        <div class="bracket-columns">
            <div class="bracket-col">
                <div class="bracket-col-title">VÒNG 1/8 (ROUND OF 16)</div>
                <div class="bracket-match-list">
                    ${ko.r16.map((m) => buildMatchBox(m)).join("")}
                </div>
            </div>

            <div class="bracket-col">
                <div class="bracket-col-title">TỨ KẾT (QUARTER-FINALS)</div>
                <div class="bracket-match-list qf-spacing">
                    ${ko.qf.map((m) => buildMatchBox(m)).join("")}
                </div>
            </div>

            <div class="bracket-col">
                <div class="bracket-col-title">BÁN KẾT (SEMI-FINALS)</div>
                <div class="bracket-match-list sf-spacing">
                    ${ko.sf.map((m) => buildMatchBox(m)).join("")}
                </div>
            </div>

            <div class="bracket-col">
                <div class="bracket-col-title">CHUNG KẾT &amp; HẠNG 3</div>
                <div class="bracket-match-list final-spacing">
                    <div class="final-stage-label">🏆 GRAND FINAL 2026</div>
                    ${buildMatchBox(ko.final, true)}
                    <div class="third-stage-label">🥉 TRANH HẠNG BA</div>
                    ${buildMatchBox(ko.third_place, false)}
                </div>
            </div>
        </div>
    `;
}

function renderSimGroupsStandings(groups) {
    const groupsEl = document.getElementById("simGroupsView");
    if (!groupsEl || !groups) return;

    groupsEl.innerHTML = groups
        .map((g) => {
            const rowsHTML = g.standings
                .map(
                    (r) => `
                <tr class="${r.qualified ? "sim-row-qualified" : ""}">
                    <td><strong>${r.rank}</strong></td>
                    <td>
                        <div class="sim-team-cell">
                            <img src="${r.flag_url}" alt="" class="inline-flag" />
                            <span>${r.team}</span>
                            ${r.qualified ? '<span class="q-badge">Q</span>' : ""}
                        </div>
                    </td>
                    <td>${r.w}-${r.d}-${r.l}</td>
                    <td>${r.gf}:${r.ga} (${r.gd >= 0 ? "+" + r.gd : r.gd})</td>
                    <td><strong class="pts-cell">${r.pts}</strong></td>
                </tr>
            `
                )
                .join("");

            const matchesMini = g.matches
                .map(
                    (m) => `
                <div class="sim-mini-match" onclick="inspectSimulatedMatch('${m.team1.replace(/'/g, "\\'")}', '${m.team2.replace(/'/g, "\\'")}', 'Group Stage')">
                    <span>${m.team1}</span>
                    <strong>${m.score}</strong>
                    <span>${m.team2}</span>
                </div>
            `
                )
                .join("");

            return `
            <div class="sim-group-box" style="--grp-accent:${g.color}">
                <div class="sim-group-hdr">
                    <span>BẢNG ${g.group}</span>
                    <span class="sim-grp-sub">Top 1–2 đi tiếp</span>
                </div>
                <table class="sim-standings-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Đội tuyển</th>
                            <th>T-H-B</th>
                            <th>HS</th>
                            <th>Đ</th>
                        </tr>
                    </thead>
                    <tbody>${rowsHTML}</tbody>
                </table>
                <div class="sim-mini-matches-grid">${matchesMini}</div>
            </div>
        `;
        })
        .join("");
}

window.inspectSimulatedMatch = function (t1, t2, stage) {
    document.getElementById("team1Select").value = t1;
    document.getElementById("team2Select").value = t2;
    document.getElementById("stageSelect").value = stage;
    document.getElementById("yearSelect").value = "2026";
    syncSelectedTeamsUI();
    runPrediction(true);
    switchStage(1);
};

function renderTeamComparison(s1, s2) {
    if (!s1 || !s2) return;
    const container = document.getElementById("comparisonBars");
    const metrics = [
        { label: "WIN %", v1: s1.win_rate, v2: s2.win_rate, suffix: "%" },
        { label: "GOALS / MATCH", v1: s1.avg_goals_for, v2: s2.avg_goals_for, suffix: "" },
        { label: "CLEAN SHEET", v1: s1.clean_sheet_rate || 0, v2: s2.clean_sheet_rate || 0, suffix: "%" },
        { label: "WC MATCHES", v1: s1.played, v2: s2.played, suffix: "" },
    ];

    container.innerHTML = metrics
        .map((m) => {
            const total = m.v1 + m.v2 || 1;
            const p1 = Math.round((m.v1 / total) * 100);
            const p2 = 100 - p1;
            return `
            <div class="comp-row">
                <div class="comp-row-top">
                    <span style="color:#3d947b;font-weight:700">${m.v1}${m.suffix}</span>
                    <span>${m.label}</span>
                    <span style="color:#4c6fd1;font-weight:700">${m.v2}${m.suffix}</span>
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
            <td><strong style="color:#3d947b">${r.predicted_winner}</strong></td>
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
    switchStage(1);
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
