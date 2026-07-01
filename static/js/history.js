// history.js — 통계 분석 & 전체 로그 (개선판)

(function () {
  let currentPage = 1;
  let totalLogs   = 0;
  const PER_PAGE  = 10;
  let   fireChart    = null;
  let   barChart     = null;
  let   lineChart    = null;

  const DISTRICT_ORDER = ['동구', '중구', '서구', '유성구', '대덕구'];

  /* ── 현재 필터 값 ─────────────────────────────────────── */
  function getCurrentDroneFilter() {
    return document.getElementById('filter-drone')?.value || 'all';
  }
  function getCurrentTypeFilter() {
    return document.getElementById('filter-type')?.value || 'all';
  }

  /* ── 전체 로그를 한 번에 가져와서 차트에 활용 ─────────── */
  async function fetchAllLogsForChart() {
    try {
      const droneFilter = getCurrentDroneFilter();
      const typeFilter  = getCurrentTypeFilter();
      const params = new URLSearchParams({ district: droneFilter, type: typeFilter, page: 1, per: 9999 });
      const res  = await fetch(`/dashboard/api/logs?${params}`);
      const data = await res.json();
      return data.logs || [];
    } catch (e) {
      console.error('Chart data fetch error:', e);
      return [];
    }
  }

  /* ── 통계 + 차트 갱신 ─────────────────────────────────── */
  async function fetchStats() {
    const logs = await fetchAllLogsForChart();

    const fireCount  = logs.filter(l => l.type === '화재').length;
    const smokeCount = logs.filter(l => l.type === '연기').length;
    const total      = logs.length;

    /* 숫자 요약 갱신 */
    const totalEl = document.getElementById('stat-total');
    const fireEl  = document.getElementById('stat-fire');
    const smokeEl = document.getElementById('stat-smoke');
    if (totalEl) totalEl.textContent = total;
    if (fireEl)  fireEl.textContent  = fireCount;
    if (smokeEl) smokeEl.textContent = smokeCount;

    renderDonutChart(fireCount, smokeCount);
    renderBarChart(logs);
    renderLineChart(logs);
  }

  /* ── 도넛 차트: 유형별 비율 ───────────────────────────── */
  function renderDonutChart(fireCount, smokeCount) {
    const ctx = document.getElementById('fire-trend-chart');
    if (!ctx) return;
    if (fireChart) { fireChart.destroy(); fireChart = null; }

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
              color:    '#3a6080',
              font:     { family: 'Outfit', size: 11 },
              padding:  12,
              boxWidth: 12,
            }
          },
          tooltip: {
            backgroundColor: 'rgba(8,14,24,0.95)',
            titleColor:      '#dde4f0',
            bodyColor:       '#5a7090',
            borderColor:     'rgba(0,180,255,0.25)',
            borderWidth:     1,
          }
        }
      }
    });
  }

  /* ── 바 차트: 구별 감지 현황 ──────────────────────────── */
  function renderBarChart(logs) {
    const ctx = document.getElementById('district-bar-chart');
    if (!ctx) return;
    if (barChart) { barChart.destroy(); barChart = null; }

    /* 구별 집계 */
    const districtFire  = {};
    const districtSmoke = {};
    DISTRICT_ORDER.forEach(d => { districtFire[d] = 0; districtSmoke[d] = 0; });

    logs.forEach(log => {
      const district = (log.location || '').split(' ')[0];
      if (!DISTRICT_ORDER.includes(district)) return;
      if (log.type === '화재') districtFire[district]++;
      else                     districtSmoke[district]++;
    });

    barChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: DISTRICT_ORDER,
        datasets: [
          {
            label: '화재',
            data:  DISTRICT_ORDER.map(d => districtFire[d]),
            backgroundColor: 'rgba(220,20,20,0.7)',
            borderColor:     '#dc1414',
            borderWidth:     1,
            borderRadius:    3,
          },
          {
            label: '연기',
            data:  DISTRICT_ORDER.map(d => districtSmoke[d]),
            backgroundColor: 'rgba(90,112,144,0.55)',
            borderColor:     '#5a7090',
            borderWidth:     1,
            borderRadius:    3,
          }
        ]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#5a7090', font: { family: 'Outfit', size: 10 }, padding: 10, boxWidth: 10 }
          },
          tooltip: {
            backgroundColor: 'rgba(8,14,24,0.95)',
            titleColor: '#dde4f0', bodyColor: '#5a7090',
            borderColor: 'rgba(255,90,0,0.3)', borderWidth: 1,
          }
        },
        scales: {
          x: {
            stacked: false,
            ticks:  { color: '#5a7090', font: { family: 'Outfit', size: 10 } },
            grid:   { color: 'rgba(255,255,255,0.04)' },
          },
          y: {
            beginAtZero: true,
            ticks:  { color: '#5a7090', font: { family: 'Outfit', size: 10 }, stepSize: 1 },
            grid:   { color: 'rgba(255,255,255,0.06)' },
          }
        }
      }
    });
  }

  /* ── 라인 차트: 월별 감지 추이 ───────────────────────── */
  function renderLineChart(logs) {
    const ctx = document.getElementById('monthly-line-chart');
    if (!ctx) return;
    if (lineChart) { lineChart.destroy(); lineChart = null; }

    /* 월별 집계 */
    const monthlyFire  = {};
    const monthlySmoke = {};
    logs.forEach(log => {
      const m = (log.time || '').substring(0, 7); // "YYYY-MM"
      if (!m) return;
      if (log.type === '화재') monthlyFire[m]  = (monthlyFire[m]  || 0) + 1;
      else                     monthlySmoke[m] = (monthlySmoke[m] || 0) + 1;
    });

    const allMonths = [...new Set([...Object.keys(monthlyFire), ...Object.keys(monthlySmoke)])].sort();

    lineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: allMonths.length ? allMonths : ['데이터 없음'],
        datasets: [
          {
            label: '화재',
            data:  allMonths.map(m => monthlyFire[m] || 0),
            borderColor:     '#dc1414',
            backgroundColor: 'rgba(220,20,20,0.12)',
            pointBackgroundColor: '#dc1414',
            tension:   0.3,
            fill:      true,
            pointRadius: 4,
          },
          {
            label: '연기',
            data:  allMonths.map(m => monthlySmoke[m] || 0),
            borderColor:     '#5a7090',
            backgroundColor: 'rgba(90,112,144,0.1)',
            pointBackgroundColor: '#5a7090',
            tension:   0.3,
            fill:      true,
            pointRadius: 4,
          }
        ]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#5a7090', font: { family: 'Outfit', size: 10 }, padding: 10, boxWidth: 10 }
          },
          tooltip: {
            backgroundColor: 'rgba(8,14,24,0.95)',
            titleColor: '#dde4f0', bodyColor: '#5a7090',
            borderColor: 'rgba(255,90,0,0.3)', borderWidth: 1,
          }
        },
        scales: {
          x: {
            ticks: { color: '#5a7090', font: { family: 'Outfit', size: 10 } },
            grid:  { color: 'rgba(255,255,255,0.04)' },
          },
          y: {
            beginAtZero: true,
            ticks: { color: '#5a7090', font: { family: 'Outfit', size: 10 }, stepSize: 1 },
            grid:  { color: 'rgba(255,255,255,0.06)' },
          }
        }
      }
    });
  }

  /* ── 드론 ID 컬럼 표시/숨김 ───────────────────────────── */
  function updateDroneIdColumnVisibility() {
    const droneFilter = getCurrentDroneFilter();
    const isAll       = droneFilter === 'all';

    /* 헤더 th */
    const thDrone = document.querySelector('.col-drone-id');
    if (thDrone) thDrone.style.display = isAll ? '' : 'none';

    /* 바디 td (2번째 td: 드론 ID) */
    const rows = document.querySelectorAll('#history-log-tbody tr');
    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length >= 2) cells[1].style.display = isAll ? '' : 'none';
    });
  }

  /* ── 로그 목록 로드 ────────────────────────────────────── */
  window.fetchLogs = async function (page) {
    if (page) currentPage = page;
    const droneFilter = getCurrentDroneFilter();
    const typeFilter  = getCurrentTypeFilter();

    const params = new URLSearchParams({
      district: droneFilter,
      type:     typeFilter,
      page:     currentPage,
      per:      PER_PAGE,
    });

    try {
      const res  = await fetch(`/dashboard/api/logs?${params}`);
      const data = await res.json();
      totalLogs  = data.total;
      renderLogTable(data.logs);
      renderPagination(data.total, data.page);
      // 차트도 같이 갱신
      fetchStats();
    } catch (e) { console.error('Log fetch error:', e); }
  };

  function renderLogTable(logs) {
    const tbody = document.getElementById('history-log-tbody');
    if (!tbody) return;

    const droneFilter = getCurrentDroneFilter();
    const isAll       = droneFilter === 'all';
    const colspan     = isAll ? 7 : 6;

    if (!logs || logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:var(--text-muted);padding:30px;">조건에 맞는 로그가 없습니다.</td></tr>`;
      updateDroneIdColumnVisibility();
      return;
    }

    let html = '';
    const startNo = (currentPage - 1) * PER_PAGE + 1;
    logs.forEach((log, idx) => {
      const typeBadge = log.type === '화재'
        ? `<span class="badge badge-fire">${log.type}</span>`
        : `<span class="badge badge-smoke">${log.type}</span>`;

      /* 구별 현황(all)일 때만 드론 ID 셀 표시 */
      const droneCell = isAll
        ? `<td><span style="font-family:var(--font-en); font-weight:600;">${log.drone_id}</span></td>`
        : `<td style="display:none;"><span style="font-family:var(--font-en); font-weight:600;">${log.drone_id}</span></td>`;

      html += `<tr style="cursor:pointer;" onclick="goDetail(${log.id})">
        <td>${startNo + idx}</td>
        ${droneCell}
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
    updateDroneIdColumnVisibility();
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

  /* ── 초기화 ────────────────────────────────────────────── */
  fetchStats();
  fetchLogs(1);

})();
