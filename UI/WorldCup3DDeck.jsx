import React, { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

/**
 * WorldCup3DDeck.jsx
 * ---------------------------------------------------------------------------
 * Production-ready Multi-Stage 3D Deck Component (React + Tailwind CSS + Framer Motion)
 * - Ultra-Minimalist Information Architecture (70-80% text reduction, visual badges & SVG cues)
 * - 5-Stage 3D Camera/Plane Transitions (rotateX, rotateY, translateZ, scale, blur)
 * - Floating Pill/Brutalist Dock Navigation + Keyboard Arrow Support
 * - Graceful `prefers-reduced-motion` Fallback
 */

const STAGES = [
  { id: 0, code: "01", key: "ARENA", label: "ARENA", title: "MATCH ARENA" },
  { id: 1, code: "02", key: "VERDICT", label: "VERDICT", title: "AI VERDICT & COUNCIL" },
  { id: 2, code: "03", key: "RADAR", label: "RADAR", title: "RADAR & POISSON MATRIX" },
  { id: 3, code: "04", key: "BRACKET", label: "BRACKET", title: "2026 BRACKET SIMULATOR" },
  { id: 4, code: "05", key: "VAULT", label: "VAULT", title: "GROUPS A–L & DATA VAULT" },
];

const EASE_OUT_EXPO = [0.22, 1, 0.36, 1];

export default function WorldCup3DDeck({ initialData = null }) {
  const [[activeStage, direction], setStageState] = useState([0, 0]);
  const prefersReducedMotion = useReducedMotion();

  const [matchState, setMatchState] = useState({
    team1: "Argentina",
    team2: "France",
    flag1: "https://flagcdn.com/w160/ar.png",
    flag2: "https://flagcdn.com/w160/fr.png",
    stage: "Final",
    year: 2026,
    score: "2 - 1",
    xg1: 1.84,
    xg2: 1.42,
    probs: { win: 46.8, draw: 24.5, loss: 28.7 },
    model: "VotingEnsemble",
    ...(initialData || {}),
  });

  const navigateToStage = useCallback(
    (targetIdx) => {
      const clamped = ((targetIdx % STAGES.length) + STAGES.length) % STAGES.length;
      if (clamped === activeStage) return;
      const dir = clamped > activeStage ? 1 : -1;
      setStageState([clamped, dir]);
    },
    [activeStage]
  );

  // Keyboard Left/Right navigation
  useEffect(() => {
    const onKeyDown = (e) => {
      if (["INPUT", "SELECT", "TEXTAREA"].includes(e.target?.tagName)) return;
      if (e.key === "ArrowRight") navigateToStage(activeStage + 1);
      if (e.key === "ArrowLeft") navigateToStage(activeStage - 1);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [activeStage, navigateToStage]);

  // 3D Camera / Plane Variants with Reduced Motion Fallback
  const stageVariants = {
    enter: (dir) =>
      prefersReducedMotion
        ? { opacity: 0 }
        : {
            opacity: 0,
            scale: 0.84,
            z: -320,
            rotateX: 14,
            rotateY: dir > 0 ? 24 : -24,
            x: dir > 0 ? "18%" : "-18%",
            filter: "blur(10px)",
          },
    center: {
      opacity: 1,
      scale: 1,
      z: 0,
      rotateX: 0,
      rotateY: 0,
      x: "0%",
      filter: "blur(0px)",
      transition: {
        duration: prefersReducedMotion ? 0.2 : 0.72,
        ease: EASE_OUT_EXPO,
      },
    },
    exit: (dir) =>
      prefersReducedMotion
        ? { opacity: 0, transition: { duration: 0.18 } }
        : {
            opacity: 0,
            scale: 0.82,
            z: -360,
            rotateX: 16,
            rotateY: dir > 0 ? -24 : 24,
            x: dir > 0 ? "-18%" : "18%",
            filter: "blur(12px)",
            transition: {
              duration: 0.62,
              ease: EASE_OUT_EXPO,
            },
          },
  };

  const currentMeta = STAGES[activeStage];

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-[#060814] text-slate-50 select-none flex flex-col">
      {/* Ambient Cyber-Grid & Radial Glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 opacity-25"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(0,240,255,0.12) 1px, transparent 1px), linear-gradient(to bottom, rgba(168,85,247,0.12) 1px, transparent 1px)",
          backgroundSize: "52px 52px",
        }}
      />

      {/* Minimal Top HUD */}
      <header className="relative z-30 mx-auto mt-3 flex w-[95%] max-w-7xl items-center justify-between rounded-2xl border-2 border-slate-100/90 bg-slate-900/75 px-5 py-3 backdrop-blur-xl shadow-[5px_5px_0px_#00f0ff]">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl border-2 border-white bg-gradient-to-br from-emerald-400 via-cyan-400 to-purple-500 text-lg shadow-[3px_3px_0px_#000]">
            🏆
          </div>
          <div>
            <span className="block font-mono text-[10px] tracking-[0.22em] text-cyan-300">
              FIFA WC 2026 • 3D DECK
            </span>
            <h1 className="text-lg font-black tracking-wider uppercase bg-gradient-to-r from-white via-cyan-300 to-pink-400 bg-clip-text text-transparent">
              WORLD CUP AI ARENA
            </h1>
          </div>
        </div>

        {/* Stage Indicator Pill */}
        <div className="hidden md:flex items-center gap-2.5 rounded-full border-2 border-cyan-400 bg-slate-950/90 px-4 py-1.5 shadow-[3px_3px_0px_#00f0ff]">
          <span className="font-mono text-xs font-bold text-emerald-400">
            {currentMeta.code} / 05
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
          <span className="font-mono text-xs font-extrabold tracking-widest text-white">
            {currentMeta.title}
          </span>
        </div>

        {/* Compact KPI Badges */}
        <div className="flex items-center gap-2">
          <div className="rounded-xl border border-cyan-400/50 bg-slate-950/80 px-3 py-1 text-right">
            <span className="block font-mono text-[9px] text-slate-400">MATCHES</span>
            <strong className="font-mono text-xs text-emerald-400">964</strong>
          </div>
          <div className="rounded-xl border border-purple-400/50 bg-slate-950/80 px-3 py-1 text-right">
            <span className="block font-mono text-[9px] text-slate-400">ENGINE</span>
            <strong className="font-mono text-xs text-cyan-300">{matchState.model}</strong>
          </div>
        </div>
      </header>

      {/* 3D Perspective Viewport */}
      <main
        className="relative flex-1 w-full overflow-y-auto overflow-x-hidden px-4 pt-5 pb-28 flex items-center justify-center"
        style={{ perspective: "1200px" }}
      >
        <div
          className="relative w-full max-w-6xl"
          style={{ transformStyle: "preserve-3d" }}
        >
          <AnimatePresence initial={false} custom={direction} mode="wait">
            <motion.section
              key={activeStage}
              custom={direction}
              variants={stageVariants}
              initial="enter"
              animate="center"
              exit="exit"
              style={{
                transformStyle: "preserve-3d",
                willChange: "transform, opacity",
              }}
              className="w-full rounded-3xl border-2 border-slate-100/90 bg-slate-900/75 p-6 md:p-8 backdrop-blur-2xl shadow-[8px_8px_0px_#000000]"
            >
              {activeStage === 0 && (
                <ArenaStage
                  state={matchState}
                  setState={setMatchState}
                  onPredict={() => navigateToStage(1)}
                />
              )}
              {activeStage === 1 && (
                <VerdictStage
                  state={matchState}
                  onNext={() => navigateToStage(2)}
                />
              )}
              {activeStage === 2 && <RadarMatrixStage state={matchState} />}
              {activeStage === 3 && <BracketStage onInspect={() => navigateToStage(1)} />}
              {activeStage === 4 && <VaultStage onSelectMatch={() => navigateToStage(1)} />}
            </motion.section>
          </AnimatePresence>
        </div>
      </main>

      {/* Fixed Floating 3D Dock Navigation */}
      <nav
        aria-label="3D Stage Navigation"
        className="fixed bottom-4 left-1/2 z-40 -translate-x-1/2 flex items-center gap-1.5 rounded-full border-2 border-white bg-slate-950/90 px-3 py-2 backdrop-blur-2xl shadow-[6px_6px_0px_#000000,0_15px_35px_rgba(0,240,255,0.22)]"
      >
        <button
          type="button"
          onClick={() => navigateToStage(activeStage - 1)}
          aria-label="Previous Stage"
          className="grid h-9 w-9 place-items-center rounded-full border border-slate-700 bg-slate-900 text-xs font-bold text-slate-200 hover:border-cyan-400 hover:text-cyan-300 transition"
        >
          ◀
        </button>

        {STAGES.map((st) => {
          const isActive = st.id === activeStage;
          return (
            <button
              key={st.key}
              type="button"
              onClick={() => navigateToStage(st.id)}
              className={`relative flex items-center gap-1.5 rounded-full px-3.5 py-2 font-mono text-[11px] font-bold tracking-wider transition-all ${
                isActive
                  ? "bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950 shadow-[2px_2px_0px_#ffffff] -translate-y-0.5"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <span className="opacity-70">{st.code}</span>
              <span>{st.label}</span>
            </button>
          );
        })}

        <button
          type="button"
          onClick={() => navigateToStage(activeStage + 1)}
          aria-label="Next Stage"
          className="grid h-9 w-9 place-items-center rounded-full border border-slate-700 bg-slate-900 text-xs font-bold text-slate-200 hover:border-cyan-400 hover:text-cyan-300 transition"
        >
          ▶
        </button>
      </nav>
    </div>
  );
}

/* ============================================================================
   STAGE 01: MATCH ARENA (ULTRA-MINIMALIST)
   ============================================================================ */
function ArenaStage({ state, onPredict }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded-md bg-emerald-400 px-2.5 py-1 font-mono text-xs font-black text-slate-950">
            STAGE 01
          </span>
          <h2 className="text-xl font-black tracking-wider uppercase">MATCH ARENA</h2>
        </div>
        <span className="rounded-full border border-cyan-400/50 bg-cyan-400/10 px-3 py-1 font-mono text-xs font-bold text-cyan-300">
          {state.stage} • {state.year}
        </span>
      </div>

      {/* 3D Contender Cards */}
      <div className="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
        <div className="md:col-span-5 rounded-2xl border-2 border-emerald-400/80 bg-slate-950/70 p-5 text-center shadow-[5px_5px_0px_#00f5a0]">
          <span className="font-mono text-[10px] font-bold tracking-widest text-emerald-400">
            CONTENDER A
          </span>
          <img
            src={state.flag1}
            alt={state.team1}
            className="mx-auto my-3 h-16 w-24 rounded-lg border-2 border-white object-cover shadow-md"
          />
          <div className="text-2xl font-black uppercase tracking-wide">{state.team1}</div>
          <div className="mt-2 flex justify-center gap-2 font-mono text-xs text-slate-400">
            <span className="rounded bg-slate-900 px-2 py-0.5 text-emerald-300">WIN 64%</span>
            <span className="rounded bg-slate-900 px-2 py-0.5 text-cyan-300">xG {state.xg1}</span>
          </div>
        </div>

        <div className="md:col-span-1 flex flex-col items-center justify-center">
          <div className="grid h-14 w-14 place-items-center rounded-full border-2 border-white bg-gradient-to-br from-pink-500 to-amber-400 font-black text-slate-950 shadow-[4px_4px_0px_#000]">
            VS
          </div>
        </div>

        <div className="md:col-span-5 rounded-2xl border-2 border-cyan-400/80 bg-slate-950/70 p-5 text-center shadow-[5px_5px_0px_#00f0ff]">
          <span className="font-mono text-[10px] font-bold tracking-widest text-cyan-300">
            CONTENDER B
          </span>
          <img
            src={state.flag2}
            alt={state.team2}
            className="mx-auto my-3 h-16 w-24 rounded-lg border-2 border-white object-cover shadow-md"
          />
          <div className="text-2xl font-black uppercase tracking-wide">{state.team2}</div>
          <div className="mt-2 flex justify-center gap-2 font-mono text-xs text-slate-400">
            <span className="rounded bg-slate-900 px-2 py-0.5 text-cyan-300">WIN 59%</span>
            <span className="rounded bg-slate-900 px-2 py-0.5 text-purple-300">xG {state.xg2}</span>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={onPredict}
        className="w-full rounded-2xl border-2 border-white bg-gradient-to-r from-emerald-400 via-cyan-400 to-purple-500 py-4 text-center font-black tracking-widest text-slate-950 uppercase shadow-[6px_6px_0px_#000] hover:-translate-y-0.5 transition"
      >
        ⚡ PREDICT &amp; ENTER 3D VERDICT →
      </button>
    </div>
  );
}

/* ============================================================================
   STAGE 02: AI VERDICT & COUNCIL
   ============================================================================ */
function VerdictStage({ state, onNext }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <span className="rounded-md bg-cyan-400 px-2.5 py-1 font-mono text-xs font-black text-slate-950">
          STAGE 02 • AI VERDICT
        </span>
        <button
          type="button"
          onClick={onNext}
          className="rounded-xl border border-cyan-400 px-3 py-1 font-mono text-xs font-bold text-cyan-300 hover:bg-cyan-400/10"
        >
          RADAR &amp; MATRIX →
        </button>
      </div>

      <div className="rounded-2xl border-2 border-white/80 bg-slate-950/80 p-6 text-center shadow-[5px_5px_0px_#00f5a0]">
        <div className="font-mono text-xs text-slate-400 uppercase">
          {state.stage} • WC {state.year}
        </div>
        <div className="my-3 text-5xl font-black tracking-widest text-white">
          {state.score}
        </div>
        <span className="inline-block rounded-full border-2 border-white bg-emerald-400 px-4 py-1 font-mono text-xs font-black text-slate-950">
          🏆 {state.team1.toUpperCase()} WIN ({state.probs.win}%)
        </span>

        {/* Tri-color Probability Bar */}
        <div className="mt-5 h-4 w-full overflow-hidden rounded-full border border-white/60 flex">
          <div style={{ width: `${state.probs.win}%` }} className="bg-emerald-400" />
          <div style={{ width: `${state.probs.draw}%` }} className="bg-amber-400" />
          <div style={{ width: `${state.probs.loss}%` }} className="bg-cyan-400" />
        </div>
        <div className="mt-2 flex justify-between font-mono text-xs font-bold">
          <span className="text-emerald-400">{state.team1}: {state.probs.win}%</span>
          <span className="text-amber-300">DRAW: {state.probs.draw}%</span>
          <span className="text-cyan-300">{state.team2}: {state.probs.loss}%</span>
        </div>
      </div>
    </div>
  );
}

/* ============================================================================
   STAGE 03: RADAR & POISSON MATRIX
   ============================================================================ */
function RadarMatrixStage({ state }) {
  const topScores = [
    { score: "2 - 1", prob: "14.8%" },
    { score: "1 - 1", prob: "12.4%" },
    { score: "1 - 0", prob: "10.9%" },
    { score: "2 - 0", prob: "9.2%" },
  ];
  return (
    <div className="space-y-5">
      <span className="rounded-md bg-purple-400 px-2.5 py-1 font-mono text-xs font-black text-slate-950">
        STAGE 03 • 5-AXIS RADAR &amp; POISSON
      </span>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {topScores.map((item, i) => (
          <div
            key={item.score}
            className="rounded-xl border border-slate-700 bg-slate-950/80 p-4 text-center shadow-[4px_4px_0px_#000]"
          >
            <span className="font-mono text-[10px] text-cyan-300">#{i + 1} EXACT SCORE</span>
            <div className="my-1 text-2xl font-black text-white">{item.score}</div>
            <span className="font-mono text-xs font-bold text-emerald-400">{item.prob}</span>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 font-mono text-xs text-slate-300 flex justify-between">
        <span>{state.team1} xG: {state.xg1}</span>
        <span>5x5 POISSON GOAL DISTRIBUTION</span>
        <span>{state.team2} xG: {state.xg2}</span>
      </div>
    </div>
  );
}

/* ============================================================================
   STAGE 04: 2026 BRACKET SIMULATOR
   ============================================================================ */
function BracketStage({ onInspect }) {
  const koMatches = [
    { round: "SEMI-FINAL 1", t1: "Argentina", t2: "Spain", score: "2 - 1" },
    { round: "SEMI-FINAL 2", t1: "France", t2: "Brazil", score: "2 - 2 (P)" },
    { round: "GRAND FINAL", t1: "Argentina", t2: "France", score: "2 - 1" },
  ];
  return (
    <div className="space-y-5">
      <span className="rounded-md bg-amber-400 px-2.5 py-1 font-mono text-xs font-black text-slate-950">
        STAGE 04 • 88-MATCH SIMULATOR
      </span>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {koMatches.map((m) => (
          <button
            key={m.round}
            type="button"
            onClick={onInspect}
            className="rounded-2xl border-2 border-white/80 bg-slate-950/80 p-4 text-left shadow-[4px_4px_0px_#00f0ff] hover:-translate-y-0.5 transition"
          >
            <div className="font-mono text-[10px] font-bold text-amber-300">{m.round}</div>
            <div className="mt-2 flex items-center justify-between font-bold">
              <span>{m.t1} vs {m.t2}</span>
              <span className="rounded bg-emerald-400 px-2 py-0.5 font-mono text-xs text-slate-950">
                {m.score}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ============================================================================
   STAGE 05: GROUPS A–L & DATA VAULT
   ============================================================================ */
function VaultStage({ onSelectMatch }) {
  const sampleGroups = [
    { g: "A", teams: ["USA", "Morocco", "Scotland", "Costa Rica"] },
    { g: "B", teams: ["Mexico", "Japan", "Ecuador", "Wales"] },
    { g: "C", teams: ["Argentina", "South Korea", "Algeria", "Norway"] },
    { g: "D", teams: ["France", "Colombia", "Senegal", "Canada"] },
  ];
  return (
    <div className="space-y-5">
      <span className="rounded-md bg-pink-400 px-2.5 py-1 font-mono text-xs font-black text-slate-950">
        STAGE 05 • GROUPS A–L &amp; SQLITE VAULT
      </span>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {sampleGroups.map((grp) => (
          <div
            key={grp.g}
            onClick={onSelectMatch}
            className="cursor-pointer rounded-2xl border border-slate-700 bg-slate-950/80 p-3.5 shadow-[4px_4px_0px_#000] hover:border-cyan-400 transition"
          >
            <div className="font-mono text-xs font-black text-cyan-300">GROUP {grp.g}</div>
            <ul className="mt-2 space-y-1 text-xs font-semibold text-slate-200">
              {grp.teams.map((t) => (
                <li key={t} className="truncate">• {t}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
