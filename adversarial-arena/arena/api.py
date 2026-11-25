from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from arena.models import ArenaReport
from arena.orchestrator import ArenaOrchestrator

app = FastAPI(title="Adversarial Multi-Agent Arena MVP", version="0.1.0")
_orchestrator = ArenaOrchestrator()


class RunRequest(BaseModel):
    scenario: str = "prompt_injection"
    rounds: int = 5
    seed: int = 42


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>Adversarial Multi-Agent Arena — داشبورد ارائه</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: Tahoma, system-ui, sans-serif; max-width: 1000px; margin: 1.5rem auto; padding: 0 1rem; background: #0f172a; color: #e2e8f0; line-height: 1.6; }
    h1 { color: #38bdf8; margin-bottom: 0.25rem; font-size: 1.5rem; }
    .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.25rem; }
    .panel { background: #1e293b; padding: 1rem 1.25rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid #334155; }
    .controls { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; }
    label { font-size: 0.9rem; color: #cbd5e1; }
    input { width: 75px; padding: 0.4rem; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; text-align: center; }
    button { padding: 0.5rem 1.1rem; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-family: inherit; }
    .btn-run { background: #22c55e; color: #052e16; }
    .btn-run:hover { background: #16a34a; }
    .btn-stop { background: #ef4444; color: #fff; }
    .btn-json { background: #334155; color: #e2e8f0; margin-right: auto; }
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .kpi { background: #1e293b; padding: 1rem; border-radius: 10px; border: 1px solid #334155; text-align: center; }
    .kpi-val { font-size: 1.6rem; font-weight: bold; color: #38bdf8; margin-top: 0.25rem; }
    .kpi-label { font-size: 0.8rem; color: #94a3b8; }
    .round-card { background: #1e293b; border-radius: 12px; margin-bottom: 1rem; border: 1px solid #334155; overflow: hidden; }
    .round-header { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1.1rem; background: #0f172a; border-bottom: 1px solid #334155; flex-wrap: wrap; gap: 0.5rem; }
    .badge { padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.8rem; font-weight: bold; }
    .badge-safe { background: #14532d; color: #86efac; }
    .badge-down { background: #7f1d1d; color: #fca5a5; }
    .badge-reason { background: #78350f; color: #fde68a; margin-right: 0.35rem; direction: ltr; display: inline-block; }
    .chat { padding: 1rem; display: flex; flex-direction: column; gap: 0.65rem; }
    .msg { padding: 0.75rem 1rem; border-radius: 10px; max-width: 85%; font-size: 0.9rem; }
    .msg-attacker { align-self: flex-start; background: #3b1219; border-right: 4px solid #ef4444; }
    .msg-defender { align-self: flex-end; background: #0f2942; border-left: 4px solid #38bdf8; }
    .msg-meta { font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.3rem; display: flex; gap: 0.5rem; }
    .msg-text { direction: ltr; text-align: left; white-space: pre-wrap; }
    .tool-box { margin-top: 0.5rem; padding: 0.4rem 0.65rem; border-radius: 6px; font-size: 0.8rem; direction: ltr; text-align: left; }
    .tool-ok { background: #052e16; border: 1px solid #22c55e; color: #86efac; }
    .tool-block { background: #450a0a; border: 1px solid #ef4444; color: #fca5a5; }
    .judge-bar { padding: 0.6rem 1.1rem; background: #0b1220; font-size: 0.85rem; color: #cbd5e1; border-top: 1px solid #334155; }
    pre { background: #020617; padding: 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; direction: ltr; text-align: left; display: none; }
    a { color: #38bdf8; text-decoration: none; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>میدان نبرد چندعاملی ایزوله (Adversarial Multi-Agent Arena)</h1>
  <div class="subtitle">شبیه‌سازی امن و آفلاین حملات Prompt Injection و سوءاستفاده از ابزارها با داور قطعی</div>

  <div class="panel controls">
    <label>تعداد راند: <input id="rounds" type="number" value="5" min="1" max="50" /></label>
    <label>Seed (تکرارپذیری): <input id="seed" type="number" value="42" /></label>
    <button class="btn-run" onclick="runArena()">▶ اجرای شبیه‌سازی</button>
    <button class="btn-stop" onclick="stopArena()">⛔ توقف اضطراری</button>
    <button class="btn-json" onclick="toggleJson()">{ } نمایش/مخفی کردن JSON</button>
    <a href="/docs" target="_blank">مستندات API (Swagger)</a>
  </div>

  <div id="kpis" class="kpis" style="display:none;"></div>
  <pre id="rawJson"></pre>
  <div id="roundsContainer">
    <div class="panel" style="text-align:center; color:#94a3b8;">
      برای شروع شبیه‌سازی بین عامل مهاجم و مدافع، روی دکمه <b>اجرای شبیه‌سازی</b> کلیک کنید.
    </div>
  </div>

  <script>
    function esc(str) {
      return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    }

    function toggleJson() {
      const pre = document.getElementById('rawJson');
      pre.style.display = pre.style.display === 'block' ? 'none' : 'block';
    }

    async function runArena() {
      const container = document.getElementById('roundsContainer');
      container.innerHTML = '<div class="panel">در حال اجرای شبیه‌سازی...</div>';
      const res = await fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: 'prompt_injection',
          rounds: Number(document.getElementById('rounds').value),
          seed: Number(document.getElementById('seed').value)
        })
      });
      const data = await res.json();
      document.getElementById('rawJson').textContent = JSON.stringify(data, null, 2);
      renderReport(data);
    }

    async function stopArena() {
      const res = await fetch('/emergency-stop', { method: 'POST' });
      alert('کلید توقف اضطراری فعال شد: ' + JSON.stringify(await res.json()));
    }

    function renderReport(report) {
      const kpis = document.getElementById('kpis');
      kpis.style.display = 'grid';
      const asr = (report.attack_success_rate * 100).toFixed(1) + '%';
      const det = (report.detection_rate * 100).toFixed(1) + '%';
      const ttc = report.avg_time_to_compromise_sec !== null ? report.avg_time_to_compromise_sec + 's' : 'نفوذی رخ نداد';

      kpis.innerHTML = `
        <div class="kpi"><div class="kpi-label">نرخ موفقیت حمله (ASR)</div><div class="kpi-val" style="color:#f87171">${asr}</div></div>
        <div class="kpi"><div class="kpi-label">نرخ تشخیص مدافع</div><div class="kpi-val" style="color:#4ade80">${det}</div></div>
        <div class="kpi"><div class="kpi-label">میانگین زمان تا نفوذ</div><div class="kpi-val">${ttc}</div></div>
        <div class="kpi"><div class="kpi-label">کل توکن / هزینه تخمینی</div><div class="kpi-val">${report.total_tokens} <span style="font-size:0.85rem;color:#94a3b8">($${report.estimated_token_cost_usd})</span></div></div>
      `;

      const container = document.getElementById('roundsContainer');
      container.innerHTML = report.rounds.map(r => {
        const down = r.verdict.defender_down;
        const statusBadge = down
          ? `<span class="badge badge-down">❌ سقوط مدافع (نوبت ${r.compromised_at_turn ?? '-'})</span>`
          : `<span class="badge badge-safe">✅ دفاع موفق</span>`;
        const reasonsHtml = (r.verdict.reasons || []).map(x => `<span class="badge badge-reason">${esc(x)}</span>`).join('');

        const msgsHtml = r.messages.map(m => {
          const isAtk = m.role === 'attacker';
          const roleLabel = isAtk ? '🔴 عامل مهاجم (Attacker)' : '🛡️ عامل مدافع (Defender)';
          const detTag = m.detected_attack ? '<span style="color:#4ade80">• حمله شناسایی شد</span>' : '';
          let toolsHtml = '';
          if (m.tool_results && m.tool_results.length > 0) {
            toolsHtml = m.tool_results.map(tr => `
              <div class="tool-box ${tr.allowed ? 'tool-ok' : 'tool-block'}">
                🔧 Tool: <b>${esc(tr.tool_name)}</b> — ${tr.allowed ? 'ALLOWED ✅' : 'BLOCKED 🚫'}<br/>
                ${esc(tr.allowed ? tr.output : tr.error)}
              </div>
            `).join('');
          }
          return `
            <div class="msg ${isAtk ? 'msg-attacker' : 'msg-defender'}">
              <div class="msg-meta"><b>${roleLabel}</b><span>نوبت ${m.turn}</span><span>(${m.tokens_used} توکن)</span>${detTag}</div>
              <div class="msg-text">${esc(m.content)}</div>
              ${toolsHtml}
            </div>
          `;
        }).join('');

        return `
          <div class="round-card">
            <div class="round-header">
              <div><b>راند #${r.config.round_id}</b> <span style="color:#94a3b8;font-size:0.85rem">(${r.elapsed_seconds}s • ${r.total_tokens} توکن)</span></div>
              <div>${reasonsHtml} ${statusBadge}</div>
            </div>
            <div class="chat">${msgsHtml}</div>
            <div class="judge-bar">⚖️ <b>حکم داور قطعی:</b> <span style="direction:ltr;display:inline-block">${esc(r.verdict.details)}</span></div>
          </div>
        `;
      }).join('');
    }
  </script>
</body>
</html>"""


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "sandboxed"}


@app.post("/run", response_model=ArenaReport)
def run_simulation(req: RunRequest) -> ArenaReport:
    return _orchestrator.run_arena(scenario=req.scenario, rounds=req.rounds, seed=req.seed)


@app.post("/emergency-stop")
def emergency_stop() -> dict:
    _orchestrator.trigger_emergency_stop()
    return {"status": "emergency_stop_triggered"}