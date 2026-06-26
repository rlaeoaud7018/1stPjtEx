// dashboard.js — 실시간 관제 화면

(function () {
  const POLL_MS     = 2000;   // 폴링 주기 (2초)
  const ALERT_COOLDOWN_MS = 30000; // 경보 반복 방지 (30초)

  const days = ['일', '월', '화', '수', '목', '금', '토'];
  let   lastAlertId   = null;
  let   alertCooldown = false;
  let   sirenPlaying  = false;

  // ── 시계 ────────────────────────────────────────────────
  function padZ(n) { return String(n).padStart(2, '0'); }

  function updateClock() {
    const now   = new Date();
    const dateEl = document.getElementById('mon-date');
    const timeEl = document.getElementById('mon-time');
    if (!dateEl || !timeEl) return;

    const dateStr = `${now.getFullYear()}.${padZ(now.getMonth()+1)}.${padZ(now.getDate())}`;
    const timeStr = `${padZ(now.getHours())}:${padZ(now.getMinutes())}`;
    const ampm    = now.getHours() < 12 ? 'AM' : 'PM';
    dateEl.textContent = dateStr;
    timeEl.textContent = `${timeStr} ${ampm}`;
  }

  // ── 사이렌 ──────────────────────────────────────────────
  function playSiren() {
    const audio = document.getElementById('siren-audio');
    if (!audio || sirenPlaying) return;
    audio.play().then(() => { sirenPlaying = true; }).catch(() => {});
  }

  function stopSiren() {
    const audio = document.getElementById('siren-audio');
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    sirenPlaying = false;
  }

  // ── 화재 경보 모달 ───────────────────────────────────────
  function showFireModal(log) {
    document.getElementById('alert-drone').textContent      = log.drone_id || '-';
    document.getElementById('alert-location').textContent   = log.location || '-';
    document.getElementById('alert-time').textContent       = log.time || '-';
    document.getElementById('alert-confidence').textContent = log.confidence ? `${(log.confidence * 100).toFixed(0)}%` : '-';

    document.getElementById('fire-modal-overlay').classList.remove('hidden');
    document.getElementById('screen-danger-border').classList.add('active');
    playSiren();
  }

  window.closeFireModal = function () {
    document.getElementById('fire-modal-overlay').classList.add('hidden');
    document.getElementById('screen-danger-border').classList.remove('active');
    stopSiren();
    // 쿨다운
    alertCooldown = true;
    setTimeout(() => { alertCooldown = false; }, ALERT_COOLDOWN_MS);
  };

  window.startResponse = function () {
    closeFireModal();
    alert('대응을 시작합니다. 관할 소방서에 연락하세요.');
  };

  // ── 최신 경보 폴링 ──────────────────────────────────────
  async function pollLatestAlert() {
    if (alertCooldown) return;
    try {
      const res  = await fetch('/dashboard/api/latest_alert');
      const data = await res.json();
      if (data.alert && data.log) {
        const logId = data.log.id;
        if (logId !== lastAlertId) {
          lastAlertId = logId;
          showFireModal(data.log);
        }
      }
    } catch (e) { /* 연결 불안정 무시 */ }
  }

  // ── 최근 로그 폴링 ──────────────────────────────────────
  async function pollRecentLogs() {
    try {
      const res   = await fetch('/dashboard/api/recent_logs');
      const logs  = await res.json();
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
      const typeBadge = log.type === '화재'
        ? `<span class="badge badge-fire">${log.type}</span>`
        : `<span class="badge badge-smoke">${log.type}</span>`;
      const statusBadge = log.status === '대응중'
        ? `<span class="badge badge-active">${log.status}</span>`
        : `<span class="badge badge-ok">${log.status}</span>`;

      html += `<tr>
        <td>${idx + 1}</td>
        <td><span style="font-family:var(--font-en); font-weight:600;">${log.drone_id}</span></td>
        <td>${typeBadge}</td>
        <td style="color:var(--text-muted); font-size:0.74rem;">${log.location}</td>
        <td style="font-family:var(--font-en); font-size:0.74rem;">${log.time}</td>
        <td>${statusBadge}</td>
      </tr>`;
    });
    tbody.innerHTML = html;
  }

  // ── 초기화 ──────────────────────────────────────────────
  updateClock();
  setInterval(updateClock, 1000);
  pollRecentLogs();
  pollLatestAlert();
  setInterval(pollRecentLogs,    POLL_MS);
  setInterval(pollLatestAlert,   POLL_MS);

})();
