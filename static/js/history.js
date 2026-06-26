// history.js — 통계 분석 & 전체 로그

(function () {
  let currentPage = 1;
  let totalLogs   = 0;
  const PER_PAGE  = 10;
  let   fireChart = null;

  // ── 통계 로드 ────────────────────────────────────────────
  async function fetchStats() {
    try {
      const res  = await fetch('/dashboard/api/stats');
      const data = await res.json();
      const totalEl = document.getElementById('stat-total');
      const fireEl  = document.getElementById('stat-fire');
      const smokeEl = document.getElementById('stat-smoke');
      if (totalEl) totalEl.textContent = data.total;
      if (fireEl)  fireEl.textContent  = data.fire;
      if (smokeEl) smokeEl.textContent = data.smoke;
      renderChart(data.fire, data.smoke);
    } catch (e) { console.error('Stats error:', e); }
  }

  // ── 차트 렌더링 ──────────────────────────────────────────
  function renderChart(fireCount, smokeCount) {
    const ctx = document.getElementById('fire-trend-chart');
    if (!ctx) return;
    if (fireChart) { fireChart.destroy(); }

    fireChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['화재 (FIRE)', '연기 (SMOKE)'],
        datasets: [{
          data:            [fireCount, smokeCount],
          backgroundColor: ['rgba(220,20,20,0.75)', 'rgba(90,112,144,0.6)'],
          borderColor:     ['#dc1414', '#5a7090'],
          borderWidth:     2,
          hoverOffset:     8,
        }]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: true,
        cutout:              '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color:     '#5a7090',
              font:      { family: 'Outfit', size: 12 },
              padding:   16,
              boxWidth:  12,
            }
          },
          tooltip: {
            backgroundColor: 'rgba(8,14,24,0.95)',
            titleColor:      '#dde4f0',
            bodyColor:       '#5a7090',
            borderColor:     'rgba(255,90,0,0.3)',
            borderWidth:     1,
          }
        }
      }
    });
  }

  // ── 로그 목록 로드 ───────────────────────────────────────
  window.fetchLogs = async function (page) {
    if (page) currentPage = page;
    const droneFilter = document.getElementById('filter-drone')?.value || 'all';
    const typeFilter  = document.getElementById('filter-type')?.value  || 'all';

    const params = new URLSearchParams({
      drone: droneFilter,
      type:  typeFilter,
      page:  currentPage,
      per:   PER_PAGE,
    });

    try {
      const res  = await fetch(`/dashboard/api/logs?${params}`);
      const data = await res.json();
      totalLogs  = data.total;
      renderLogTable(data.logs);
      renderPagination(data.total, data.page);
    } catch (e) { console.error('Log fetch error:', e); }
  };

  function renderLogTable(logs) {
    const tbody = document.getElementById('history-log-tbody');
    if (!tbody) return;

    if (!logs || logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);padding:30px;">조건에 맞는 로그가 없습니다.</td></tr>';
      return;
    }

    let html = '';
    const startNo = (currentPage - 1) * PER_PAGE + 1;
    logs.forEach((log, idx) => {
      const typeBadge = log.type === '화재'
        ? `<span class="badge badge-fire">${log.type}</span>`
        : `<span class="badge badge-smoke">${log.type}</span>`;

      html += `<tr style="cursor:pointer;" onclick="goDetail(${log.id})">
        <td>${startNo + idx}</td>
        <td><span style="font-family:var(--font-en); font-weight:600;">${log.drone_id}</span></td>
        <td>${typeBadge}</td>
        <td style="color:var(--text-muted); font-size:0.76rem;">${log.location}</td>
        <td style="font-family:var(--font-en); font-size:0.76rem;">${log.time}</td>
        <td style="color:var(--orange-main); font-weight:600;">${(log.confidence * 100).toFixed(0)}%</td>
        <td>
          <a href="/dashboard/log_detail/${log.id}"
             class="btn btn-outline btn-sm"
             onclick="event.stopPropagation()">[보기]</a>
        </td>
      </tr>`;
    });
    tbody.innerHTML = html;
  }

  window.goDetail = function (logId) {
    window.location.href = `/dashboard/log_detail/${logId}`;
  };

  function renderPagination(total, page) {
    const bar = document.getElementById('pagination-bar');
    if (!bar) return;
    const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));
    let html = '';

    html += `<button class="page-btn arrow" ${page <= 1 ? 'disabled' : ''}
              onclick="fetchLogs(${page - 1})">‹</button>`;

    const start = Math.max(1, page - 2);
    const end   = Math.min(totalPages, page + 2);

    for (let p = start; p <= end; p++) {
      html += `<button class="page-btn ${p === page ? 'active' : ''}"
                onclick="fetchLogs(${p})">${p}</button>`;
    }

    html += `<button class="page-btn arrow" ${page >= totalPages ? 'disabled' : ''}
              onclick="fetchLogs(${page + 1})">›</button>`;

    bar.innerHTML = html;
  }

  // ── 초기화 ──────────────────────────────────────────────
  fetchStats();
  fetchLogs(1);

})();
