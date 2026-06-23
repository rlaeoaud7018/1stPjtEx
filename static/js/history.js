/**
 * 소방 관제 시스템 - 감지 이력 및 데이터 시각화 스크립트
 * [프론트엔드 B 담당]
 */

document.addEventListener("DOMContentLoaded", function () {
    
    // 이력 조회 및 지도 초기 가동
    initMap();
    fetchHistoryData();

    let map;
    function initMap() {
        // 서울시청 인근 기준 임시 좌표
        const centerLatLng = [37.5665, 126.9780];
        
        map = L.map('map').setView(centerLatLng, 16);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        const marker = L.marker(centerLatLng).addTo(map);
        marker.bindPopup("<b>소방 관제 드론 01호</b><br>동작 대기 중").openPopup();
    }

    function fetchHistoryData() {
        fetch("/dashboard/api/logs")
            .then(res => res.json())
            .then(data => {
                renderTable(data);
                renderChart(data);
            })
            .catch(err => console.error("Error fetching history:", err));
    }

    function renderTable(data) {
        const tbody = document.getElementById("history-tbody");
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = `<tr id="no-history-row"><td colspan="4" class="text-muted py-5">화재 감지 내역이 없습니다.</td></tr>`;
            return;
        }

        let html = "";
        data.forEach(log => {
            const badgeClass = log.type === "FIRE" ? "bg-danger" : "bg-secondary";
            html += `
                <tr>
                    <td>${log.time}</td>
                    <td><span class="badge ${badgeClass}">${log.type}</span></td>
                    <td class="text-warning fw-bold">${(log.confidence * 100).toFixed(0)}%</td>
                    <td>${log.message}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }

    let fireChart = null;
    function renderChart(data) {
        const ctx = document.getElementById('fire-trend-chart');
        if (!ctx) return;

        let fireCount = 0;
        let smokeCount = 0;

        data.forEach(log => {
            if (log.type === "FIRE") fireCount++;
            else if (log.type === "SMOKE") smokeCount++;
        });

        if (fireChart !== null) {
            fireChart.destroy();
        }

        fireChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['FIRE (불)', 'SMOKE (연기)'],
                datasets: [{
                    label: '감지 건수',
                    data: [fireCount, smokeCount],
                    backgroundColor: [
                        '#ff2d55',  // Neon Red
                        '#94a3b8'   // Slate Gray
                    ],
                    borderColor: '#0b0f19',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff',
                            font: {
                                family: 'Outfit'
                            }
                        }
                    }
                }
            }
        });
    }
});
