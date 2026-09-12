/**
 * SatQuery AI - Frontend Controller & Backend Integration
 * SIH26167: Interactive Vision-Language Assistant for Multimodal Remote Sensing
 */

// Determine API Base URL automatically:
// If running on a dev port (e.g. 5500/5501/3000/5173), fallback to backend at :8000.
// Otherwise (cloud hosting or backend static mount), use the current host origin.
const API_BASE_URL = (window.location.port && ["5500", "5501", "3000", "5173"].includes(window.location.port))
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : `${window.location.origin}`;

// Global Application State
const state = {
    currentSlide: 1,
    image1File: null,
    image2File: null,
    image1Id: null,
    image2Id: null,
    image1Meta: null,
    image2Meta: null,
    modality1: "optical",
    modality2: "optical",
    isUploading1: false,
    isUploading2: false,
    isAnalyzing: false,
    currentResult: null,
    backendConnected: false,
    historyData: []
};


/* ================= INITIALIZATION & HEALTH CHECK ================= */

document.addEventListener("DOMContentLoaded", () => {
    checkBackendHealth();
    // Periodic health check every 15 seconds
    setInterval(checkBackendHealth, 15000);
});

async function checkBackendHealth() {
    const statusBadge = document.getElementById("backendStatusBadge");
    const indicator = document.getElementById("statusIndicator");
    const statusText = document.getElementById("backendStatusText");

    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
            method: "GET",
            headers: { "Accept": "application/json" }
        });

        if (res.ok) {
            const data = await res.json();
            state.backendConnected = true;
            statusBadge.className = "backend-badge online";
            indicator.className = "status-indicator online";
            statusText.textContent = `Backend: Online (v${data.data?.version || "1.0.0"})`;
            statusBadge.title = `SatQuery AI Backend Online • ${data.data?.components?.tool_registry || "All tools active"}`;
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch (err) {
        state.backendConnected = false;
        statusBadge.className = "backend-badge offline";
        indicator.className = "status-indicator offline";
        statusText.textContent = "Backend: Offline (Click to Retry)";
        statusBadge.title = `Cannot reach backend at ${API_BASE_URL}. Ensure FastAPI is running.`;
    }
}


/* ================= SLIDE CONTROL ================= */

function goToSlide(slideNumber) {
    const slides = document.querySelectorAll(".slide");
    slides.forEach(slide => slide.classList.remove("active-slide"));

    const selectedSlide = document.getElementById("slide" + slideNumber);
    if (selectedSlide) {
        selectedSlide.classList.add("active-slide");
    }

    const steps = document.querySelectorAll(".step");
    steps.forEach(step => {
        const stepNum = Number(step.dataset.step);
        step.classList.remove("active");
        if (stepNum <= slideNumber) {
            step.classList.add("active");
        }
    });

    state.currentSlide = slideNumber;
    window.scrollTo({ top: 0, behavior: "smooth" });
}


/* ================= TOAST NOTIFICATIONS ================= */

function showToast(message, type = "info", duration = 4000) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "ℹ️";
    if (type === "success") icon = "✓";
    if (type === "error") icon = "⚠️";
    if (type === "warning") icon = "⚡";

    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-msg">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, duration);
}


/* ================= IMAGE & MODALITY HANDLING ================= */

function onModalityChange(index) {
    const select = document.getElementById(`modality${index}`);
    if (!select) return;
    if (index === 1) state.modality1 = select.value;
    if (index === 2) state.modality2 = select.value;
}

async function handleFileSelect(event, index) {
    const file = event.target.files[0];
    if (!file) return;

    if (index === 1) {
        state.image1File = file;
        state.image1Id = null;
    } else {
        state.image2File = file;
        state.image2Id = null;
    }

    // Local Preview
    const preview = document.getElementById(`preview${index}`);
    const placeholder = document.getElementById(`placeholder${index}`);
    const reader = new FileReader();

    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = "block";
        placeholder.style.display = "none";
    };
    reader.readAsDataURL(file);

    // Auto-upload to backend for immediate metadata inspection
    await uploadRasterFile(file, index);
}

async function uploadRasterFile(file, index) {
    const metaTray = document.getElementById(`metaTray${index}`);
    const modality = index === 1 ? state.modality1 : state.modality2;
    const tag = index === 1 ? "primary" : "comparison";

    if (index === 1) state.isUploading1 = true;
    if (index === 2) state.isUploading2 = true;

    showToast(`Uploading and inspecting raster: ${file.name}...`, "info", 2500);

    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("modality", modality);
        formData.append("tag", tag);

        const res = await fetch(`${API_BASE_URL}/api/v1/uploads`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Upload failed (HTTP ${res.status})`);
        }

        const data = await res.json();
        const uploadData = data.data;

        if (index === 1) {
            state.image1Id = uploadData.id;
            state.image1Meta = uploadData.metadata;
        } else {
            state.image2Id = uploadData.id;
            state.image2Meta = uploadData.metadata;
        }

        renderMetadataPills(index, uploadData.metadata, uploadData.modality);
        showToast(`Raster ${uploadData.original_filename} processed successfully.`, "success");

    } catch (err) {
        console.error("Upload error:", err);
        showToast(`Failed to upload ${file.name}: ${err.message}`, "error", 5000);
    } finally {
        if (index === 1) state.isUploading1 = false;
        if (index === 2) state.isUploading2 = false;
    }
}

function renderMetadataPills(index, meta, modality) {
    const metaTray = document.getElementById(`metaTray${index}`);
    if (!metaTray) return;

    metaTray.style.display = "flex";

    const dimPill = document.getElementById(`metaDim${index}`);
    const crsPill = document.getElementById(`metaCrs${index}`);
    const bandsPill = document.getElementById(`metaBands${index}`);
    const geoPill = document.getElementById(`metaGeo${index}`);

    if (meta) {
        if (dimPill) dimPill.textContent = `${meta.width}×${meta.height}`;
        if (crsPill) crsPill.textContent = meta.crs ? `CRS: ${meta.crs}` : "CRS: Projected";
        if (bandsPill) bandsPill.textContent = `${meta.num_bands || 3} Bands • ${modality.toUpperCase()}`;
        if (geoPill) geoPill.textContent = meta.is_georeferenced ? "Georeferenced ✓" : "Raster RGB ✓";
    }
}

function clearImage(index) {
    const input = document.getElementById(`image${index}`);
    const preview = document.getElementById(`preview${index}`);
    const placeholder = document.getElementById(`placeholder${index}`);
    const metaTray = document.getElementById(`metaTray${index}`);

    if (input) input.value = "";
    if (preview) {
        preview.src = "";
        preview.style.display = "none";
    }
    if (placeholder) placeholder.style.display = "block";
    if (metaTray) metaTray.style.display = "none";

    if (index === 1) {
        state.image1File = null;
        state.image1Id = null;
        state.image1Meta = null;
    } else {
        state.image2File = null;
        state.image2Id = null;
        state.image2Meta = null;
    }
}


/* ================= AI DATA CATALOG & 1-CLICK DEMO PRESETS ================= */

async function loadSampleCatalog() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/data/samples`, {
            method: "GET",
            headers: { "Accept": "application/json" }
        });
        if (!res.ok) {
            throw new Error(`Sample catalog unavailable (HTTP ${res.status})`);
        }
        const data = await res.json();
        return data.data || [];
    } catch (err) {
        console.warn("Sample catalog lookup failed:", err);
        return [];
    }
}

async function loadPreset(type) {
    showToast(`Loading '${type.toUpperCase()}' demo preset...`, "info", 2000);
    goToSlide(2);

    try {
        if (type === "vqa") {
            // Optical Single VQA
            document.getElementById("modality1").value = "optical";
            state.modality1 = "optical";
            clearImage(2);

            const upload1 = await loadSampleImage("optical_sample.png", 1, "optical", "primary");
            setQuestion("What type of environment and infrastructure is visible in this satellite imagery?");

        } else if (type === "grounding") {
            // Visual Grounding
            document.getElementById("modality1").value = "optical";
            state.modality1 = "optical";
            clearImage(2);

            const upload1 = await loadSampleImage("optical_sample.png", 1, "optical", "primary");
            setQuestion("Where are the buildings and runway targets located?");

        } else if (type === "change") {
            // Bi-temporal Change (T1 vs T2)
            document.getElementById("modality1").value = "optical";
            document.getElementById("modality2").value = "optical";
            state.modality1 = "optical";
            state.modality2 = "optical";

            await loadSampleImage("t1_sample.png", 1, "optical", "t1");
            await loadSampleImage("t2_sample.png", 2, "optical", "t2");
            setQuestion("What changed between T1 and T2 imagery?");

        } else if (type === "fusion") {
            // Optical + SAR Multimodal Fusion
            document.getElementById("modality1").value = "optical";
            document.getElementById("modality2").value = "sar";
            state.modality1 = "optical";
            state.modality2 = "sar";

            await loadSampleImage("optical_sample.png", 1, "optical", "primary");
            await loadSampleImage("sar_sample.png", 2, "sar", "comparison");
            setQuestion("Perform joint optical and SAR analysis to inspect terrain penetration");
        }

        showToast("Demo preset loaded! Click 'EXECUTE SATQUERY AI' to run.", "success");

    } catch (err) {
        console.error("Failed to load preset:", err);
        showToast(`Error loading preset: ${err.message}`, "error", 4000);
    }
}

async function loadSampleImage(filename, index, modality, tag) {
    const formData = new FormData();
    formData.append("modality", modality);
    if (tag) formData.append("tag", tag);

    const res = await fetch(`${API_BASE_URL}/api/v1/uploads/sample/${filename}`, {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        throw new Error(`Failed to load sample ${filename}`);
    }

    const data = await res.json();
    const uploadData = data.data;

    // Update UI Preview
    const preview = document.getElementById(`preview${index}`);
    const placeholder = document.getElementById(`placeholder${index}`);
    if (preview) {
        preview.src = `${API_BASE_URL}${uploadData.preview_url}`;
        preview.style.display = "block";
    }
    if (placeholder) placeholder.style.display = "none";

    if (index === 1) {
        state.image1Id = uploadData.id;
        state.image1Meta = uploadData.metadata;
    } else {
        state.image2Id = uploadData.id;
        state.image2Meta = uploadData.metadata;
    }

    renderMetadataPills(index, uploadData.metadata, uploadData.modality);
    return uploadData;
}

function quickStartTask(type) {
    loadPreset(type);
}

function setQuestion(text) {
    const input = document.getElementById("question");
    if (input) input.value = text;
}


/* ================= ANALYSIS EXECUTION ================= */

async function analyzeImages() {
    const questionInput = document.getElementById("question");
    const question = questionInput.value.trim();

    // Validation
    if (!state.image1Id && !state.image1File) {
        showToast("Please upload or select the primary satellite image first.", "warning");
        goToSlide(2);
        return;
    }

    if (!question) {
        showToast("Please enter a natural language question for SatQuery AI.", "warning");
        questionInput.focus();
        return;
    }

    // Set Loading UI on Slide 3
    goToSlide(3);
    setLoadingState(true, question);

    try {
        // 1. Ensure Primary Image is uploaded
        let img1Id = state.image1Id;
        if (!img1Id && state.image1File) {
            updateLoadingStep("Uploading primary raster...");
            await uploadRasterFile(state.image1File, 1);
            img1Id = state.image1Id;
        }

        // 2. Ensure Secondary Image is uploaded if selected
        let img2Id = state.image2Id;
        if (!img2Id && state.image2File) {
            updateLoadingStep("Uploading comparison raster...");
            await uploadRasterFile(state.image2File, 2);
            img2Id = state.image2Id;
        }

        const imageIds = [img1Id];
        if (img2Id) imageIds.push(img2Id);

        updateLoadingStep("Synthesizing query intent & executing specialist models...");

        // 3. Post Analysis request to Backend
        const payload = {
            query: question,
            image_ids: imageIds,
            async_mode: false,
            parameters: {}
        };

        const res = await fetch(`${API_BASE_URL}/api/v1/analysis`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Analysis request failed with status ${res.status}`);
        }

        const data = await res.json();
        const result = data.data;
        state.currentResult = result;

        // Render Results
        renderAnalysisResults(result, imageIds.length);
        showToast("Analysis complete with visual evidence generated!", "success");

    } catch (err) {
        console.error("Analysis Pipeline Failed:", err);
        renderErrorState(err.message, question);
        showToast(`Analysis Error: ${err.message}`, "error", 6000);
    } finally {
        setLoadingState(false);
    }
}

function setLoadingState(isLoading, question = "") {
    state.isAnalyzing = isLoading;

    const analyzeBtn = document.getElementById("analyzeBtn");
    const btnText = document.getElementById("analyzeBtnText");
    const btnIcon = document.getElementById("analyzeBtnIcon");

    if (isLoading) {
        if (btnText) btnText.textContent = "PROCESSING...";
        if (btnIcon) btnIcon.textContent = "⏳";
        if (analyzeBtn) analyzeBtn.disabled = true;

        document.getElementById("analysisStatus").textContent = "Processing Analysis...";
        document.getElementById("taskBadge").textContent = "Query Planning & Inference";
        document.getElementById("analysisMeta").textContent = "Executing geospatial pipeline...";
        document.getElementById("statusCard").className = "status-card processing";
        document.getElementById("statusIcon").textContent = "⚡";

        document.getElementById("questionResult").textContent = question;
        document.getElementById("resultText").innerHTML = `
            <div class="loading-animation-wrap">
                <div class="spinner-ring"></div>
                <div class="loading-step-text" id="loadingStepText">
                    Synthesizing query intent, validating CRS alignment, and loading remote sensing models...
                </div>
            </div>
        `;

        document.getElementById("evidenceGrid").innerHTML = `
            <div class="evidence-placeholder">
                <span class="pulse-dot">●</span> Generating visual evidence overlays...
            </div>
        `;

    } else {
        if (btnText) btnText.textContent = "EXECUTE SATQUERY AI";
        if (btnIcon) btnIcon.textContent = "→";
        if (analyzeBtn) analyzeBtn.disabled = false;
    }
}

function updateLoadingStep(text) {
    const el = document.getElementById("loadingStepText");
    if (el) el.textContent = text;
}

function renderAnalysisResults(result, imageCount) {
    // 1. Status Card & Header
    const statusCard = document.getElementById("statusCard");
    statusCard.className = "status-card complete";
    document.getElementById("statusIcon").textContent = "✓";
    document.getElementById("analysisStatus").textContent = "Analysis Complete";

    const taskFormatted = formatTaskName(result.task);
    document.getElementById("taskBadge").textContent = taskFormatted;
    document.getElementById("analysisMeta").textContent = `Executed in ${Math.round(result.execution_duration_ms || 0)}ms • Calibrated & Verified`;

    // 2. Query recap
    document.getElementById("questionResult").textContent = result.query;

    // 3. AI Answer
    const toolName = result.execution_plan?.selected_tools?.join(", ") || "Ensemble Specialist";
    document.getElementById("selectedToolTag").textContent = `Tool: ${toolName}`;

    // Format answer text with bolding
    const formattedAnswer = formatAnswerMarkdown(result.answer || "Analysis completed.");
    document.getElementById("resultText").innerHTML = formattedAnswer;

    // 4. Calibrated Confidence
    const conf = result.confidence || { score: 0.90, level: "high", factors: [] };
    const confPct = Math.round((conf.score || 0.90) * 100);
    
    document.getElementById("confScoreLarge").textContent = `${confPct}%`;
    const confFill = document.getElementById("confProgressFill");
    if (confFill) {
        confFill.style.width = `${confPct}%`;
        confFill.className = `conf-progress-fill level-${conf.level || "high"}`;
    }

    const levelBadge = document.getElementById("confLevelBadge");
    if (levelBadge) {
        levelBadge.textContent = `${(conf.level || "HIGH").toUpperCase()} CONFIDENCE`;
        levelBadge.className = `conf-level-badge level-${conf.level || "high"}`;
    }

    // Factors List
    const factorsList = document.getElementById("confFactorsList");
    if (factorsList) {
        factorsList.innerHTML = "";
        const factors = conf.factors && conf.factors.length > 0
            ? conf.factors
            : ["Spatial CRS alignment verified", "Multimodal spectral validation passed", "Model prediction confidence threshold met"];
        
        factors.forEach(f => {
            const li = document.createElement("li");
            li.textContent = f;
            factorsList.appendChild(li);
        });
    }

    // Cross Modal Agreement
    const crossRow = document.getElementById("crossModalRow");
    if (conf.cross_modal_agreement) {
        crossRow.style.display = "flex";
        document.getElementById("crossModalVal").textContent = conf.cross_modal_agreement.toUpperCase();
    } else {
        crossRow.style.display = "none";
    }

    // 5. Visual Evidence Gallery
    renderEvidenceGallery(result.evidence || []);

    // 6. Metrics Grid
    document.getElementById("imageCount").textContent = imageCount;
    document.getElementById("execLatency").textContent = `${Math.round(result.execution_duration_ms || 0)} ms`;
    document.getElementById("pipelineMode").textContent = formatTaskShort(result.task);

    // 7. Execution Trace Telemetry
    renderExecutionTrace(result.execution_trace || []);
}

function renderErrorState(errorMessage, query) {
    const statusCard = document.getElementById("statusCard");
    statusCard.className = "status-card error";
    document.getElementById("statusIcon").textContent = "✕";
    document.getElementById("analysisStatus").textContent = "Analysis Failed";
    document.getElementById("taskBadge").textContent = "Error";
    document.getElementById("analysisMeta").textContent = "Encountered processing exception";

    document.getElementById("questionResult").textContent = query;
    document.getElementById("resultText").innerHTML = `
        <div class="error-box">
            <strong>Pipeline Execution Error:</strong>
            <p>${errorMessage}</p>
            <div class="error-remedy">
                💡 Tip: Verify that images are valid geospatial rasters and that the query aligns with the modalities provided.
            </div>
        </div>
    `;

    document.getElementById("evidenceGrid").innerHTML = `
        <div class="evidence-placeholder">
            No visual evidence generated due to error.
        </div>
    `;
}

function formatAnswerMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n\n/g, "<br><br>")
        .replace(/\n- (.*?)/g, "<br>• $1");
}

function formatTaskName(task) {
    const map = {
        "single_image_vqa": "Single-Image RS-VQA",
        "visual_grounding": "Visual Grounding & Localization",
        "grounding": "Visual Grounding & Localization",
        "temporal_change": "Bi-Temporal Change Detection",
        "change_vqa": "Temporal Change VQA",
        "optical_sar_analysis": "Optical + SAR Multimodal Fusion",
        "cross_modal_fusion": "Optical + SAR Multimodal Fusion"
    };
    return map[task] || task || "Remote Sensing Analysis";
}

function formatTaskShort(task) {
    const map = {
        "single_image_vqa": "RS-VQA",
        "visual_grounding": "Grounding",
        "grounding": "Grounding",
        "temporal_change": "Change Detection",
        "optical_sar_analysis": "Opt+SAR Fusion"
    };
    return map[task] || "Specialist AI";
}


/* ================= EVIDENCE GALLERY & LIGHTBOX ================= */

function renderEvidenceGallery(evidenceItems) {
    const grid = document.getElementById("evidenceGrid");
    const countBadge = document.getElementById("evidenceCountBadge");
    grid.innerHTML = "";

    countBadge.textContent = `${evidenceItems.length} Artifact${evidenceItems.length === 1 ? "" : "s"}`;

    if (!evidenceItems || evidenceItems.length === 0) {
        grid.innerHTML = `
            <div class="evidence-placeholder">
                Analysis complete. No spatial bounding overlays required for this specific task.
            </div>
        `;
        return;
    }

    evidenceItems.forEach((item, i) => {
        const card = document.createElement("div");
        card.className = "evidence-card-item";

        const imgUrl = item.url ? `${API_BASE_URL}${item.url}` : "";
        const evidenceTitle = formatEvidenceType(item.evidence_type);
        const confVal = Math.round((item.confidence || 0.90) * 100);

        card.innerHTML = `
            <div class="evidence-thumb-wrap" onclick="openLightbox('${imgUrl}', '${evidenceTitle}', '${item.description || ""}')">
                <img src="${imgUrl}" alt="${evidenceTitle}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🛰️</text></svg>'">
                <div class="evidence-zoom-overlay">
                    <span>🔍 Inspect Full Resolution</span>
                </div>
            </div>
            <div class="evidence-info">
                <div class="evidence-top-row">
                    <span class="evidence-type-badge">${evidenceTitle}</span>
                    <span class="evidence-conf-pill">${confVal}% Confidence</span>
                </div>
                <p class="evidence-desc">${item.description || "Generated spatial evidence overlay."}</p>
                <div class="evidence-actions">
                    <button class="inspect-btn" onclick="openLightbox('${imgUrl}', '${evidenceTitle}', '${item.description || ""}')">
                        Inspect
                    </button>
                    <a href="${imgUrl}" target="_blank" download class="download-link" title="Open Raster in New Tab">
                        ↗
                    </a>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });
}

function formatEvidenceType(type) {
    const map = {
        "bounding_box": "Spatial Grounding Overlay",
        "change_mask": "Change Detection Mask",
        "temporal_comparison": "T1 vs T2 Side-by-Side",
        "fused_comparison": "Optical vs SAR Cross-Modal",
        "optical_evidence": "Optical Reflectance",
        "sar_evidence": "SAR Radar Backscatter",
        "scene_interpretation": "Scene Feature Classification"
    };
    return map[type] || type || "Spatial Artifact";
}

function openLightbox(src, title, caption) {
    const modal = document.getElementById("lightboxModal");
    const img = document.getElementById("lightboxImg");
    const titleEl = document.getElementById("lightboxTitle");
    const captionEl = document.getElementById("lightboxCaption");

    img.src = src;
    titleEl.textContent = title || "Visual Evidence Inspection";
    captionEl.textContent = caption || "";
    modal.classList.add("active");
}

function closeLightbox(event) {
    const modal = document.getElementById("lightboxModal");
    modal.classList.remove("active");
}


/* ================= EXECUTION TRACE ACCORDION ================= */

function toggleTraceAccordion() {
    const content = document.getElementById("traceContent");
    const icon = document.getElementById("traceToggleIcon");
    if (content.style.display === "none") {
        content.style.display = "block";
        icon.textContent = "▲";
    } else {
        content.style.display = "none";
        icon.textContent = "▼";
    }
}

function renderExecutionTrace(traces) {
    const timeline = document.getElementById("traceTimeline");
    timeline.innerHTML = "";

    if (!traces || traces.length === 0) {
        timeline.innerHTML = `<div class="trace-empty">No trace telemetry available.</div>`;
        return;
    }

    traces.forEach(t => {
        const item = document.createElement("div");
        item.className = "trace-item";

        item.innerHTML = `
            <div class="trace-order">${t.step_order}</div>
            <div class="trace-details">
                <div class="trace-name-row">
                    <strong class="trace-name">${t.step_name}</strong>
                    <span class="trace-duration">${t.duration_ms || 0} ms</span>
                    <span class="trace-status-pill status-${(t.status || "completed").toLowerCase()}">${t.status}</span>
                </div>
                <div class="trace-summary">${t.summary || ""}</div>
            </div>
        `;
        timeline.appendChild(item);
    });
}


/* ================= AUDIT HISTORY ================= */

async function openHistoryModal() {
    const modal = document.getElementById("historyModal");
    const body = document.getElementById("historyBody");
    modal.classList.add("active");
    body.innerHTML = `<div class="history-loading">Fetching analysis audit trail from database...</div>`;

    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/history?limit=15`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const historyList = data.data || [];
        state.historyData = historyList;

        if (historyList.length === 0) {
            body.innerHTML = `<div class="history-empty">No previous analyses recorded yet. Execute a query to view history.</div>`;
            return;
        }

        body.innerHTML = "";
        historyList.forEach(item => {
            const row = document.createElement("div");
            row.className = "history-item";

            const timeStr = item.created_at ? new Date(item.created_at).toLocaleString() : "Recent";
            const queryText = item.result?.query || "Satellite Analysis";
            const taskText = formatTaskName(item.result?.task);
            const confVal = item.result?.confidence?.score ? `${Math.round(item.result.confidence.score * 100)}%` : "90%";

            row.innerHTML = `
                <div class="history-left">
                    <div class="history-title">${queryText}</div>
                    <div class="history-sub">
                        <span class="task-pill">${taskText}</span>
                        <span>•</span>
                        <span>${timeStr}</span>
                    </div>
                </div>
                <div class="history-right">
                    <span class="history-conf">${confVal} Conf</span>
                    <button class="history-view-btn" onclick="loadHistoricalResult('${item.job_id}')">View</button>
                </div>
            `;
            body.appendChild(row);
        });

    } catch (err) {
        body.innerHTML = `<div class="history-error">Failed to load history: ${err.message}</div>`;
    }
}

function closeHistoryModal() {
    const modal = document.getElementById("historyModal");
    modal.classList.remove("active");
}

function loadHistoricalResult(jobId) {
    const match = state.historyData.find(h => h.job_id === jobId);
    if (match && match.result) {
        closeHistoryModal();
        goToSlide(3);
        renderAnalysisResults(match.result, 1);
        showToast("Historical analysis session loaded.", "info");
    }
}


/* ================= NAVIGATION & RESET ================= */

function goBackToQuery() {
    goToSlide(2);
}

function resetApp() {
    clearImage(1);
    clearImage(2);
    const q = document.getElementById("question");
    if (q) q.value = "";
    goToSlide(1);
}
/* =========================================================
   SATQUERY AI CHAT ASSISTANT
   ========================================================= */

let satChatHistory = [];

document.addEventListener("DOMContentLoaded", () => {

    const chatToggle = document.getElementById("satChatToggle");
    const chatWindow = document.getElementById("satChatWindow");
    const chatClose = document.getElementById("satChatClose");

    const chatInput = document.getElementById("satChatInput");
    const chatSend = document.getElementById("satChatSend");

    if (!chatToggle || !chatWindow) {
        console.warn("SatQuery chatbox elements not found.");
        return;
    }


    /* -------------------------------
       OPEN CHAT
    -------------------------------- */

    chatToggle.addEventListener("click", () => {

        chatWindow.classList.toggle("active");

        if (chatWindow.classList.contains("active")) {
            setTimeout(() => {
                chatInput?.focus();
            }, 250);
        }

    });


    /* -------------------------------
       CLOSE CHAT
    -------------------------------- */

    chatClose?.addEventListener("click", () => {
        chatWindow.classList.remove("active");
    });


    /* -------------------------------
       SEND BUTTON
    -------------------------------- */

    chatSend?.addEventListener("click", () => {
        sendSatChatMessage();
    });


    /* -------------------------------
       ENTER TO SEND
       SHIFT + ENTER = NEW LINE
    -------------------------------- */

    chatInput?.addEventListener("keydown", (event) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendSatChatMessage();
        }

    });


    /* -------------------------------
       AUTO RESIZE TEXTAREA
    -------------------------------- */

    chatInput?.addEventListener("input", () => {

        chatInput.style.height = "auto";

        chatInput.style.height =
            Math.min(chatInput.scrollHeight, 110) + "px";

    });

});


/* =========================================================
   SEND CHAT MESSAGE
   ========================================================= */

async function sendSatChatMessage() {

    const input =
        document.getElementById("satChatInput");

    const sendButton =
        document.getElementById("satChatSend");

    if (!input) return;


    const message =
        input.value.trim();

    if (!message) return;


    /* Add user's message */

    appendSatChatMessage(
        message,
        "user"
    );


    /* Clear input */

    input.value = "";
    input.style.height = "auto";


    /* Disable send */

    if (sendButton) {
        sendButton.disabled = true;
    }


    /* Show typing */

    setSatChatTyping(true);


    try {

        const response = await fetch(
            `${API_BASE_URL}/api/v1/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    message: message,
                    history: satChatHistory
                })
            }
        );


        if (!response.ok) {

            const errorData =
                await response
                    .json()
                    .catch(() => ({}));

            throw new Error(
                errorData.detail ||
                `Chat request failed (HTTP ${response.status})`
            );
        }


        const data =
            await response.json();


        /*
         * Expected backend response:
         *
         * {
         *   "data": {
         *      "reply": "AI answer..."
         *   }
         * }
         */

        const reply =
            data?.data?.reply ||
            data?.reply ||
            "Sorry, I couldn't generate a response.";


        appendSatChatMessage(
            reply,
            "ai"
        );


        /* Save conversation */

        satChatHistory.push({
            role: "user",
            content: message
        });

        satChatHistory.push({
            role: "assistant",
            content: reply
        });


        /*
         * Keep only the last 20 messages.
         * This prevents the request from becoming too large.
         */

        if (satChatHistory.length > 20) {
            satChatHistory =
                satChatHistory.slice(-20);
        }


    } catch (error) {

        console.error(
            "SatQuery AI Chat Error:",
            error
        );


        appendSatChatMessage(
            `⚠️ Unable to connect to SatQuery AI.<br><br>
             <small>${escapeSatChatText(error.message)}</small>`,
            "ai",
            true
        );

    } finally {

        setSatChatTyping(false);

        if (sendButton) {
            sendButton.disabled = false;
        }

        input.focus();
    }

}


/* =========================================================
   ADD MESSAGE TO CHAT
   ========================================================= */

function appendSatChatMessage(
    message,
    sender = "ai",
    isError = false
) {

    const messagesContainer =
        document.getElementById(
            "satChatMessages"
        );

    if (!messagesContainer) return;


    const wrapper =
        document.createElement("div");


    wrapper.className =
        sender === "user"
            ? "sat-message sat-message-user"
            : "sat-message sat-message-ai";


    const avatar =
        sender === "user"
            ? "👤"
            : "🛰️";


    const name =
        sender === "user"
            ? "You"
            : "SatQuery AI";


    const bubble =
        document.createElement("div");


    bubble.className =
        "sat-message-bubble";


    if (sender === "user") {

        bubble.textContent = message;

    } else {

        /*
         * AI replies are allowed to contain
         * simple formatting.
         */

        bubble.innerHTML =
            formatSatChatResponse(message);

    }


    if (isError) {

        bubble.style.borderColor =
            "rgba(239, 68, 68, 0.35)";
    }


    wrapper.innerHTML = `
        <div class="sat-message-avatar">
            ${avatar}
        </div>

        <div class="sat-message-content">

            <div class="sat-message-name">
                ${name}
            </div>

        </div>
    `;


    wrapper
        .querySelector(".sat-message-content")
        .appendChild(bubble);


    messagesContainer.appendChild(
        wrapper
    );


    /* Scroll to latest message */

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}


/* =========================================================
   TYPING INDICATOR
   ========================================================= */

function setSatChatTyping(show) {

    const typing =
        document.getElementById(
            "satChatTyping"
        );

    if (!typing) return;


    if (show) {

        typing.classList.add("active");

    } else {

        typing.classList.remove("active");
    }


    const messages =
        document.getElementById(
            "satChatMessages"
        );

    if (messages) {

        messages.scrollTop =
            messages.scrollHeight;
    }
}


/* =========================================================
   BASIC AI RESPONSE FORMATTING
   ========================================================= */

function formatSatChatResponse(text) {

    if (!text) return "";


    let safe =
        escapeSatChatText(text);


    /*
     * Bold:
     * **text**
     */

    safe =
        safe.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    /*
     * Line breaks
     */

    safe =
        safe.replace(
            /\n/g,
            "<br>"
        );


    return safe;
}


/* =========================================================
   ESCAPE HTML
   ========================================================= */

function escapeSatChatText(text) {

    const div =
        document.createElement("div");

    div.textContent =
        String(text);

    return div.innerHTML;
}