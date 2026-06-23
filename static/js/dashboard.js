/**
 * 소방 관제 시스템 - 실시간 모니터링 스크립트
 * pop_up.png 스타일 팝업 + send_alert SMS 연동
 */

/* ── 전역 상태 ── */
let isMuted    = true;
let alertShown = false;       // 팝업 이미 표시 중인지
let currentAlertData = null;  // 현재 경보 데이터

/* ── 초기화 ── */
document.addEventListener("DOMContentLoaded", function () {

    // 시계
    updateClock();
    setInterval(updateClock, 1000);

    // 폴링
    setInterval(fetchRealtimeLogs,  2000);
    setInterval(checkFireAlert,     2000);

    // 사운드 토글
    const soundBtn  = document.getElementById("btn-sound-toggle");
    const sirenAudio = document.getElementById("siren-audio");

    if (soundBtn) {
        soundBtn.addEventListener("click", function () {
            isMuted = !isMuted;
            if (isMuted) {
                soundBtn.textContent = "🔇 사운드";
                sirenAudio && sirenAudio.pause();
            } else {
                soundBtn.textContent = "🔊 경보중";
                soundBtn.style.color = "#ff6060";
                sirenAudio && sirenAudio.play().catch(() => {});
            }
        });
    }
});

/* ── 시계 ── */
function updateClock() {
    const el = document.getElementById("topbar-clock");
    if (!el) return;
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    el.textContent = `PM ${hh}:${mm}`;
}

/* ── 실시간 로그 ── */
function fetchRealtimeLogs() {
    fetch("/dashboard/api/logs")
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById("log-tbody");
            if (!tbody) return;

            const updateEl = document.getElementById("log-update-time");
            if (updateEl) {
                const now = new Date();
                updateEl.textContent = "갱신: " +
                    [now.getHours(), now.getMinutes(), now.getSeconds()]
                    .map(n => String(n).padStart(2, "0")).join(":");
            }

            if (!data || data.length === 0) {
                tbody.innerHTML = `<tr id="no-log-row"><td colspan="5" class="text-muted py-4">최근 감지 이력이 없습니다.</td></tr>`;
                return;
            }

            const LOCATION_MAP = {
                "DR-01": "강릉 옥계 산림 지역",
                "DR-02": "속초 설악 산림 지역",
                "DR-03": "장흑 개원 산림 지역",
                "DR-04": "평창 오대산 지역",
                "DR-05": "홍천 내촌 산림 지역"
            };

            let html = "";
            data.slice(0, 10).forEach(log => {
                const badgeClass = log.type === "FIRE" ? "bg-danger" : "bg-secondary";
                const droneId   = log.drone_id || "DR-01";
                const location  = LOCATION_MAP[droneId] || "미상 지역";
                const timePart  = (log.time || "").split(" ")[1] || log.time || "";
                html += `
                    <tr>
                        <td><span class="badge bg-secondary">${droneId}</span></td>
                        <td class="text-muted small">${timePart}</td>
                        <td><span class="badge ${badgeClass}">${log.type || "UNKNOWN"}</span></td>
                        <td class="text-warning fw-bold">${((log.confidence || 0) * 100).toFixed(0)}%</td>
                        <td class="text-light small">${location}</td>
                    </tr>`;
            });
            tbody.innerHTML = html;
        })
        .catch(err => console.error("Error loading logs:", err));
}

/* ── 화재 경보 체크 ── */
function checkFireAlert() {
    fetch("/dashboard/api/latest_alert")
        .then(r => r.json())
        .then(data => {
            const overlay    = document.getElementById("emergency-overlay");
            const sirenAudio = document.getElementById("siren-audio");

            if (data.alert) {
                // 화면 점멸 오버레이 ON
                overlay && overlay.classList.remove("d-none");

                // 사이렌
                if (!isMuted && sirenAudio && sirenAudio.paused) {
                    sirenAudio.play().catch(() => {});
                }

                // 팝업 (처음 감지되었을 때만 자동 표시)
                if (!alertShown) {
                    currentAlertData = {
                        drone_id:    data.drone_id    || "DR-??",
                        detect_time: data.detect_time || "--:--:--",
                        location:    data.location    || "미상 지역"
                    };
                    showFireModal(currentAlertData);
                }

                // 드론 카드 강조
                highlightDroneCard(data.drone_id);

            } else {
                overlay && overlay.classList.add("d-none");
                if (sirenAudio && !sirenAudio.paused) {
                    sirenAudio.pause();
                    sirenAudio.currentTime = 0;
                }
                // 경보 해제 시 팝업 상태 초기화 (다음 경보 대비)
                if (alertShown) {
                    closeFireModal();
                }
            }
        })
        .catch(err => console.error("Error reading alert API:", err));
}

/* ── 드론 카드 강조 ── */
function highlightDroneCard(droneId) {
    document.querySelectorAll(".drone-card").forEach(c => c.classList.remove("active-drone"));
    if (!droneId) return;
    const card = document.getElementById("drone-card-" + droneId);
    if (card) card.classList.add("active-drone");
}

/* ── 팝업 열기 ── */
function showFireModal(alertData) {
    alertShown = true;

    document.getElementById("popup-drone-id").textContent    = alertData.drone_id;
    document.getElementById("popup-detect-time").textContent = alertData.detect_time;
    document.getElementById("popup-location").textContent    = alertData.location;

    // SMS 결과 초기화
    const resultBox = document.getElementById("sms-result-box");
    if (resultBox) resultBox.classList.remove("show");
    const actionBtn = document.getElementById("btn-fire-action");
    if (actionBtn) { actionBtn.disabled = false; actionBtn.textContent = "대응 조치"; }

    const overlay = document.getElementById("fireAlertOverlay");
    overlay.classList.add("show");
}

/* ── 팝업 닫기 ── */
function closeFireModal() {
    alertShown = false;
    const overlay = document.getElementById("fireAlertOverlay");
    if (overlay) overlay.classList.remove("show");

    document.querySelectorAll(".drone-card").forEach(c => c.classList.remove("active-drone"));
}

/* ── 대응 조치 (SMS 발송 데모) ── */
function sendAlert() {
    if (!currentAlertData) return;

    const actionBtn = document.getElementById("btn-fire-action");
    if (actionBtn) { actionBtn.disabled = true; actionBtn.textContent = "발송 중..."; }

    fetch("/dashboard/api/send_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentAlertData)
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) {
            const resultBox  = document.getElementById("sms-result-box");
            const recipList  = document.getElementById("sms-recipients-list");
            const resultTitle = document.getElementById("sms-result-title");

            if (resultTitle) {
                resultTitle.innerHTML =
                    `📨 <strong>${res.sent_count}명</strong>에게 문자 발송 완료 (${res.sent_at})`;
            }

            if (recipList && res.recipients) {
                recipList.innerHTML = res.recipients
                    .map(r => `<li>▶ ${r.name} (${r.phone || '번호 미등록'})</li>`)
                    .join("");
            }

            if (resultBox) resultBox.classList.add("show");
            if (actionBtn) { actionBtn.textContent = "✔ 발송 완료"; }
        } else {
            alert("발송 중 오류가 발생했습니다.");
            if (actionBtn) { actionBtn.disabled = false; actionBtn.textContent = "대응 조치"; }
        }
    })
    .catch(err => {
        console.error("send_alert error:", err);
        alert("네트워크 오류가 발생했습니다.");
        if (actionBtn) { actionBtn.disabled = false; actionBtn.textContent = "대응 조치"; }
    });
}
