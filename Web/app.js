"use strict";
/* app.js - de interface van 2048 Arena in de browser.
 *
 * De spelregels en de AI draaien in Python (app.py). Deze code:
 *   1. tekent het juiste scherm (start, singleplayer, versus, kamer, einde),
 *   2. stuurt elke zet naar de server met fetch("/api/...") en tekent het antwoord.
 */

const TARGETS = [1000, 2500, 5000];
const MODES = [["single", "Singleplayer"], ["bot", "Tegen bot"], ["friend", "Tegen vriend"]];
const DIFFS = [["easy", "Easy"], ["middel", "Middel"], ["hard", "Hard"]];
const DIFF_HELP = {
  easy: "Easy: de bot kiest de zet die nu de meeste punten geeft en maakt vaak een foutje.",
  middel: "Middel: de bot kijkt één nieuwe tegel vooruit (expectimax) en maakt soms een foutje.",
  hard: "Hard: de bot kijkt twee tot drie tegels vooruit (expectimax) en maakt geen fouten.",
};
// e.code = de plaats van de toets, dus op azerty werken Z Q S D vanzelf ook
const KEYS = {
  ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down",
  KeyA: "left", KeyD: "right", KeyW: "up", KeyS: "down",
};

// alles wat de interface moet onthouden
const S = {
  screen: "start",  // start | single | versus | lobby | end
  mode: "bot", diff: "middel", target: 5000,
  game: null, gameId: null,
  room: null,       // {code, token, role, address}
  roomState: null, shownRound: 0,
  lobbyError: "", joinText: "",
};
let gen = 0;          // verhoogt bij elk nieuw spel, zodat oude timers niets meer doen
let busy = false, botTimer = null, endTimer = null, pollTimer = null, polling = false;
let prevBoards = {};  // vorige borden, om nieuwe tegels te laten "poppen"

const app = document.getElementById("app");

// ================================================================ hulpjes
const fmt = n => Math.trunc(n).toLocaleString("en-US").replace(/,/g, " ");
const esc = s => String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const diffLabel = k => (DIFFS.find(d => d[0] === k) || ["", k])[1];

async function api(action, data = {}) {
  const res = await fetch("/api/" + action, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || "Er ging iets mis met de server.");
  return json;
}

let toastTimer = null;
function toast(msg, bad = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "show" + (bad ? " bad" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = ""), 2200);
}

function loadBest() { try { return +localStorage.getItem("best2048") || 0; } catch { return 0; } }
function saveBest(n) { try { localStorage.setItem("best2048", n); } catch { /* geen opslag */ } }

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {  // via een gewoon IP-adres (geen https) bestaat navigator.clipboard niet
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  toast("Gekopieerd!");
}

// ======================================================= bouwstenen (HTML)
function segment(items, selected, action, style = "light") {
  return `<div class="segment ${style}">` + items.map(([key, label]) =>
    `<button class="seg ${String(key) === String(selected) ? "on" : ""}" data-action="${action}" data-value="${key}">${esc(label)}</button>`
  ).join("") + `</div>`;
}

function header(subtitle, withTabs = false, withDiff = false) {
  let right = "";
  if (withTabs) {
    right = `<div class="header-right">${withDiff ? segment(DIFFS, S.diff, "set-diff") : ""}${segment(MODES, S.mode, "switch-mode", "orange")}</div>`;
  }
  return `<header class="top">
    <div class="logo-wrap" data-action="menu" title="Terug naar het menu">
      <div class="logo">2048</div>
      <div><div class="brand">2048 Arena</div>${subtitle ? `<div class="sub">${esc(subtitle)}</div>` : ""}</div>
    </div>${right}</header>`;
}

function boardHTML(board, key, color, overlay = "") {
  const prev = prevBoards[key];
  let cells = "";
  board.forEach((row, r) => row.forEach((v, c) => {
    if (!v) { cells += `<div class="tile"></div>`; return; }
    const pop = prev && prev[r][c] !== v ? " pop" : "";
    cells += `<div class="tile t${v > 2048 ? "big" : v} d${String(v).length}${pop}">${v}</div>`;
  }));
  prevBoards[key] = board;
  return `<div class="board ${color}">${cells}${overlay ? `<div class="board-overlay">${esc(overlay)}</div>` : ""}</div>`;
}

function stat(label, value, color = "") {
  return `<div class="stat"><div class="k">${label}</div><div class="v ${color}">${value}</div></div>`;
}

// ================================================================ schermen
function renderStart() {
  const cards = [
    ["single", "Alleen", "Singleplayer", "Speel alleen en probeer de 2048-tegel te halen. Je score wordt bijgehouden."],
    ["bot", "Tegen de computer", "Tegen de bot", "Jij links, de bot rechts. Om de beurt een zet. Wie als eerste de doelscore haalt, wint."],
    ["friend", "Met een ander", "Tegen een vriend", "Maak een kamer en deel de code. Jullie spelen om de beurt op je eigen toestel."],
  ];
  let html = header("Schuif tegels, combineer, haal als eerste 2048") +
    `<main class="page"><h1>Hoe wil je spelen?</h1>
     <p class="lead">Kies een modus. De AI draait in Python op deze computer.</p><div class="cards">`;
  for (const [key, tag, title, desc] of cards) {
    const sel = S.mode === key;
    html += `<button class="mode-card ${sel ? "selected" : ""}" data-action="pick-mode" data-value="${key}">
      <div class="eyebrow">${sel ? "Geselecteerd" : tag}</div>
      <div class="card-title">${title}</div><p>${desc}</p></button>`;
  }
  html += `</div><div class="options">`;
  if (S.mode === "bot") {
    html += `<div><div class="label">Moeilijkheid van de bot</div>${segment(DIFFS, S.diff, "pick-diff")}
             <p class="hint">${DIFF_HELP[S.diff]}</p></div>`;
  }
  if (S.mode !== "single") {
    html += `<div><div class="label">Doelscore</div>${segment(TARGETS.map(t => [t, fmt(t)]), S.target, "pick-target")}
             <p class="hint">Wie dit als eerste haalt, wint.</p></div>`;
  }
  return html + `</div><button class="btn primary big" data-action="start">Start spel</button></main>`;
}

function renderSingle() {
  const g = S.game;
  const best = Math.max(loadBest(), g.you.score);
  saveBest(best);
  return header("Schuif tegels, combineer, haal als eerste 2048", true) +
    `<main class="single">
      ${boardHTML(g.you.board, "you", "orange", g.over ? "Geen zetten meer" : "")}
      <aside class="side">
        <div class="score-card"><div class="eyebrow">Score</div><div class="num">${fmt(g.you.score)}</div></div>
        <div class="stats">${stat("BESTE", fmt(best))}${stat("HOOGSTE TEGEL", fmt(g.you.highest))}</div>
        <button class="btn light" data-action="new-game">Nieuw spel</button>
        <button class="btn ghost" data-action="undo" ${g.can_undo && !g.over ? "" : "disabled"}>Zet ongedaan maken</button>
        <p class="hint">Bediening: pijltjestoetsen of W A S D (Z Q S D op azerty). Op een gsm: vegen.</p>
      </aside></main>`;
}

function renderVersus() {
  const g = S.game;
  const isBot = g.mode === "bot";
  const oppName = isBot ? "Bot" : "Vriend";
  const oppTag = isBot ? diffLabel(g.diff).toUpperCase() : (S.room && S.room.role === "host" ? "SPELER 2" : "HOST");

  const column = (name, tag, p, color, key) => `
    <section class="player">
      <div class="player-head"><div class="who"><span class="dot ${color}"></span>${name}</div><span class="tag">${tag}</span></div>
      <div class="stats">${stat("SCORE", fmt(p.score), color)}${stat("HOOGSTE TEGEL", fmt(p.highest))}</div>
      ${boardHTML(p.board, key, color, p.stuck ? "Vast!" : "")}
    </section>`;

  const bar = (name, score, color) => {
    const pct = Math.min(100, Math.floor(score * 100 / g.target));
    return `<div class="bar-row"><span>${name}</span><span>${pct}%</span></div>
            <div class="bar ${color}"><span style="width:${pct}%"></span></div>`;
  };

  let pill;
  if (g.winner) pill = `<div class="pill done"><span class="dot"></span>Ronde voorbij</div>`;
  else if (g.turn === "you") pill = `<div class="pill"><span class="dot"></span>Jouw beurt</div>`;
  else pill = `<div class="pill blue"><span class="dot"></span>Beurt van ${oppName.toLowerCase()}</div>`;

  let footer;
  if (g.winner) footer = "";
  else if (isBot) footer = g.turn === "opp" ? "De bot denkt na..." : "De bot wacht op zijn beurt.";
  else footer = g.turn === "opp" ? "Wacht op de zet van je vriend..." : "Jouw beurt: speel met de pijltjes of W A S D.";

  return header("Schuif tegels, combineer, haal als eerste de doelscore", true, isBot) +
    `<main class="versus">
      ${column("Jij", "W A S D", g.you, "orange", "you")}
      <div class="mid">
        <div class="vs">VS</div>
        ${pill}
        <div class="goal"><div class="k">EERSTE NAAR</div><div class="num">${fmt(g.target)}</div>
          ${bar("Jij", g.you.score, "")}${bar(oppName, g.opp.score, "blue")}</div>
        <div class="move-nr">Zet ${g.moves}</div>
        <button class="btn light" data-action="new-game">Nieuw spel</button>
      </div>
      ${column(oppName, oppTag, g.opp, "blue", "opp")}
    </main>
    <p class="footer">${footer}</p>`;
}

function renderLobby() {
  let html = header("Schuif tegels, combineer, haal als eerste de doelscore", true) +
    `<main class="page"><h1>Speel tegen een vriend</h1>
     <p class="lead">Jullie spelen om de beurt, elk op een eigen toestel in hetzelfde netwerk.</p>`;
  const room = S.room, rs = S.roomState;
  const error = S.lobbyError ? `<p class="error">${esc(S.lobbyError)}</p>` : "";

  const joinPanel = `
    <div class="panel">
      <h2>Doe mee aan een kamer</h2>
      <div class="label">Kamercode van je vriend</div>
      <input id="join-input" maxlength="80" autocomplete="off" spellcheck="false" placeholder="bijv. 4F7K" value="${esc(S.joinText)}">
      <button class="btn blue wide" data-action="join">Verbinden</button>
      <p class="hint">Zelfde wifi nodig. Je vriend opent het adres van jouw computer, zoals in de link hiernaast. Je mag ook de hele link plakken.</p>
      ${room && room.role === "guest" ? "" : error}
    </div>`;

  if (!room) {  // er is (nog) geen kamer, bv. na een fout
    return html + `<div class="lobby"><div class="panel orange"><h2>Maak een kamer</h2>
      <button class="btn primary wide" data-action="create-room">Nieuwe kamer maken</button></div>${joinPanel}</div></main>`;
  }

  if (room.role === "guest") {
    return html + `<div class="lobby"><div class="panel blue">
      <h2>Verbonden met kamer ${esc(room.code)}</h2>
      <p class="lead">De host kiest de doelscore${rs ? ` (nu ${fmt(rs.target)})` : ""} en start het spel.</p>
      ${error}
      <button class="btn ghost" style="margin-top:28px" data-action="cancel-join">Annuleren</button>
    </div></div></main>`;
  }

  const connected = rs && rs.connected;
  const target = rs ? rs.target : S.target;
  html += `<div class="lobby">
    <div class="panel orange">
      <h2>Maak een kamer</h2>
      <div class="label">Kamercode</div>
      <div class="code-row"><div class="code">${esc(room.code)}</div>
        <button class="btn ghost" data-action="copy" data-value="${esc(room.code)}">Kopieer code</button></div>
      <div class="label">Of deel de link</div>
      <button class="field" data-action="copy" data-value="${esc(room.address)}" title="Klik om te kopiëren">${esc(room.address)}</button>
      <div class="slots">
        <div class="slot"><span class="name"><span class="dot"></span>Speler 1 (jij)</span><span class="state">Klaar</span></div>
        <div class="slot ${connected ? "" : "waiting"}"><span class="name"><span class="dot blue"></span>${connected ? "Speler 2 (vriend)" : "Speler 2"}</span>
          <span class="state">${connected ? "Klaar" : "Wacht op vriend..."}</span></div>
      </div>
      <div class="label">Doelscore</div>
      ${segment(TARGETS.map(t => [t, fmt(t)]), target, "set-room-target")}
      ${connected
        ? `<button class="btn primary wide" data-action="room-start">Start spel</button>`
        : `<button class="btn wide" disabled>Start zodra je vriend erbij is</button>`}
    </div>
    ${joinPanel}
  </div></main>`;
  return html;
}

function renderEnd() {
  const g = S.game;
  const menu = `<button class="btn ghost" data-action="menu">Terug naar menu</button>`;

  if (g.mode === "single") {
    return header("") + `<main class="end">
      <div class="eyebrow">Einde van het spel</div>
      <h1>Geen zetten meer</h1>
      <p class="lead">Je eindscore is ${fmt(g.you.score)}.</p>
      <div class="result-cards">
        <div class="result win-you"><div class="name">Score</div><div class="num orange">${fmt(g.you.score)}</div></div>
        <div class="result"><div class="name">Hoogste tegel</div><div class="num">${fmt(g.you.highest)}</div></div>
      </div>
      <div class="end-buttons"><button class="btn primary" data-action="new-game">Nieuw spel</button>${menu}</div></main>`;
  }

  const isBot = g.mode === "bot";
  const oppName = isBot ? `Bot (${diffLabel(g.diff)})` : "Vriend";
  const other = isBot ? "de bot" : "je vriend";
  let cls = "", title, sub;
  if (g.winner === "you") {
    title = "Je hebt gewonnen!";
    sub = g.reason === "target" ? `Jij haalde als eerste de doelscore van ${fmt(g.target)}.`
                                : `Er waren geen zetten meer en jij had de hoogste score.`;
  } else if (g.winner === "opp") {
    cls = "lost";
    title = isBot ? "De bot heeft gewonnen" : "Je vriend heeft gewonnen";
    sub = g.reason === "target" ? `${other[0].toUpperCase() + other.slice(1)} haalde als eerste de doelscore van ${fmt(g.target)}.`
                                : `Er waren geen zetten meer en ${other} had de hoogste score.`;
  } else {
    cls = "draw";
    title = "Gelijkspel!";
    sub = "Er waren geen zetten meer en jullie scores zijn gelijk.";
  }
  return header("") + `<main class="end ${cls}">
    <div class="eyebrow">Einde van de ronde</div>
    <h1>${title}</h1>
    <p class="lead">${sub}</p>
    <div class="result-cards">
      <div class="result ${g.winner === "you" ? "win-you" : ""}"><div class="name">Jij</div>
        <div class="num orange">${fmt(g.you.score)}</div><div class="small">Hoogste tegel ${fmt(g.you.highest)}</div></div>
      <div class="result ${g.winner === "opp" ? "win-opp" : ""}"><div class="name">${oppName}</div>
        <div class="num blue">${fmt(g.opp.score)}</div><div class="small">Hoogste tegel ${fmt(g.opp.highest)}</div></div>
    </div>
    <div class="end-buttons"><button class="btn primary" data-action="new-game">Revanche</button>${menu}</div></main>`;
}

function render() {
  const focusId = document.activeElement && document.activeElement.id;
  const screens = { start: renderStart, single: renderSingle, versus: renderVersus, lobby: renderLobby, end: renderEnd };
  app.innerHTML = screens[S.screen]();
  if (focusId) {  // focus (bv. in het invoerveld) behouden na het hertekenen
    const el = document.getElementById(focusId);
    if (el) { el.focus(); if (el.setSelectionRange) el.setSelectionRange(el.value.length, el.value.length); }
  }
}

// ====================================================== spelverloop
function stopAll() {
  gen++;
  clearTimeout(botTimer);
  clearTimeout(endTimer);
  endTimer = null;
  busy = false;
  prevBoards = {};
}

function setGame(state) {
  S.game = state;
  if (S.screen !== "end") render();
  const finished = state.mode === "single" ? state.over : !!state.winner;
  if (finished) showEndSoon();
  else scheduleBot();
}

function showEndSoon() {  // eerst het eindbord even tonen, dan het eindscherm
  if (endTimer || S.screen === "end") return;
  const my = gen;
  endTimer = setTimeout(() => {
    endTimer = null;
    if (my === gen) { S.screen = "end"; render(); }
  }, 1300);
}

function scheduleBot() {
  const g = S.game;
  clearTimeout(botTimer);
  if (!g || g.mode !== "bot" || g.winner || g.turn !== "opp") return;
  const my = gen;
  botTimer = setTimeout(async () => {
    try {
      const st = await api("bot", { id: S.gameId });
      if (my === gen) setGame(st);
    } catch (e) { if (my === gen) toast(e.message, true); }
  }, g.delay);
}

async function startGame(data, screen) {
  stopAll();
  const my = gen;
  try {
    const st = await api("start", data);
    if (my !== gen) return;
    S.gameId = st.id;
    S.screen = screen;
    setGame(st);
  } catch (e) { toast(e.message, true); }
}

const startSingle = () => startGame({ mode: "single" }, "single");
const startBot = () => startGame({ mode: "bot", diff: S.diff, target: S.target }, "versus");

function startMode(mode) {
  if (mode !== "friend") leaveRoom();
  S.mode = mode;
  if (mode === "single") startSingle();
  else if (mode === "bot") startBot();
  else openLobby();
}

async function doMove(dir) {
  const g = S.game;
  if (busy || !g) return;
  let action, data;
  if (S.screen === "single" && !g.over) {
    action = "move"; data = { id: S.gameId, dir };
  } else if (S.screen === "versus" && !g.winner && g.turn === "you") {
    if (g.mode === "bot") { action = "move"; data = { id: S.gameId, dir }; }
    else { action = "room/move"; data = { code: S.room.code, token: S.room.token, dir }; }
  } else return;

  busy = true;
  const my = gen;
  try {
    const st = await api(action, data);
    if (my === gen) setGame(g.mode === "friend" ? { ...st, mode: "friend" } : st);
  } catch (e) { toast(e.message, true); }
  finally { if (my === gen) busy = false; }
}

async function undo() {
  try { setGame(await api("undo", { id: S.gameId })); } catch (e) { toast(e.message, true); }
}

// ================================================== tegen een vriend
function openLobby() {
  stopAll();
  S.mode = "friend";
  S.screen = "lobby";
  S.lobbyError = "";
  if (S.room) { render(); startPolling(); }
  else createRoom();
}

async function createRoom() {
  try {
    const r = await api("room/create", { target: S.target });
    S.room = { code: r.code, token: r.token, role: "host", address: r.address };
    S.roomState = null;
    S.shownRound = 0;
    S.lobbyError = "";
    startPolling();
  } catch (e) { S.lobbyError = e.message; }
  render();
}

async function joinRoom(text) {
  const code = text.trim().replace(/\/+$/, "").split("/").pop().toUpperCase();
  S.mode = "friend";
  S.screen = "lobby";
  if (!code) { S.lobbyError = "Vul eerst de kamercode van je vriend in."; render(); return; }
  if (S.room && S.room.code === code) { S.lobbyError = "Dat is je eigen kamer. Geef deze code aan je vriend."; render(); return; }
  try {
    const r = await api("room/join", { code });
    leaveRoom();
    S.room = { code: r.code, token: r.token, role: "guest" };
    S.roomState = null;
    S.shownRound = 0;
    S.joinText = "";
    S.lobbyError = "";
    startPolling();
  } catch (e) { S.lobbyError = e.message; }
  render();
}

function leaveRoom() {
  if (!S.room) return;
  api("room/leave", { code: S.room.code, token: S.room.token }).catch(() => {});
  S.room = null;
  S.roomState = null;
  stopPolling();
}

async function roomCall(action, extra = {}) {
  if (!S.room) return;
  try {
    await api(action, { code: S.room.code, token: S.room.token, ...extra });
    pollRoom();
  } catch (e) { toast(e.message, true); }
}

function startPolling() { if (!pollTimer) pollTimer = setInterval(pollRoom, 500); }
function stopPolling() { clearInterval(pollTimer); pollTimer = null; }

// elke halve seconde vragen we de server hoe de kamer ervoor staat
async function pollRoom() {
  const room = S.room;
  if (!room || polling) return;
  polling = true;
  try {
    const st = await api("room/state", { code: room.code, token: room.token });
    if (S.room !== room) return;
    if (JSON.stringify(st) === JSON.stringify(S.roomState)) return;  // niets veranderd
    S.roomState = st;
    if (st.match) {
      if (st.round !== S.shownRound) {  // nieuwe ronde gestart
        stopAll();
        S.shownRound = st.round;
        S.screen = "versus";
      }
      if (S.screen === "versus" || S.screen === "end") setGame({ ...st.match, mode: "friend" });
    } else if (S.screen === "lobby") {
      render();
    }
  } catch (e) {
    if (S.room === room) {  // kamer gesloten of server weg
      S.room = null;
      S.roomState = null;
      stopPolling();
      stopAll();
      S.lobbyError = "De kamer is gesloten of de verbinding is verbroken.";
      if (S.screen !== "start") { S.screen = "lobby"; render(); }
    }
  } finally { polling = false; }
}

// ============================================================ invoer
const actions = {
  "menu": () => { leaveRoom(); stopAll(); S.screen = "start"; render(); },
  "pick-mode": v => { S.mode = v; render(); },
  "pick-diff": v => { S.diff = v; render(); },
  "pick-target": v => { S.target = +v; render(); },
  "start": () => startMode(S.mode),
  "switch-mode": v => { if (v !== S.mode) startMode(v); },
  "set-diff": v => { S.diff = v; startBot(); },
  "new-game": () => (S.mode === "friend" ? roomCall("room/start") : startMode(S.mode)),
  "undo": undo,
  "copy": v => copyText(v),
  "join": () => joinRoom(S.joinText),
  "cancel-join": () => { leaveRoom(); createRoom(); },
  "create-room": createRoom,
  "set-room-target": v => { S.target = +v; roomCall("room/target", { target: +v }); },
  "room-start": () => roomCall("room/start"),
};

document.addEventListener("click", e => {
  const el = e.target.closest("[data-action]");
  if (el && !el.disabled) actions[el.dataset.action](el.dataset.value);
});

document.addEventListener("input", e => {
  if (e.target.id === "join-input") S.joinText = e.target.value;
});

document.addEventListener("keydown", e => {
  if (e.target.id === "join-input") {
    if (e.key === "Enter") joinRoom(S.joinText);
    return;
  }
  const dir = KEYS[e.code];
  if (dir && (S.screen === "single" || S.screen === "versus")) {
    e.preventDefault();
    doMove(dir);
  }
});

// vegen op een gsm of tablet
let touchStart = null;
document.addEventListener("touchstart", e => {
  if (e.touches.length === 1) touchStart = [e.touches[0].clientX, e.touches[0].clientY];
}, { passive: true });
document.addEventListener("touchend", e => {
  if (!touchStart) return;
  const dx = e.changedTouches[0].clientX - touchStart[0];
  const dy = e.changedTouches[0].clientY - touchStart[1];
  touchStart = null;
  if (Math.max(Math.abs(dx), Math.abs(dy)) < 30) return;
  if (S.screen === "single" || S.screen === "versus") {
    doMove(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "right" : "left") : (dy > 0 ? "down" : "up"));
  }
});

// tab gesloten: kamer netjes verlaten
window.addEventListener("pagehide", () => {
  if (S.room) navigator.sendBeacon("/api/room/leave", JSON.stringify({ code: S.room.code, token: S.room.token }));
});

// ============================================================== start
const link = location.pathname.match(/^\/kamer\/([A-Za-z0-9]+)/);
if (link) {  // geopend via de link van een vriend: meteen meedoen
  history.replaceState(null, "", "/");
  joinRoom(link[1]);
} else {
  render();
}
