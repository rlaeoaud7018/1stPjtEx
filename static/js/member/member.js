let otpTimer = null;
let timeLeft = 0;
let isOtpVerified = false;

function getInputs() {
    return {
        idInput: document.querySelector('input[name="mId"]'),
        nameInput: document.querySelector('input[name="mName"]'),
        emailInput: document.querySelector('input[name="mMail"]'),
        otpInput: document.querySelector('input[name="otp"]')
    };
}

function sendOtp() {
    const { idInput, nameInput, emailInput } = getInputs();

    const nameValue = nameInput ? nameInput.value.trim() : "";
    const emailValue = emailInput ? emailInput.value.trim() : "";

    if (idInput) {
        const idValue = idInput.value.trim();
        if (!idValue) { alert("아이디를 입력해주세요!"); idInput.focus(); return; }
    }

    if (!nameValue) { alert("성함을 입력해주세요!"); nameInput?.focus(); return; }
    if (!emailValue) { alert("이메일을 입력해주세요!"); emailInput?.focus(); return; }

    const formData = new FormData();
    if (idInput) {
        formData.append('mId', idInput.value.trim());
    }
    formData.append('mName', nameValue);
    formData.append('mMail', emailValue);

    fetch('/member/send_verification', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert(data.message || "인증번호가 발송되었습니다.");

            if (otpTimer) clearInterval(otpTimer);

            timeLeft = 180;
            const timerBox = document.querySelector('#timer');
            updateTimerDisplay(timerBox, timeLeft);

            otpTimer = setInterval(() => {
                timeLeft -= 1;
                if (timeLeft >= 0) {
                    updateTimerDisplay(timerBox, timeLeft);
                } else {
                    clearInterval(otpTimer);
                    if (timerBox) timerBox.innerText = "시간 만료";
                    alert("인증 시간이 만료되었습니다. 다시 시도해주세요.");
                }
            }, 1000);

        } else {
            alert("발송 실패: " + (data.message || "오류가 발생했습니다."));
        }
    })
    .catch(error => {
        console.error("에러 발생:", error);
        alert("서버 통신 중 오류가 발생했습니다.");
    });
}

function checkOtp() {
    const { idInput, nameInput, emailInput, otpInput } = getInputs();

    const otp = otpInput ? otpInput.value.trim() : "";
    const email = emailInput ? emailInput.value.trim() : "";

    if (!otp) { alert("인증번호를 입력해주세요!"); otpInput?.focus(); return; }
    if (timeLeft <= 0) { alert("인증 시간이 만료되었습니다. 다시 발송해주세요."); return; }

    const formData = new FormData();
    formData.append('otp', otp);
    formData.append('mMail', email);

    fetch('/member/verify_otp', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert("인증에 성공했습니다!");
            isOtpVerified = true;

            if (otpTimer) clearInterval(otpTimer);

            const timerBox = document.querySelector('#timer');
            if (timerBox) timerBox.innerText = "인증 완료";

            if (idInput) idInput.readOnly = true;
            if (nameInput) nameInput.readOnly = true;
            if (emailInput) emailInput.readOnly = true;
            if (otpInput) otpInput.readOnly = true;

        } else {
            alert("인증 실패: " + data.message);
        }
    })
    .catch(error => {
        console.error("에러 발생:", error);
        alert("서버 통신 중 오류가 발생했습니다.");
    });
}

function goFindId() {
    if (!isOtpVerified) {
        alert("이메일 인증을 먼저 완료해주세요.");
        return;
    }
    const form = document.querySelector('form[name="id_find_form"]');
    if (form) form.submit();
}

function goFindPw() {
    if (!isOtpVerified) {
        alert("이메일 인증을 먼저 완료해주세요.");
        return;
    }
    const form = document.querySelector('form[name="pw_find_form"]');
    if (form) form.submit();
}

function updateTimerDisplay(element, totalSeconds) {
    if (!element) return;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    element.innerText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}
