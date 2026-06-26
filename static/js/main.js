// main.js — 홈페이지 시계 & 공통 유틸

(function() {
  const days = ['일', '월', '화', '수', '목', '금', '토'];

  function padZ(n) { return String(n).padStart(2, '0'); }

  function updateClock() {
    const now  = new Date();
    const yy   = now.getFullYear();
    const mm   = padZ(now.getMonth() + 1);
    const dd   = padZ(now.getDate());
    const day  = days[now.getDay()];
    const hh   = padZ(now.getHours());
    const mi   = padZ(now.getMinutes());
    const ss   = padZ(now.getSeconds());

    const dateEl = document.getElementById('clock-date');
    const timeEl = document.getElementById('clock-time');
    if (dateEl) dateEl.textContent = `${yy}.${mm}.${dd} (${day})`;
    if (timeEl) timeEl.textContent = `${hh}:${mi}:${ss}`;
  }

  updateClock();
  setInterval(updateClock, 1000);
})();
