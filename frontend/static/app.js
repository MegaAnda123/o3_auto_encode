"use strict";

const BUNDLE_REFRESH_MS = 5000;
const PROGRESS_REFRESH_MS = 1000;

const bundlesEl = document.getElementById("bundles");
const statusEl = document.getElementById("status-line");

let bundlesByName = new Map();
// Keys of <details> elements the user opened, so polling re-renders do not collapse them.
const openDetails = new Set();
// Last rendered payload, used to skip pointless re-renders.
let lastRenderSignature = "";

/* ------------------------------------------------------------ details state */

function detailsAttrs(key) {
    return `data-details-key="${key}" ${openDetails.has(key) ? "open" : ""}`;
}

// `toggle` does not bubble, so listen in the capture phase.
document.addEventListener(
    "toggle",
    (event) => {
        const key = event.target instanceof HTMLElement ? event.target.dataset.detailsKey : null;
        if (!key) return;
        if (event.target.open) {
            openDetails.add(key);
        } else {
            openDetails.delete(key);
        }
    },
    true
);

/* ---------------------------------------------------------------- formatting */

function formatBytes(bytes) {
    if (bytes === null || bytes === undefined) return "—";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let value = bytes;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
        value /= 1024;
        unit += 1;
    }
    return `${value.toFixed(value >= 100 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function formatBitrate(bps) {
    if (!bps) return "—";
    return `${(bps / 1_000_000).toFixed(2)} Mbps`;
}

function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatDuration(seconds) {
    if (seconds === null || seconds === undefined) return "—";
    const total = Math.round(seconds);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${m}m ${String(s).padStart(2, "0")}s`;
}

function formatNumber(value) {
    return value === null || value === undefined ? "—" : value.toLocaleString();
}

/* -------------------------------------------------------------------- render */

function statCell(label, value, className = "") {
    return `<div class="stat"><span class="label">${label}</span><span class="value ${className}">${value}</span></div>`;
}

function renderSourceStats(bundle) {
    const first = bundle.clips[0] || {};
    return `<div class="stats">
        ${statCell("Clips", formatNumber(bundle.clip_count))}
        ${statCell("Date", formatDate(bundle.creation_time))}
        ${statCell("Frames", formatNumber(bundle.total_frames))}
        ${statCell("Resolution", bundle.resolution || "—")}
        ${statCell("Bitrate", formatBitrate(first.bitrate))}
        ${statCell("Source size", formatBytes(bundle.total_size))}
    </div>`;
}

function renderEncodedStats(bundle) {
    const encoded = bundle.encoded;
    if (!encoded) {
        return `<p class="pending">Encoded stats appear once encoding is finished.</p>`;
    }
    const savings = encoded.savings_pct === null ? "—" : `${encoded.savings_pct.toFixed(1)} %`;
    return `<div class="stats">
        ${statCell("Encoded size", formatBytes(encoded.size))}
        ${statCell("Saved", savings, "savings")}
        ${statCell("Out resolution", encoded.resolution || "—")}
        ${statCell("Out bitrate", formatBitrate(encoded.bitrate))}
        ${statCell("Out codec", encoded.codec || "—")}
    </div>`;
}

function renderSettings(bundle) {
    const settings = bundle.settings;
    if (!settings) return "";
    return `<div class="stats">
        ${statCell("Encode codec", settings.codec || "—")}
        ${statCell("Preset", settings.preset || "—")}
        ${statCell("CRF / CQ", settings.crf || "—")}
    </div>
    <details ${detailsAttrs(`${bundle.name}::command`)}><summary>ffmpeg command</summary><code>${settings.command || "—"}</code></details>`;
}

function renderClips(bundle) {
    const rows = bundle.clips
        .map(
            (clip) => `<tr>
                <td>${clip.name}</td>
                <td>${clip.duration || "—"}</td>
                <td>${formatNumber(clip.frames)}</td>
                <td>${clip.resolution || "—"}</td>
                <td>${formatBitrate(clip.bitrate)}</td>
                <td>${formatBytes(clip.size)}</td>
            </tr>`
        )
        .join("");
    return `<details ${detailsAttrs(`${bundle.name}::clips`)}><summary>Raw clips used (${bundle.clip_count})</summary>
        <table>
            <thead><tr><th>Clip</th><th>Duration</th><th>Frames</th><th>Resolution</th><th>Bitrate</th><th>Size</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
    </details>`;
}

function renderBundle(bundle) {
    const canCompare = Boolean(bundle.encoded && bundle.encoded.exists);
    return `<article class="bundle" data-bundle="${bundle.name}">
        <div class="bundle-head">
            <h2>${bundle.name}</h2>
            <div>
                <span class="badge ${bundle.status}">${bundle.status}</span>
                <button type="button" data-compare="${bundle.name}" ${canCompare ? "" : "disabled"}>Compare</button>
            </div>
        </div>
        ${renderSourceStats(bundle)}
        ${renderEncodedStats(bundle)}
        ${renderSettings(bundle)}
        ${renderClips(bundle)}
        <div class="progress" data-progress hidden>
            <div class="progress-bar"><div data-progress-fill></div></div>
            <div class="progress-meta muted">
                <span data-progress-percent></span>
                <span data-progress-frames></span>
                <span data-progress-fps></span>
                <span data-progress-eta></span>
            </div>
        </div>
    </article>`;
}

/* --------------------------------------------------------------- data loading */

async function loadBundles() {
    try {
        const response = await fetch("/api/bundles");
        if (!response.ok) throw new Error(response.statusText);
        const data = await response.json();

        bundlesByName = new Map(data.bundles.map((bundle) => [bundle.name, bundle]));
        statusEl.textContent = `${data.bundles.length} bundle(s) · updated ${new Date().toLocaleTimeString()}`;

        // Only touch the DOM when something actually changed, otherwise open
        // dropdowns, text selection and video state would be thrown away.
        const signature = JSON.stringify(data.bundles);
        if (signature === lastRenderSignature) return;
        lastRenderSignature = signature;

        bundlesEl.innerHTML = data.bundles.length
            ? data.bundles.map(renderBundle).join("")
            : `<p class="muted">No bundles found yet.</p>`;
    } catch (error) {
        statusEl.textContent = `Failed to load bundles: ${error.message}`;
    }
}

function clearProgress() {
    document.querySelectorAll("[data-progress]").forEach((el) => (el.hidden = true));
}

async function loadProgress() {
    let data;
    try {
        const response = await fetch("/api/progress");
        if (!response.ok) throw new Error(response.statusText);
        data = await response.json();
    } catch {
        clearProgress();
        return;
    }

    if (!data.bundle || data.state !== "encoding" || data.stale) {
        clearProgress();
        return;
    }

    const card = document.querySelector(`.bundle[data-bundle="${CSS.escape(data.bundle)}"]`);
    if (!card) return;

    clearProgress();
    const container = card.querySelector("[data-progress]");
    container.hidden = false;
    const percent = data.percent ?? 0;
    container.querySelector("[data-progress-fill]").style.width = `${percent}%`;
    container.querySelector("[data-progress-percent]").textContent = `${percent.toFixed(1)} %`;
    container.querySelector("[data-progress-frames]").textContent =
        `${formatNumber(data.frame)} / ${formatNumber(data.total_frames)} frames`;
    container.querySelector("[data-progress-fps]").textContent = data.fps ? `${data.fps} fps` : "";
    container.querySelector("[data-progress-eta]").textContent =
        data.eta_s === null || data.eta_s === undefined ? "" : `ETA ${formatDuration(data.eta_s)}`;

    const badge = card.querySelector(".badge");
    badge.textContent = "processing";
    badge.className = "badge processing";
}

/* ------------------------------------------------------------------- compare */

const dialog = document.getElementById("compare");
const originalVideo = document.getElementById("video-original");
const encodedVideo = document.getElementById("video-encoded");
const syncToggle = document.getElementById("compare-sync");
const compareNote = document.getElementById("compare-note");

function openCompare(bundleName) {
    const bundle = bundlesByName.get(bundleName);
    if (!bundle || !bundle.encoded) return;

    document.getElementById("compare-title").textContent = bundleName;
    originalVideo.src = bundle.clips[0] ? bundle.clips[0].media_url : "";
    encodedVideo.src = bundle.encoded.media_url;
    compareNote.textContent =
        "Original side shows the first source clip only (full concat comparison is not implemented yet).";
    dialog.showModal();
}

function closeCompare() {
    originalVideo.pause();
    encodedVideo.pause();
    originalVideo.removeAttribute("src");
    encodedVideo.removeAttribute("src");
    dialog.close();
}

function mirror(source, target, action) {
    if (!syncToggle.checked) return;
    action(target, source);
}

originalVideo.addEventListener("play", () => mirror(originalVideo, encodedVideo, (t) => t.play()));
originalVideo.addEventListener("pause", () => mirror(originalVideo, encodedVideo, (t) => t.pause()));
originalVideo.addEventListener("seeked", () =>
    mirror(originalVideo, encodedVideo, (t, s) => (t.currentTime = s.currentTime))
);
encodedVideo.addEventListener("play", () => mirror(encodedVideo, originalVideo, (t) => t.play()));
encodedVideo.addEventListener("pause", () => mirror(encodedVideo, originalVideo, (t) => t.pause()));
encodedVideo.addEventListener("seeked", () =>
    mirror(encodedVideo, originalVideo, (t, s) => (t.currentTime = s.currentTime))
);

document.getElementById("compare-play").addEventListener("click", () => {
    if (originalVideo.paused) {
        originalVideo.play();
        encodedVideo.play();
    } else {
        originalVideo.pause();
        encodedVideo.pause();
    }
});
document.getElementById("compare-close").addEventListener("click", closeCompare);
dialog.addEventListener("close", closeCompare);

bundlesEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-compare]");
    if (button) openCompare(button.dataset.compare);
});

/* --------------------------------------------------------------------- start */

loadBundles().then(loadProgress);
setInterval(loadBundles, BUNDLE_REFRESH_MS);
setInterval(loadProgress, PROGRESS_REFRESH_MS);

