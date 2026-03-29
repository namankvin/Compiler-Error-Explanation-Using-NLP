const codeInput = document.getElementById("code-input");
const analyzeButton = document.getElementById("analyze-btn");
const loadExampleButton = document.getElementById("load-example");
const resultsContainer = document.getElementById("results");
const statusElement = document.getElementById("status");
const runtimeElement = document.getElementById("runtime");

const compilerSelect = document.getElementById("compiler");
const warningsToggle = document.getElementById("warnings");
const securityToggle = document.getElementById("security");
const preferModelToggle = document.getElementById("prefer-model");

codeInput.value = window.DEFAULT_CODE || "";

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setStatus(text) {
  statusElement.textContent = text;
}

function renderCleanState(meta) {
  resultsContainer.innerHTML = `
    <div class="clean-state">
      No diagnostics reported. Compilation succeeded.
      <div style="margin-top:0.4rem; color:#2a5a50;">Compiler: ${escapeHtml(meta.compiler)} | Time: ${meta.elapsed_ms} ms</div>
    </div>
  `;
}

function renderDiagnostics(items) {
  if (!items || items.length === 0) {
    resultsContainer.innerHTML = "";
    return;
  }

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
      </article>
    `;
  });

  resultsContainer.innerHTML = cards.join("\n");
}

async function runAnalysis() {
  const code = codeInput.value;
  if (!code.trim()) {
    setStatus("Please paste C code before running analysis.");
    return;
  }

  analyzeButton.disabled = true;
  setStatus("Compiling and generating NLP explanations...");
  runtimeElement.textContent = "";
  resultsContainer.innerHTML = "";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        compiler: compilerSelect.value,
        warnings: warningsToggle.checked,
        security: securityToggle.checked,
        prefer_model: preferModelToggle.checked,
      }),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Request failed.");
    }

    const meta = payload.meta || {};
    runtimeElement.textContent = `Runtime: ${meta.elapsed_ms || "-"} ms`;

    if (payload.success) {
      setStatus("Compilation successful.");
      renderCleanState(meta);
      return;
    }

    setStatus(`Found ${payload.diagnostics.length} diagnostic(s).`);
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
  setStatus("Loaded sample code.");
});
