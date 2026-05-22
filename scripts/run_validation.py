#!/usr/bin/env python3
"""Run Nomad Life validation agents against an isolated sandbox dashboard."""

from __future__ import annotations

import argparse
import html
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from time_utils import local_timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / "data/_validation_sandbox"
REPORT_DIR = PROJECT_ROOT / "reports/validation"
OUTPUT_DIR = PROJECT_ROOT / "output/validation"
NODE_SCRIPT_PATH = OUTPUT_DIR / "validation_runner.js"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def find_port(start: int = 43174) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No local validation port available.")


def reset_dir(path: Path) -> None:
    if path.exists():
        for item in sorted(path.rglob("*"), reverse=True):
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
    path.mkdir(parents=True, exist_ok=True)


def prepare_sandbox(root: Path, target_date: str) -> None:
    reset_dir(root)
    now = datetime.now(local_timezone()).isoformat(timespec="seconds")
    current_stay = {
        "stay_id": "validation-bali-2026-05",
        "region": "Validation Bali",
        "country": "Indonesia",
        "timezone": "Asia/Makassar",
        "start_date": target_date[:7] + "-01",
        "end_date": None,
        "status": "active",
        "dataset_scope": "validation_sandbox",
        "notes": ["Synthetic validation stay. Do not import into production data."],
    }
    write_json(root / "data/travel/current-stay.json", current_stay)
    write_json(root / "data/travel/stays-index.json", {"stays": [current_stay]})
    write_json(
        root / "dashboard/today.json",
        {
            "schema_version": "0.1.0",
            "validation_sandbox": True,
            "generated_at": now,
            "date": target_date,
            "summary": "검증 sandbox: 오늘은 Quick 입력, 운동 기록, 재정 리뷰, 영어 리뷰, AI Work 흐름이 모두 보이는지 확인합니다.",
            "focus_today": ["Quick 입력을 10초 안에 저장", "Finance freshness 확인", "English 반복 이슈 확인"],
            "let_go_today": ["검증 데이터는 실제 생활 기록으로 해석하지 않기"],
            "missions": ["더미 활동 1개 저장", "모바일/태블릿 대표 화면 확인"],
            "actions": [
                {"title": "Validation action", "status": "approval_needed", "reason": "승인 필요 액션이 완료 기록과 구분되는지 확인"}
            ],
            "agent_council": [
                {"agent": "nomad-health", "status": "partial", "insight": "최근 운동 2개가 표시되어야 합니다.", "recommendation": "루틴 카드와 히트맵 가독성을 확인합니다."},
                {"agent": "nomad-finance", "status": "partial", "insight": "식비와 카페 지출이 상승한 더미 패턴입니다.", "recommendation": "데이터 기준일과 조정 가능한 항목이 보여야 합니다."},
                {"agent": "nomad-english", "status": "partial", "insight": "반복 문법 이슈 2개가 있습니다.", "recommendation": "다음 세션 prompt가 바로 복사 가능한지 확인합니다."},
            ],
            "local_app_context": {},
        },
    )
    write_json(
        root / "dashboard/life-balance.json",
        {"schema_version": "0.1.0", "validation_sandbox": True, "areas": [
            {"area": "work", "score": 72, "label": "Work"},
            {"area": "health", "score": 58, "label": "Health"},
            {"area": "rest", "score": 36, "label": "Rest"},
        ]},
    )
    activity_sessions = [
        {
            "id": "validation_activity_work_1",
            "date": target_date,
            "area": "work",
            "duration_minutes": 120,
            "place": "cafe",
            "subcategory": "vibe coding",
            "detail": "Validation dashboard harness implementation",
            "status": "completed",
            "validation_sandbox": True,
        },
        {
            "id": "validation_activity_health_1",
            "date": target_date,
            "area": "health",
            "duration_minutes": 45,
            "place": "gym",
            "subcategory": "strength",
            "detail": "Push/pull routine",
            "status": "completed",
            "validation_sandbox": True,
        },
    ]
    for session in activity_sessions:
        append_jsonl(root / "data/activity/activity-sessions.jsonl", session)
    write_json(
        root / "dashboard/activity-allocation.json",
        {
            "schema_version": "0.1.0",
            "validation_sandbox": True,
            "date": target_date,
            "summary": {"tracked_minutes": 165, "total_minutes": 165},
            "month_summary": {"total_tracked_minutes": 165},
            "sessions": activity_sessions,
            "month_sessions": activity_sessions,
            "areas": [
                {"area": "work", "minutes": 120, "share": 0.73},
                {"area": "health", "minutes": 45, "share": 0.27},
            ],
        },
    )
    write_json(root / "dashboard/notifications.json", {"notifications": [], "validation_sandbox": True})
    write_json(root / "dashboard/sync-status.json", {"summary": {"pending_captures": 0}, "recent_events": [], "validation_sandbox": True})
    write_json(
        root / "dashboard/health.json",
        {
            "schema_version": "0.1.0",
            "validation_sandbox": True,
            "summary": {"session_count": 2, "total_minutes": 75},
            "recommendations": ["상체 루틴 간격을 하루 더 둡니다."],
            "sessions": activity_sessions[1:],
            "muscle_dashboard": {"status": "partial"},
        },
    )
    write_json(
        root / "dashboard/english.json",
        {
            "schema_version": "0.1.0",
            "validation_sandbox": True,
            "summary": {"study_minutes": 30, "reviewed_session_count": 1, "correction_count": 3},
            "gpts_reviews": [{"id": "validation_english_review_1", "date": target_date, "focus_area": "speaking"}],
            "dashboard_validation_agent": {"status": "needs_fix", "checks": [{"key": "metric_evidence", "passed": True}]},
            "issue_tracker": {"issues": [{"title": "article usage", "examples": ["a/an confusion"], "remediation": "short drills"}]},
            "pre_study_context": {"status": "ready", "prompt": "Practice article usage with travel planning examples."},
        },
    )
    write_json(
        root / "data/expenses/normalized-expenses.json",
        {
            "schema_version": "0.1.0",
            "validation_sandbox": True,
            "summary": {"expense_count": 4, "month_total": 245000, "currency": "KRW"},
            "data_quality": {"status": "partial", "latest_trade_date": target_date, "notes": ["Synthetic validation finance export."]},
            "analysis": {"latest_trade_date": target_date, "top_categories": [{"category": "식비", "amount": 120000}]},
            "expenses": [],
        },
    )
    write_json(root / "data/expenses/expense-candidates.json", {"candidates": [], "validation_sandbox": True})
    write_json(
        root / "data/work/projects.json",
        {"schema_version": "0.1.0", "projects": [{"project_id": "nomad-life-validation", "name": "Validation Harness", "status": "in_progress"}]},
    )
    write_json(
        root / "data/work/project-progress.json",
        {"schema_version": "0.1.0", "projects": [{"project_id": "nomad-life-validation", "status": "in_progress", "next_actions": ["Review validation findings"]}]},
    )


def browser_script() -> str:
    return r'''
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const baseUrl = process.env.NOMAD_VALIDATION_URL;
const outDir = process.env.NOMAD_VALIDATION_ARTIFACT_DIR;
const resultPath = process.env.NOMAD_VALIDATION_RESULT_PATH;
const viewports = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

function finding(severity, title, evidence, recommendation, surface = "Dashboard") {
  return { severity, title, evidence, recommendation, surface };
}

async function collectVisualFindings(page, viewportName) {
  return await page.evaluate((viewportName) => {
    const findings = [];
    const visible = (el) => {
      const box = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return box.width > 0 && box.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    };
    const labelFor = (el) => {
      return el.id || el.getAttribute("aria-label") || el.textContent.trim().replace(/\s+/g, " ").slice(0, 48) || el.tagName.toLowerCase();
    };
    for (const el of document.querySelectorAll("button, input, select, textarea")) {
      if (!visible(el)) continue;
      if (["radio", "checkbox", "hidden"].includes(el.getAttribute("type") || "")) continue;
      const box = el.getBoundingClientRect();
      const minSize = viewportName === "desktop" ? 32 : 44;
      if (box.width < minSize || box.height < minSize) {
        findings.push({
          severity: viewportName === "desktop" ? "P3" : "P2",
          title: "Interactive control below target size",
          surface: labelFor(el),
          evidence: `${Math.round(box.width)}x${Math.round(box.height)} on ${viewportName}`,
          recommendation: `Use at least ${minSize}px touch/click target for this viewport.`,
        });
      }
    }
    if (document.documentElement.scrollWidth > window.innerWidth + 2) {
      findings.push({
        severity: "P1",
        title: "Horizontal overflow",
        surface: "Page",
        evidence: `scrollWidth ${document.documentElement.scrollWidth}, viewport ${window.innerWidth}`,
        recommendation: "Find the overflowing panel/control and constrain width or wrapping.",
      });
    }
    for (const el of document.querySelectorAll("h1,h2,h3,p,span,button,a,strong,small")) {
      if (!visible(el)) continue;
      const style = window.getComputedStyle(el);
      if (el.scrollWidth > el.clientWidth + 3 && ["hidden", "clip"].includes(style.overflowX)) {
        findings.push({
          severity: "P2",
          title: "Text may be clipped",
          surface: labelFor(el),
          evidence: `scrollWidth ${el.scrollWidth}, clientWidth ${el.clientWidth}`,
          recommendation: "Allow wrapping, shorten the label, or adjust container sizing.",
        });
      }
    }
    return findings.slice(0, 40);
  }, viewportName);
}

async function screenshot(page, name) {
  const file = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const headless = process.env.NOMAD_VALIDATION_HEADLESS !== "0";
  const slowMo = Number(process.env.NOMAD_VALIDATION_SLOW_MO || 0);
  const browser = await chromium.launch({ headless, slowMo });
  const consoleErrors = [];
  const results = { scenarios: [], visual_findings: [], screenshots: [], console_errors: consoleErrors };

  async function runScenario(name, viewport, scenario) {
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height } });
    const page = await context.newPage();
    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        consoleErrors.push({ scenario: name, type: message.type(), text: message.text().slice(0, 500) });
      }
    });
    page.on("pageerror", (error) => {
      consoleErrors.push({ scenario: name, type: "pageerror", text: String(error).slice(0, 500) });
    });
    const started = Date.now();
    const record = { name, viewport: viewport.name, status: "pass", steps: [], duration_ms: 0, errors: [] };
    try {
      await scenario(page, record);
    } catch (error) {
      record.status = "fail";
      record.errors.push(String(error && error.stack || error));
    }
    record.duration_ms = Date.now() - started;
    results.scenarios.push(record);
    results.visual_findings.push(...(await collectVisualFindings(page, viewport.name)).map((item) => ({ ...item, scenario: name, viewport: viewport.name })));
    results.screenshots.push({ scenario: name, viewport: viewport.name, path: await screenshot(page, `${viewport.name}-${name}`) });
    if (process.env.NOMAD_VALIDATION_PREVIEW_PAUSE_MS) {
      await page.waitForTimeout(Number(process.env.NOMAD_VALIDATION_PREVIEW_PAUSE_MS));
    }
    await context.close();
  }

  await runScenario("main-load", viewports[2], async (page, record) => {
    await page.goto(`${baseUrl}/web/#main`, { waitUntil: "networkidle" });
    await page.locator("#main-agent-summary").waitFor({ timeout: 10000 });
    const bodyText = await page.locator("body").innerText();
    if (!bodyText.includes("Validation Bali") || !bodyText.includes("nomad-health")) {
      throw new Error("Sandbox dashboard signals did not render.");
    }
    record.steps.push("Loaded main dashboard sandbox summary.");
  });

  await runScenario("quick-input-save", viewports[0], async (page, record) => {
    await page.goto(`${baseUrl}/web/#main`, { waitUntil: "networkidle" });
    await page.locator("#floating-quick-button").click();
    await page.locator("#activity-detail").fill("validation dummy quick input");
    await page.locator('#activity-form button[type="submit"]').click();
    await page.waitForTimeout(1000);
    const response = await page.request.get(`${baseUrl}/api/activity-history`);
    const payload = await response.json();
    if (!payload.validation_sandbox) throw new Error("Activity history is not sandboxed.");
    if (!payload.sessions.some((item) => String(item.detail || "").includes("validation dummy quick input"))) {
      throw new Error("Saved quick input was not found in sandbox activity history.");
    }
    record.steps.push("Opened mobile quick dialog.");
    record.steps.push("Saved dummy activity to sandbox API.");
    record.steps.push("Confirmed production data was not used by API contract.");
  });

  await runScenario("tablet-workspace-scan", viewports[1], async (page, record) => {
    await page.goto(`${baseUrl}/web/#health`, { waitUntil: "networkidle" });
    await page.locator("#health-dashboard").waitFor({ timeout: 10000 });
    record.steps.push("Rendered Health workspace on tablet viewport.");
    await page.goto(`${baseUrl}/web/#english`, { waitUntil: "networkidle" });
    await page.locator("#english").waitFor({ timeout: 10000 });
    record.steps.push("Rendered English workspace on tablet viewport.");
    await page.goto(`${baseUrl}/web/#finance`, { waitUntil: "networkidle" });
    await page.locator("#finance-review").waitFor({ timeout: 10000 });
    record.steps.push("Rendered Finance workspace on tablet viewport.");
  });

  await browser.close();
  fs.writeFileSync(resultPath, JSON.stringify(results, null, 2));
})().catch((error) => {
  fs.writeFileSync(resultPath, JSON.stringify({ fatal_error: String(error && error.stack || error) }, null, 2));
  process.exit(1);
});
'''


def data_value_findings(sandbox_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    finance = json.loads((sandbox_root / "data/expenses/normalized-expenses.json").read_text(encoding="utf-8"))
    if not finance.get("data_quality", {}).get("latest_trade_date") and not finance.get("analysis", {}).get("latest_trade_date"):
        findings.append({
            "severity": "P1",
            "title": "Finance freshness is not visible",
            "evidence": "No latest_trade_date in finance data quality or analysis.",
            "recommendation": "Expose source date/freshness near every finance review summary.",
        })
    today = json.loads((sandbox_root / "dashboard/today.json").read_text(encoding="utf-8"))
    generic = [item for item in today.get("agent_council", []) if "관리" in str(item.get("recommendation", "")) and len(str(item.get("insight", ""))) < 16]
    if generic:
        findings.append({
            "severity": "P2",
            "title": "Agent Council recommendation may be generic",
            "evidence": f"{len(generic)} council item(s) use broad recommendation without enough evidence.",
            "recommendation": "Tie each recommendation to source, metric, trend, and next action.",
        })
    if not today.get("actions"):
        findings.append({
            "severity": "P2",
            "title": "No action boundary visible",
            "evidence": "today.actions is empty.",
            "recommendation": "Show whether there is nothing to approve or whether action data is missing.",
        })
    return findings


def markdown_report(title: str, payload: dict[str, Any]) -> str:
    lines = [f"# {title}", "", f"- Agent: `{payload.get('agent')}`", f"- Verdict: `{payload.get('verdict')}`", f"- Scope: {payload.get('scope')}", f"- Sandbox: `{payload.get('sandbox')}`", ""]
    coverage = payload.get("review_coverage") or []
    if coverage:
        lines.extend(["## Review Coverage", ""])
        lines.extend(f"- {item}" for item in coverage)
        lines.append("")
    scenarios = payload.get("scenarios") or []
    if scenarios:
        lines.extend(["## Scenario Trace", ""])
        for item in scenarios:
            lines.append(f"### {item.get('name')} / {item.get('viewport')} / {item.get('status')}")
            lines.append("")
            lines.append(f"- Duration: `{item.get('duration_ms')}ms`")
            for step in item.get("steps") or []:
                lines.append(f"- Step: {step}")
            for error in item.get("errors") or []:
                lines.append(f"- Error: {error}")
            lines.append("")
    data_sources = payload.get("data_sources") or []
    if data_sources:
        lines.extend(["## Data Sources", ""])
        lines.extend(f"- `{item}`" for item in data_sources)
        lines.append("")
    findings = payload.get("findings") or []
    lines.extend(["## Findings", ""])
    if findings:
        for item in findings:
            lines.append(f"- `{item.get('severity', 'P?')}` {item.get('title')}: {item.get('evidence')}")
    else:
        lines.append("- No findings.")
    lines.extend(["", "## Raw JSON", "", "```json", json.dumps(payload, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def write_reports(date: str, artifact_dir: Path, browser_results: dict[str, Any], sandbox_root: Path) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    visual_findings = browser_results.get("visual_findings", [])
    scenarios = browser_results.get("scenarios", [])
    ux_findings = []
    if browser_results.get("fatal_error"):
        ux_findings.append({
            "severity": "P0",
            "title": "Browser validation could not start",
            "evidence": str(browser_results.get("fatal_error"))[:900],
            "recommendation": "Install Playwright browsers with `npx playwright install chromium`, then rerun validation.",
        })
    for scenario in browser_results.get("scenarios", []):
        if scenario.get("status") != "pass":
            ux_findings.append({
                "severity": "P1",
                "title": f"Scenario failed: {scenario.get('name')}",
                "evidence": "; ".join(scenario.get("errors") or [])[:700],
                "recommendation": "Reproduce from the saved screenshot and repair the broken flow.",
            })
    if browser_results.get("console_errors"):
        ux_findings.append({
            "severity": "P2",
            "title": "Console warnings/errors during validation",
            "evidence": f"{len(browser_results['console_errors'])} console issue(s) captured.",
            "recommendation": "Review console_errors in latest-validation.json and fix noisy runtime issues.",
        })
    data_findings = data_value_findings(sandbox_root)
    ux_payload = {
        "agent": "nomad-ux-flow-review",
        "scope": "Sandbox E2E journey scan",
        "verdict": "needs_fix" if ux_findings else "pass",
        "sandbox": True,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "review_coverage": [
            "Dashboard sandbox render and active stay signal",
            "Mobile Quick Input open/save flow",
            "Sandbox API persistence after save",
            "Production-data isolation contract",
            "Tablet workspace navigation across Health, English, and Finance",
        ],
        "findings": ux_findings,
        "passes": [f"{item['name']} ({item['viewport']})" for item in scenarios if item.get("status") == "pass"],
        "open_questions": [],
    }
    visual_payload = {
        "agent": "nomad-gui-review",
        "scope": "Sandbox mobile/tablet/desktop screenshot scan",
        "verdict": "needs_fix" if visual_findings else "pass",
        "sandbox": True,
        "review_coverage": [
            "Desktop main cockpit representative screenshot",
            "Mobile Quick Input/save representative screenshot",
            "Tablet workspace scan screenshot",
            "Interactive control target size",
            "Horizontal overflow",
            "Clipped text candidates",
            "Console warning/error capture",
        ],
        "findings": visual_findings[:80],
        "passes": [f"Captured {len(browser_results.get('screenshots', []))} representative screenshots."],
        "open_questions": [],
    }
    data_payload = {
        "agent": "nomad-review-value-review",
        "scope": "Sandbox dashboard data usefulness scan",
        "verdict": "needs_fix" if data_findings else "pass",
        "sandbox": True,
        "review_coverage": [
            "Finance freshness visibility",
            "Action/approval boundary visibility",
            "Agent Council recommendation specificity",
            "Synthetic data isolation marker",
        ],
        "data_sources": [
            "data/_validation_sandbox/dashboard/today.json",
            "data/_validation_sandbox/data/expenses/normalized-expenses.json",
            "data/_validation_sandbox/dashboard/english.json",
            "data/_validation_sandbox/dashboard/health.json",
        ],
        "findings": data_findings,
        "passes": ["Finance freshness, action boundary, and Agent Council specificity were checked."],
        "open_questions": [],
    }
    summary = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(local_timezone()).isoformat(timespec="seconds"),
        "sandbox": True,
        "artifact_dir": str(artifact_dir.relative_to(PROJECT_ROOT)),
        "screenshots": [
            {**item, "path": str(Path(item["path"]).relative_to(PROJECT_ROOT))}
            for item in browser_results.get("screenshots", [])
        ],
        "console_errors": browser_results.get("console_errors", []),
        "scenario_trace": scenarios,
        "agents": [ux_payload, visual_payload, data_payload],
        "overall_verdict": "needs_fix" if any(item["verdict"] != "pass" for item in [ux_payload, visual_payload, data_payload]) else "pass",
    }
    write_json(REPORT_DIR / f"{date}-latest-validation.json", summary)
    write_json(PROJECT_ROOT / "data/context/latest-validation.json", summary)
    (REPORT_DIR / f"{date}-ux-flow.md").write_text(markdown_report(f"{date} UX Flow Validation", ux_payload), encoding="utf-8")
    (REPORT_DIR / f"{date}-gui.md").write_text(markdown_report(f"{date} GUI Validation", visual_payload), encoding="utf-8")
    (REPORT_DIR / f"{date}-review-value.md").write_text(markdown_report(f"{date} Review Value Validation", data_payload), encoding="utf-8")
    html_path = REPORT_DIR / f"{date}-summary.html"
    html_path.write_text(render_html_summary(summary), encoding="utf-8")
    summary["html_report"] = str(html_path.relative_to(PROJECT_ROOT))
    write_json(REPORT_DIR / f"{date}-latest-validation.json", summary)
    write_json(PROJECT_ROOT / "data/context/latest-validation.json", summary)
    return summary


def render_html_summary(summary: dict[str, Any]) -> str:
    cards = []
    for agent in summary["agents"]:
        coverage = "".join(f"<li>{html.escape(item)}</li>" for item in agent.get("review_coverage", [])) or "<li>No explicit coverage recorded.</li>"
        findings = "".join(
            f"<li><b>{html.escape(item.get('severity', 'P?'))}</b> {html.escape(item.get('title', ''))}<br><small>{html.escape(item.get('evidence', ''))}</small></li>"
            for item in agent.get("findings", [])[:12]
        ) or "<li>No findings.</li>"
        passes = "".join(f"<li>{html.escape(item)}</li>" for item in agent.get("passes", [])) or "<li>No pass details.</li>"
        cards.append(
            f"<section>"
            f"<h2>{html.escape(agent['agent'])} · {html.escape(agent['verdict'])}</h2>"
            f"<div class='two-col'>"
            f"<div><h3>Review Coverage</h3><ul>{coverage}</ul></div>"
            f"<div><h3>Pass Evidence</h3><ul>{passes}</ul></div>"
            f"</div>"
            f"<h3>Findings</h3><ul>{findings}</ul>"
            f"</section>"
        )
    scenario_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.get('name', ''))}</td>"
        f"<td>{html.escape(item.get('viewport', ''))}</td>"
        f"<td><b>{html.escape(item.get('status', ''))}</b></td>"
        f"<td>{html.escape(str(item.get('duration_ms', '')))}ms</td>"
        f"<td>{html.escape(' / '.join(item.get('steps') or item.get('errors') or []))}</td>"
        "</tr>"
        for item in summary.get("scenario_trace", [])
    ) or "<tr><td colspan='5'>No scenario trace recorded.</td></tr>"
    console_rows = "".join(
        f"<li><b>{html.escape(item.get('type', 'console'))}</b> {html.escape(item.get('text', ''))}</li>"
        for item in summary.get("console_errors", [])
    ) or "<li>No console errors or warnings captured.</li>"
    shots = "".join(
        f"<figure><img src='../../{html.escape(item['path'])}' alt='{html.escape(item['scenario'])}'><figcaption>{html.escape(item['viewport'])} · {html.escape(item['scenario'])}</figcaption></figure>"
        for item in summary.get("screenshots", [])
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nomad Validation Summary</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", sans-serif; margin: 24px; color: #172033; background: #f7f8fa; }}
    header, section {{ background: white; border: 1px solid #dde2ea; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    h3 {{ font-size: 15px; color: #475161; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-top: 1px solid #dde2ea; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ color: #5d687a; background: #f7f8fa; }}
    .two-col {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    .shots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    figure {{ margin: 0; background: white; border: 1px solid #dde2ea; border-radius: 8px; overflow: hidden; }}
    img {{ display: block; width: 100%; height: auto; }}
    figcaption {{ padding: 8px 10px; font-size: 13px; color: #5d687a; }}
    li {{ margin: 8px 0; }}
    small {{ color: #5d687a; }}
  </style>
</head>
<body>
  <header>
    <h1>Nomad Validation Summary</h1>
    <p>Verdict: <b>{html.escape(summary['overall_verdict'])}</b> · Sandbox: true · Generated: {html.escape(summary['generated_at'])}</p>
  </header>
  <section>
    <h2>Scenario Trace</h2>
    <table>
      <thead><tr><th>Scenario</th><th>Viewport</th><th>Status</th><th>Duration</th><th>Steps / Errors</th></tr></thead>
      <tbody>{scenario_rows}</tbody>
    </table>
  </section>
  {''.join(cards)}
  <section>
    <h2>Console Capture</h2>
    <ul>{console_rows}</ul>
  </section>
  <section>
    <h2>Visual Evidence</h2>
    <div class="shots">{shots}</div>
  </section>
</body>
</html>
"""


def run_browser_validation(url: str, artifact_dir: Path, preview: bool = False) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    NODE_SCRIPT_PATH.write_text(browser_script(), encoding="utf-8")
    result_path = artifact_dir / "browser-results.json"
    env = {
        **os.environ,
        "NOMAD_VALIDATION_URL": url,
        "NOMAD_VALIDATION_ARTIFACT_DIR": str(artifact_dir),
        "NOMAD_VALIDATION_RESULT_PATH": str(result_path),
    }
    if preview:
        env["NOMAD_VALIDATION_HEADLESS"] = "0"
        env.setdefault("NOMAD_VALIDATION_SLOW_MO", "350")
        env.setdefault("NOMAD_VALIDATION_PREVIEW_PAUSE_MS", "1200")
    completed = subprocess.run(
        ["node", str(NODE_SCRIPT_PATH)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        if result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            payload["node_stderr"] = completed.stderr
            return payload
        raise RuntimeError(f"Browser validation failed:\n{completed.stderr}")
    return json.loads(result_path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Nomad Life sandbox validation agents.")
    parser.add_argument("--date", help="Validation date. Defaults to today in local timezone.")
    parser.add_argument("--sandbox-root", default=str(DEFAULT_SANDBOX_ROOT))
    parser.add_argument("--setup-only", action="store_true", help="Only prepare sandbox fixtures; do not start browser validation.")
    parser.add_argument("--serve-only", action="store_true", help="Prepare sandbox and serve the validation dashboard for manual preview.")
    parser.add_argument("--preview", action="store_true", help="Run validation in a visible headed browser with slower steps.")
    parser.add_argument("--keep-server", action="store_true", help="Leave the validation server running for manual inspection.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_date = args.date or datetime.now(local_timezone()).date().isoformat()
    sandbox_root = Path(args.sandbox_root).expanduser()
    artifact_dir = OUTPUT_DIR / target_date
    if not args.setup_only:
        reset_dir(artifact_dir)
    prepare_sandbox(sandbox_root, target_date)
    if args.setup_only:
        print(
            json.dumps(
                {
                    "schema_version": "0.1.0",
                    "mode": "setup-only",
                    "sandbox": True,
                    "date": target_date,
                    "sandbox_root": str(sandbox_root.relative_to(PROJECT_ROOT) if sandbox_root.is_relative_to(PROJECT_ROOT) else sandbox_root),
                    "next_commands": [
                        "npm run validate:serve",
                        "npm run validate:preview",
                        "npm run validate",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    port = find_port()
    env = {
        **os.environ,
        "NOMAD_VALIDATION_MODE": "1",
        "NOMAD_VALIDATION_ROOT": str(sandbox_root),
    }
    server = subprocess.Popen(  # noqa: S603 - fixed local Python server command.
        [sys.executable, str(PROJECT_ROOT / "scripts/serve_cockpit.py"), "--host", "127.0.0.1", "--port", str(port)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        time.sleep(1.2)
        if server.poll() is not None:
            stderr = server.stderr.read() if server.stderr else ""
            raise RuntimeError(f"Validation server exited early: {stderr}")
        print(f"Validation preview URL: {url}/web/", file=sys.stderr)
        if args.serve_only:
            print(
                json.dumps(
                    {
                        "schema_version": "0.1.0",
                        "mode": "serve-only",
                        "sandbox": True,
                        "date": target_date,
                        "url": f"{url}/web/",
                        "sandbox_root": str(sandbox_root.relative_to(PROJECT_ROOT) if sandbox_root.is_relative_to(PROJECT_ROOT) else sandbox_root),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            server.wait()
            return
        browser_results = run_browser_validation(url, artifact_dir, preview=args.preview)
        summary = write_reports(target_date, artifact_dir, browser_results, sandbox_root)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.keep_server:
            print(f"Validation server still running at {url}/web/")
            server.wait()
    finally:
        if not args.keep_server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()
