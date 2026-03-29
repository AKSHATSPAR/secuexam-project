/* ========================================================================
   SecuExam — Shared JavaScript Utilities
   ======================================================================== */

let deferredInstallPrompt = null;

function isStandaloneMode() {
    return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function isIosDevice() {
    return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
}

function isLikelyMobileDevice() {
    return window.innerWidth <= 900 || /android|iphone|ipad|ipod/i.test(window.navigator.userAgent);
}

function dismissInstallBanner() {
    localStorage.setItem('secuexam-install-banner-dismissed', '1');
    const banner = document.getElementById('install-banner');
    if (banner) banner.remove();
}

async function promptPwaInstall() {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    dismissInstallBanner();
}

function renderInstallBanner(mode) {
    if (!isLikelyMobileDevice() || isStandaloneMode()) return;
    if (localStorage.getItem('secuexam-install-banner-dismissed') === '1') return;
    if (document.getElementById('install-banner')) return;

    const banner = document.createElement('div');
    banner.id = 'install-banner';
    banner.className = 'install-banner';

    if (mode === 'prompt') {
        banner.innerHTML = `
            <div class="install-banner-copy">
                <strong>Install SecuExam</strong>
                <span>Open it like a real mobile app from your home screen.</span>
            </div>
            <div class="install-banner-actions">
                <button type="button" class="btn btn-primary btn-sm" id="install-now-btn">Install</button>
                <button type="button" class="btn btn-secondary btn-sm" id="install-dismiss-btn">Later</button>
            </div>
        `;
    } else {
        banner.innerHTML = `
            <div class="install-banner-copy">
                <strong>Add SecuExam to Home Screen</strong>
                <span>In Safari, tap Share and then choose Add to Home Screen.</span>
            </div>
            <div class="install-banner-actions">
                <button type="button" class="btn btn-secondary btn-sm" id="install-dismiss-btn">Dismiss</button>
            </div>
        `;
    }

    document.body.appendChild(banner);
    document.getElementById('install-dismiss-btn')?.addEventListener('click', dismissInstallBanner);
    document.getElementById('install-now-btn')?.addEventListener('click', promptPwaInstall);
}

function registerPwaSupport() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js').catch(() => {});
        });
    }

    window.addEventListener('beforeinstallprompt', (event) => {
        event.preventDefault();
        deferredInstallPrompt = event;
        renderInstallBanner('prompt');
    });

    window.addEventListener('appinstalled', () => {
        deferredInstallPrompt = null;
        dismissInstallBanner();
        showToast('SecuExam installed on this device', 'success');
    });

    document.addEventListener('DOMContentLoaded', () => {
        document.body.classList.toggle('standalone-app', isStandaloneMode());
        if (isIosDevice() && !isStandaloneMode()) {
            renderInstallBanner('ios');
        }
    });
}

registerPwaSupport();

// Toast notification system
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Format date/time
function formatDateTime(isoStr) {
    if (!isoStr) return '—';
    const d = new Date(isoStr);
    return d.toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: true
    });
}

// Format relative time
function timeAgo(isoStr) {
    const now = new Date();
    const d = new Date(isoStr);
    const diff = (now - d) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// Countdown timer
function getCountdown(targetIso) {
    const now = new Date();
    const target = new Date(targetIso);
    const diff = Math.max(0, (target - now) / 1000);
    
    const days = Math.floor(diff / 86400);
    const hours = Math.floor((diff % 86400) / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    const seconds = Math.floor(diff % 60);
    
    return { days, hours, minutes, seconds, total: diff };
}

function renderCountdown(targetIso) {
    const cd = getCountdown(targetIso);
    if (cd.total <= 0) return '<span class="badge badge-success">🔓 UNLOCKED</span>';
    
    let html = '<div class="countdown">';
    if (cd.days > 0) html += `<div class="countdown-unit"><div class="value">${cd.days}</div><div class="label-text">Days</div></div><span class="countdown-separator">:</span>`;
    html += `<div class="countdown-unit"><div class="value">${String(cd.hours).padStart(2,'0')}</div><div class="label-text">Hrs</div></div>`;
    html += `<span class="countdown-separator">:</span>`;
    html += `<div class="countdown-unit"><div class="value">${String(cd.minutes).padStart(2,'0')}</div><div class="label-text">Min</div></div>`;
    html += `<span class="countdown-separator">:</span>`;
    html += `<div class="countdown-unit"><div class="value">${String(cd.seconds).padStart(2,'0')}</div><div class="label-text">Sec</div></div>`;
    html += '</div>';
    return html;
}

// API helper
async function apiFetch(url, options = {}) {
    try {
        const res = await fetch(url, {
            ...options,
            headers: {
                ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
                ...options.headers
            }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        return data;
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}

// Logout
function logout() {
    window.location.replace('/logout');
}

// Check auth
async function checkAuth(expectedRole) {
    try {
        const res = await fetch('/api/me');
        if (!res.ok) {
            window.location.href = '/';
            return null;
        }
        const data = await res.json();
        if (expectedRole && data.role !== expectedRole) {
            window.location.href = '/';
            return null;
        }
        return data;
    } catch {
        window.location.href = '/';
        return null;
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// File size formatter
function formatFileSize(mb) {
    if (mb < 1) return `${(mb * 1024).toFixed(0)} KB`;
    return `${mb.toFixed(2)} MB`;
}

function availabilityMeta(paper) {
    if (paper.is_expired || paper.availability_state === 'expired') {
        return {
            label: 'Expired',
            icon: '⏳',
            badgeClass: 'badge-warning',
            accentClass: 'danger'
        };
    }
    if (paper.is_unlocked || paper.availability_state === 'available') {
        return {
            label: 'Available',
            icon: '🔓',
            badgeClass: 'badge-success',
            accentClass: 'success'
        };
    }
    return {
        label: 'Time-Locked',
        icon: '🔒',
        badgeClass: 'badge-info',
        accentClass: 'accent'
    };
}

function classificationMeta(classification) {
    const normalized = classification || 'Confidential';
    if (normalized === 'Critical') {
        return { label: 'Critical', badgeClass: 'badge-danger' };
    }
    if (normalized === 'Restricted') {
        return { label: 'Restricted', badgeClass: 'badge-warning' };
    }
    return { label: 'Confidential', badgeClass: 'badge-accent' };
}

function renderAvailabilityBadge(paper) {
    const meta = availabilityMeta(paper);
    return `<span class="badge ${meta.badgeClass}">${meta.icon} ${meta.label}</span>`;
}

function renderClassificationBadge(classification) {
    const meta = classificationMeta(classification);
    return `<span class="badge ${meta.badgeClass}">${meta.label}</span>`;
}

function relativeTimeLabel(minutes) {
    if (minutes === null || minutes === undefined || Number.isNaN(minutes)) return '—';
    if (minutes <= 0) return 'Live now';
    const totalMinutes = Math.abs(minutes);
    const days = Math.floor(totalMinutes / (60 * 24));
    const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
    const mins = totalMinutes % 60;
    const parts = [];
    if (days) parts.push(`${days}d`);
    if (hours) parts.push(`${hours}h`);
    if (mins || parts.length === 0) parts.push(`${mins}m`);
    return `in ${parts.join(' ')}`;
}

function minutesUntil(isoStr) {
    if (!isoStr) return null;
    return Math.floor((new Date(isoStr) - new Date()) / 60000);
}

function sortPapersForOps(papers) {
    return [...papers].sort((left, right) => {
        const leftState = availabilityMeta(left);
        const rightState = availabilityMeta(right);
        const rank = { success: 0, accent: 1, danger: 2 };
        if (rank[leftState.accentClass] !== rank[rightState.accentClass]) {
            return rank[leftState.accentClass] - rank[rightState.accentClass];
        }
        return new Date(left.exam_start_time) - new Date(right.exam_start_time);
    });
}

function findNextOperationalPaper(papers) {
    return sortPapersForOps(
        papers.filter(paper => !paper.is_expired)
    )[0] || null;
}

function renderOpsPaperCard(paper, actionHtml = '') {
    const state = availabilityMeta(paper);
    const classification = classificationMeta(paper.classification);
    const timeLabel = paper.is_unlocked
        ? `Exam live until ${formatDateTime(paper.exam_end_time)}`
        : `Unlocks ${relativeTimeLabel(paper.minutes_to_unlock)}`;
    return `
        <article class="ops-paper-card ${state.accentClass}">
            <div class="ops-paper-head">
                <div>
                    <div class="eyebrow-text">Trace ${escapeHtml(paper.trace_id || '—')}</div>
                    <h3>${escapeHtml(paper.subject)}</h3>
                </div>
                <div class="ops-paper-badges">
                    <span class="badge ${classification.badgeClass}">${classification.label}</span>
                    <span class="badge ${state.badgeClass}">${state.icon} ${state.label}</span>
                </div>
            </div>
            <div class="ops-paper-meta">
                <div><span class="meta-key">Setter</span><span class="meta-value">${escapeHtml(paper.setter_name || '—')}</span></div>
                <div><span class="meta-key">Exam</span><span class="meta-value">${formatDateTime(paper.exam_start_time)}</span></div>
                <div><span class="meta-key">Window</span><span class="meta-value">${timeLabel}</span></div>
                <div><span class="meta-key">Fingerprint</span><span class="meta-value mono">${escapeHtml((paper.file_sha256_short || 'pending') || 'pending')}</span></div>
            </div>
            ${actionHtml ? `<div class="ops-paper-actions">${actionHtml}</div>` : ''}
        </article>
    `;
}
