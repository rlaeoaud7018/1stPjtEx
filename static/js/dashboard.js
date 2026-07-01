// dashboard.js — 실시간 관제 화면

(function () {
  const POLL_MS = 2000;

  // ── 확인 이력 (localStorage 기반, 새로고침 후에도 유지) ─
  const LS_KEY = 'dronefire_confirmed_v1';
  const confirmedLogs = (function () {
    try { return new Set(JSON.parse(localStorage.getItem(LS_KEY) || '[]')); }
    catch { return new Set(); }
  })();

  function persistConfirm(rowKey) {
    confirmedLogs.add(rowKey);
    try { localStorage.setItem(LS_KEY, JSON.stringify([...confirmedLogs])); } catch { }
  }

  // ── 시계 ────────────────────────────────────────────────
  function padZ(n) { return String(n).padStart(2, '0'); }

  function updateClock() {
    const now = new Date();
    const dateEl = document.getElementById('mon-date');
    const timeEl = document.getElementById('mon-time');
    if (!dateEl || !timeEl) return;
    const ampm = now.getHours() < 12 ? 'AM' : 'PM';
    dateEl.textContent = `${now.getFullYear()}.${padZ(now.getMonth() + 1)}.${padZ(now.getDate())}`;
    timeEl.textContent = `${padZ(now.getHours())}:${padZ(now.getMinutes())} ${ampm}`;
  }

  // ── 최근 로그 폴링 ──────────────────────────────────────
  async function pollRecentLogs() {
    try {
      const res = await fetch('/dashboard/api/recent_logs');
      const logs = await res.json();
      renderRecentLogs(logs);
    } catch (e) { /* ignore */ }
  }

  function renderRecentLogs(logs) {
    const tbody = document.getElementById('recent-log-tbody');
    if (!tbody) return;

    if (!logs || logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:20px;">로그 없음</td></tr>';
      return;
    }

    let html = '';
    logs.forEach((log, idx) => {
      const rowKey = `${log.drone_id}_${log.time}`;
      const typeBadge = log.type === '화재'
        ? `<span class="badge badge-fire">${log.type}</span>`
        : `<span class="badge badge-smoke">${log.type}</span>`;

      const isConfirmed = confirmedLogs.has(rowKey);
      const sirenCell = `<button class="siren-btn${isConfirmed ? ' confirmed' : ''}" onclick="openSirenModal(this)" data-row-key="${rowKey}" data-drone-id="${log.drone_id || ''}" data-location="${(log.location || '').replace(/"/g, '&quot;')}" data-log-time="${log.time || ''}" data-type="${log.type || ''}" title="${isConfirmed ? '재확인' : '클릭하여 로그 확인'}">🚨</button>`;

      html += `<tr>
        <td>${idx + 1}</td>
        <td><span style="font-family:var(--font-en);font-weight:600;">${log.drone_id}</span></td>
        <td>${typeBadge}</td>
        <td style="color:var(--text-muted);font-size:0.74rem;">${log.location}</td>
        <td style="font-family:var(--font-en);font-size:0.74rem;">${log.time}</td>
        <td>${sirenCell}</td>
      </tr>`;
    });
    tbody.innerHTML = html;
  }

  // ── 사이렌 버튼 클릭 핸들러 ─────────────────────────────
  // confirmed 상태여도 팝업은 열림 (점멸만 안 할 뿐)
  window.openSirenModal = function (btn) {
    if (!btn) return;
    const d = btn.dataset;
    openLogModal(d.rowKey, d.droneId, d.location, d.logTime, d.type);
  };

  // ── 로그 상세 팝업 열기 ──────────────────────────────────
function openLogModal(rowKey, droneId, location, time, type) {

    const overlay = document.getElementById('log-modal-overlay');
    if (!overlay) return;

    const alertText = document.getElementById('log-modal-alert-text');
    if (alertText) {
        alertText.textContent =
            (type === '연기') ? '연기가 감지되었습니다!' : '산불이 감지되었습니다!';
    }

    document.getElementById('log-modal-drone-id').textContent = droneId || '-';
    document.getElementById('log-modal-type').textContent = type || '-';
    document.getElementById('log-modal-location').textContent = location || '-';
    document.getElementById('log-modal-time').textContent = time || '-';

    const droneMap = {
        "DRONE_01": 1,
        "DRONE_02": 2,
        "DRONE_03": 3,
        "DRONE_04": 4
    };

    const num = droneMap[droneId];

    const img = document.getElementById('log-modal-feed-img');
    if (img && num) {
        img.src = `/dashboard/video_feed/${num}?t=${Date.now()}`;
    }

    overlay.dataset.rowKey = rowKey || '';
    overlay.dataset.droneId = droneId || '';
    overlay.dataset.location = location || '';
    overlay.dataset.fireTime = time || '';
    overlay.dataset.fireType = type || '';

    overlay.classList.remove('hidden');
}

  // ── 로그 팝업 — 확인 ────────────────────────────────────
  window.confirmLogModal = function () {
    const overlay = document.getElementById('log-modal-overlay');
    if (!overlay) return;
    const od = overlay.dataset;
    if (od.rowKey) {
      persistConfirm(od.rowKey);
      const btn = document.querySelector(`[data-row-key="${od.rowKey}"]`);
      if (btn) { btn.classList.add('confirmed'); btn.title = '재확인'; }
    }
    fetch('/dashboard/api/confirm_log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action:    '확인',
        drone_id:  od.droneId,
        location:  od.location,
        fire_time: od.fireTime,
        fire_type: od.fireType,
      }),
    }).catch(() => {});
    overlay.classList.add('hidden');
    const img = document.getElementById('log-modal-feed-img');
    if (img) img.src = '';
  };

  // ── 로그 팝업 — 알림 발송 ───────────────────────────────
window.sendAlertModal = function () {
    const overlay = document.getElementById('log-modal-overlay');
    if (!overlay) return;

    const od = overlay.dataset;

    if (od.rowKey) {
        persistConfirm(od.rowKey);

        const btn = document.querySelector(`[data-row-key="${od.rowKey}"]`);
        if (btn) {
            btn.classList.add('confirmed');
            btn.title = '재확인';
        }
    }
    fetch('/dashboard/api/confirm_log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            log_id: od.rowKey,
            action: '알림발송',
            drone_id: od.droneId,
            location: od.location,
            fire_time: od.fireTime,
            fire_type: od.fireType,
        }),
    }).catch(() => {});
    fetch('/dashboard/api/send_discord', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            log_id: od.rowKey
        }),
    }).catch(() => {});

    overlay.classList.add('hidden');

    const img = document.getElementById('log-modal-feed-img');
    if (img) img.src = '';

    alert('알림이 발송되었습니다.');
};

  // ── 초기화 ──────────────────────────────────────────────
  updateClock();
  setInterval(updateClock, 1000);
  pollRecentLogs();
  setInterval(pollRecentLogs, POLL_MS);

})();
