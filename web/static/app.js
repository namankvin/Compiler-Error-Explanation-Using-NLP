const codeInput = document.getElementById("code-input");
const analyzeButton = document.getElementById("analyze-btn");
const loadExampleButton = document.getElementById("load-example");
<<<<<<< HEAD
=======
const loadExample2Button = document.getElementById("load-example-2");
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
const resultsContainer = document.getElementById("results");
const statusElement = document.getElementById("status");
const runtimeElement = document.getElementById("runtime");

<<<<<<< HEAD
const compilerSelect = document.getElementById("compiler");
const warningsToggle = document.getElementById("warnings");
const securityToggle = document.getElementById("security");
const preferModelToggle = document.getElementById("prefer-model");
=======
const carbonSummaryElement = document.getElementById("carbon-summary");

const EXAMPLE_2_CODE = `#include <stdio.h>
#include <string.h>

int main() {
  char buf[8];

  gets(buf);                               // insecure: dangerous input API
  strcpy(buf, "THIS_INPUT_IS_TOO_LONG");  // insecure: overflow-prone copy

  int n = 10                               // ERROR 1: missing semicolon
  printf(user_input);                     // ERROR 2: undeclared identifier + format-string risk
  undeclared_api(buf);                    // ERROR 3: undeclared function call
  return missing_value                    // ERROR 4: undeclared identifier + missing semicolon
}`;
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a

codeInput.value = window.DEFAULT_CODE || "";

function escapeHtml(value) {
<<<<<<< HEAD
  return value
=======
  return String(value ?? "")
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setStatus(text) {
  statusElement.textContent = text;
}

<<<<<<< HEAD
function renderCleanState(meta) {
  resultsContainer.innerHTML = `
    <div class="clean-state">
      No diagnostics reported. Compilation succeeded.
      <div style="margin-top:0.4rem; color:#2a5a50;">Compiler: ${escapeHtml(meta.compiler)} | Time: ${meta.elapsed_ms} ms</div>
=======
function toFiniteNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function graphBars(rows) {
  const validRows = rows.filter((row) => toFiniteNumber(row.value, 0) >= 0);
  const maxValue = Math.max(1, ...validRows.map((row) => toFiniteNumber(row.value, 0)));

  return validRows.map((row) => {
    const value = toFiniteNumber(row.value, 0);
    const width = Math.max(4, (value / maxValue) * 100);
    return `
      <div class="cc-graph-row">
        <div class="cc-graph-label">${escapeHtml(row.label)}</div>
        <div class="cc-graph-track">
          <div class="cc-graph-fill ${escapeHtml(row.variant || "")}" style="width:${width.toFixed(2)}%"></div>
        </div>
        <div class="cc-graph-value">${escapeHtml(row.display)}</div>
      </div>
    `;
  }).join("\n");
}

function renderCodeCarbonSummary(meta) {
  const codecarbon = meta.codecarbon || null;
  if (!codecarbon) {
    carbonSummaryElement.innerHTML = `
      <div class="carbon-card carbon-card-warning">
        <h3>CodeCarbon</h3>
        <p>Energy tracking metadata is unavailable for this response.</p>
      </div>
    `;
    return;
  }

  if (!codecarbon.requested || !codecarbon.available) {
    carbonSummaryElement.innerHTML = `
      <div class="carbon-card carbon-card-warning">
        <h3>CodeCarbon</h3>
        <p>${escapeHtml(codecarbon.note || "CodeCarbon duration comparison is unavailable in this environment.")}</p>
      </div>
    `;
    return;
  }

  const cmp = codecarbon.comparison || null;
  if (!cmp) {
    carbonSummaryElement.innerHTML = `
      <div class="carbon-card carbon-card-warning">
        <h3>CodeCarbon</h3>
        <p>Duration comparison data is unavailable for this run.</p>
      </div>
    `;
    return;
  }

  const withoutRuntimeMs = toFiniteNumber(cmp.without_tracking_runtime_ms, 0);
  const comparisonMode = String(cmp.comparison_mode || "").toLowerCase();
  const withRuntimeMs = comparisonMode === "normalized_effective_runtime"
    ? toFiniteNumber(
      cmp.with_tracking_effective_runtime_ms,
      toFiniteNumber(cmp.with_tracking_runtime_ms, 0),
    )
    : toFiniteNumber(
      cmp.with_tracking_runtime_ms,
      toFiniteNumber(cmp.with_tracking_effective_runtime_ms, 0),
    );

  const compareRows = [
    {
      label: "Without Tracking",
      value: withoutRuntimeMs,
      display: `${withoutRuntimeMs.toFixed(2)} ms`,
      variant: "prev",
    },
    {
      label: "With Tracking",
      value: withRuntimeMs,
      display: `${withRuntimeMs.toFixed(2)} ms`,
      variant: "curr",
    },
  ];

  carbonSummaryElement.innerHTML = `
    <div class="carbon-card">
      <h3>CodeCarbon Duration Block Graph</h3>
      <div class="cc-graph">${graphBars(compareRows)}</div>
    </div>
  `;
}

function renderCleanState(meta) {
  const ignoredWarnings = Number(meta.ignored_warning_count || 0);
  const details = ignoredWarnings > 0
    ? `No compiler errors. ${ignoredWarnings} warning(s) were ignored.`
    : "No compiler errors. Compilation succeeded.";

  resultsContainer.innerHTML = `
    <div class="clean-state">
      ${details}
      <div class="clean-meta">Compiler: ${escapeHtml(meta.compiler)} | Time: ${escapeHtml(meta.elapsed_ms)} ms</div>
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
    </div>
  `;
}

function renderDiagnostics(items) {
  if (!items || items.length === 0) {
    resultsContainer.innerHTML = "";
    return;
  }

<<<<<<< HEAD
  const cards = items.map((item, index) => {
    const diagnostic = item.diagnostic;
    const classification = diagnostic.classification || {};
    const expectedActual = diagnostic.expected_actual || {};
    const security = item.security_analysis;

    let securityBlock = "";
    if (security) {
      securityBlock = `
        <div class="result-block">
          <h4>Security</h4>
          <p>
Severity: ${escapeHtml(security.severity || "Unknown")}
Category: ${escapeHtml(security.category || "Unknown")}
CWE: ${escapeHtml(security.cwe || "N/A")}
Risk: ${escapeHtml(security.risk || "N/A")}
Secure Fix: ${escapeHtml(security.explanation || "N/A")}
          </p>
        </div>
      `;
    }

    return `
      <article class="result-card ${escapeHtml(diagnostic.level || "warning")}">
        <h3 class="result-title">#${index + 1} ${escapeHtml((diagnostic.level || "warning").toUpperCase())}: ${escapeHtml(diagnostic.message || "")}</h3>
        <div class="result-meta">
          Line ${diagnostic.line}, Col ${diagnostic.column} | Category: ${escapeHtml(classification.category || "Unknown")} | Phase: ${escapeHtml(classification.phase || "Unknown")}
        </div>

        <div class="result-block">
          <h4>Expected vs Actual</h4>
          <p>Expected: ${escapeHtml(expectedActual.expected || "Unknown")}\nActual: ${escapeHtml(expectedActual.actual || "Unknown")}</p>
        </div>

        <div class="result-block">
          <h4>Context</h4>
          <pre>${escapeHtml(diagnostic.code_context || "")}</pre>
        </div>

        <div class="result-block">
          <h4>NLP Explanation</h4>
          <p>${escapeHtml(item.explanation || "")}</p>
        </div>

        ${securityBlock}
=======
  const orderedItems = [...items].sort((a, b) => {
    const lineA = Number(a?.diagnostic?.line || 0);
    const lineB = Number(b?.diagnostic?.line || 0);
    return lineA - lineB;
  });

  const cards = orderedItems.map((item, index) => {
    const diagnostic = item.diagnostic || {};
    const security = item.security_analysis || {
      severity: "Info",
      category: "No immediate security pattern detected",
      cwe: "N/A",
      risk: "No direct security risk identified for this diagnostic.",
      explanation: "Security analysis completed. No specific weakness pattern was matched.",
    };
    const explanation = item.explanation || `Compiler reported: ${diagnostic.message || "Unknown diagnostic."}`;
    const compilerOutput = formatCompilerOutput(diagnostic);
    const explanationHtml = renderExplanationHtml(explanation);
    const securityHtml = renderSecurityHtml(security);
    const codeContextBlock = diagnostic.code_context
      ? renderCodeContext(diagnostic.code_context, diagnostic.line)
      : `<pre>No code context available.</pre>`;

    return `
      <article class="result-card error">
        <h3 class="result-title">Error No. ${index + 1}</h3>
        <div class="result-meta">
          Line ${escapeHtml(diagnostic.line || "?")}, Col ${escapeHtml(diagnostic.column || "?")}
        </div>

        <div class="result-block">
          <h4>Code Context</h4>
          ${codeContextBlock}
        </div>

        <div class="result-block">
          <h4>Explanation</h4>
          <div class="explanation-rich">${explanationHtml}</div>
        </div>

        <div class="result-block">
          <h4>Security Analysis</h4>
          <div class="security-rich">${securityHtml}</div>
        </div>

        <div class="result-block">
          <h4>Compiler Output</h4>
          <pre>${escapeHtml(compilerOutput)}</pre>
        </div>
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
      </article>
    `;
  });

  resultsContainer.innerHTML = cards.join("\n");
}

<<<<<<< HEAD
=======
function renderExplanationHtml(explanation) {
  const lines = String(explanation || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return `<p class="exp-line">No explanation available.</p>`;
  }

  return lines.map((line, index) => {
    if (index === 0) {
      return `<p class="exp-lead">${escapeHtml(line)}</p>`;
    }

    const colonIndex = line.indexOf(":");
    if (colonIndex > 0) {
      const key = line.slice(0, colonIndex).trim();
      const value = line.slice(colonIndex + 1).trim();
      return `
        <div class="exp-row">
          <span class="exp-key">${escapeHtml(key)}</span>
          <span class="exp-value">${escapeHtml(value)}</span>
        </div>
      `;
    }

    return `<p class="exp-line">${escapeHtml(line)}</p>`;
  }).join("");
}

function renderSecurityHtml(security) {
  const rows = [
    ["Severity", security.severity || "Unknown"],
    ["Category", security.category || "Unknown"],
    ["Common Weakness Enumeration (CWE)", security.cwe || "N/A"],
    ["Risk", security.risk || "N/A"],
    ["Secure Guidance", security.explanation || "N/A"],
  ];

  return rows.map(([label, value]) => `
    <div class="sec-row">
      <span class="sec-key">${escapeHtml(label)}</span>
      <span class="sec-value">${escapeHtml(value)}</span>
    </div>
  `).join("");
}

function formatCompilerOutput(diagnostic) {
  const level = String(diagnostic.level || "error").toLowerCase();
  const message = String(diagnostic.message || "Unknown compiler diagnostic.").trim();
  return `${level}: ${message}`;
}

function renderCodeContext(codeContext, errorLine) {
  const targetLine = Number(errorLine);
  const rendered = String(codeContext)
    .split("\n")
    .map((line) => {
      const match = line.match(/^\s*(\d+):/);
      const contextLineNo = match ? Number(match[1]) : null;
      const isErrorLine = Number.isFinite(targetLine) && contextLineNo === targetLine;
      const className = isErrorLine ? "code-line code-line-error" : "code-line";
      return `<span class="${className}">${escapeHtml(line)}</span>`;
    })
    .join("");

  return `<div class="code-context-pre">${rendered}</div>`;
}

>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
async function runAnalysis() {
  const code = codeInput.value;
  if (!code.trim()) {
    setStatus("Please paste C code before running analysis.");
    return;
  }

  analyzeButton.disabled = true;
  setStatus("Compiling and generating NLP explanations...");
  runtimeElement.textContent = "";
<<<<<<< HEAD
=======
  carbonSummaryElement.innerHTML = "";
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
  resultsContainer.innerHTML = "";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
<<<<<<< HEAD
        compiler: compilerSelect.value,
        warnings: warningsToggle.checked,
        security: securityToggle.checked,
        prefer_model: preferModelToggle.checked,
=======
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
      }),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Request failed.");
    }

    const meta = payload.meta || {};
    runtimeElement.textContent = `Runtime: ${meta.elapsed_ms || "-"} ms`;
<<<<<<< HEAD

    if (payload.success) {
      setStatus("Compilation successful.");
=======
    renderCodeCarbonSummary(meta);

    if (payload.success) {
      const ignored = Number(meta.ignored_warning_count || 0);
      if (ignored > 0) {
        setStatus(`No compiler errors. Ignored ${ignored} warning(s).`);
      } else {
        setStatus("Compilation successful.");
      }
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
      renderCleanState(meta);
      return;
    }

<<<<<<< HEAD
    setStatus(`Found ${payload.diagnostics.length} diagnostic(s).`);
=======
    setStatus("");
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
    renderDiagnostics(payload.diagnostics);
  } catch (error) {
    setStatus(`Error: ${error.message}`);
    resultsContainer.innerHTML = "";
  } finally {
    analyzeButton.disabled = false;
  }
}

analyzeButton.addEventListener("click", runAnalysis);
loadExampleButton.addEventListener("click", () => {
  codeInput.value = window.DEFAULT_CODE || codeInput.value;
<<<<<<< HEAD
  setStatus("Loaded sample code.");
=======
  setStatus("Loaded sample code 1.");
});

loadExample2Button.addEventListener("click", () => {
  codeInput.value = EXAMPLE_2_CODE;
  setStatus("Loaded sample code 2.");
>>>>>>> 9e4594b5766ca37b1d618f879725af1bfabd532a
});
