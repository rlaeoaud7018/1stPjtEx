# Bootstrap란 무엇인가? — 5살도 이해하는 설명

> 작성일: 2026-06-29  
> 작성 이유: 1차 프로젝트에서 Bootstrap을 사용한 버전(원본 `1stProject/`)이 있었고,
> 현재 작업 버전(`1차 프로젝트 테스트용/1stProject/`)은 Bootstrap 없이 순수 CSS로 동일한
> 효과를 구현했다. 두 방식의 차이를 이해하기 위해 작성함.

---

## 🧒 5살 아이도 이해하는 설명

### Bootstrap = 미리 만들어진 레고 키트

보통 레고를 할 때 처음부터 모든 부품을 직접 만들어야 한다면 엄청 오래 걸려.
Bootstrap은 "많이 쓰는 부품들을 미리 만들어 놓은 레고 키트"야.

버튼, 표, 네비바, 카드... 이런 흔한 것들을
Bootstrap 키트에서 꺼내 쓰기만 하면 돼.

---

## 📦 Bootstrap이 실제로 하는 일

### 1. 클래스 이름만 써도 예쁘게 만들어 줌

우리가 배운 방법:
```css
/* 내가 직접 CSS에 버튼을 꾸밈 */
.my-button {
    background-color: red;
    padding: 10px 20px;
    border-radius: 5px;
    color: white;
}
```
```html
<button class="my-button">클릭</button>
```

Bootstrap을 쓰는 방법:
```html
<!-- Bootstrap이 이미 만들어 둔 빨간 버튼 클래스를 그냥 가져다 씀 -->
<button class="btn btn-danger">클릭</button>
```

CSS 파일에 아무것도 안 써도, Bootstrap 파일 하나를 불러오면
`btn`, `btn-danger` 같은 클래스가 이미 꾸며진 채로 동작해.

---

### 2. Bootstrap에서 자주 보이는 클래스들

원본 프로젝트에서 보였던 것들:

| Bootstrap 클래스 | 하는 일 |
|----------------|---------|
| `btn btn-danger` | 빨간 버튼 |
| `btn btn-outline-light` | 테두리만 있는 밝은 버튼 |
| `container` | 가운데 정렬된 최대 너비 컨테이너 |
| `row`, `col-lg-6` | 12칸 그리드 레이아웃 |
| `d-flex` | `display: flex` 와 동일 |
| `justify-content-center` | 가운데 정렬 (flex) |
| `text-danger` | 빨간 글자색 |
| `bg-dark` | 어두운 배경색 |
| `fw-bold` | 굵은 글씨 |
| `py-5` | 위아래 padding 5단계 |
| `mb-4` | 아래 margin 4단계 |
| `card`, `card-glass` | 카드 박스 UI |
| `navbar`, `nav-link` | 네비게이션 바 |
| `table table-dark` | 다크 테마 테이블 |
| `badge bg-success` | 초록 뱃지 |
| `collapse` | 접었다 펼치는 기능 |

---

## 🔍 Bootstrap vs 순수 CSS — 핵심 차이

### Bootstrap 방식 (원본 `1stProject/`)
```html
<!-- HTML 파일 상단에 Bootstrap CDN 연결 (인터넷에서 가져옴) -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- 사용할 때는 미리 만들어진 클래스 이름만 씀 -->
<button class="btn btn-danger w-100 fw-bold">로그인</button>
<div class="card card-glass p-4">...</div>
```

### 순수 CSS 방식 (현재 작업 버전)
```html
<!-- CSS 파일 하나만 연결 (내 컴퓨터 파일) -->
<link rel="stylesheet" href="/static/css/style.css">

<!-- 사용할 때도 내가 직접 만든 클래스 이름을 씀 -->
<button class="btn btn-danger">로그인</button>
<div class="auth-card">...</div>
```
```css
/* style.css 안에 내가 직접 정의함 */
.btn-danger {
  background: var(--red-vivid);
  color: #fff;
}
.auth-card {
  background: rgba(10, 16, 28, 0.97);
  border-radius: 16px;
  padding: 48px 40px;
}
```

---

## ⚖️ 어느 게 더 좋아?

| 항목 | Bootstrap | 순수 CSS |
|------|-----------|---------|
| 개발 속도 | 빠름 (미리 만들어짐) | 느림 (직접 만들어야 함) |
| 인터넷 필요 | CDN 방식이면 필요 | 필요 없음 (로컬 파일) |
| 커스터마이징 | 제한적 (Bootstrap 규칙 따름) | 자유롭게 가능 |
| 파일 크기 | 큼 (Bootstrap 전체) | 작음 (필요한 것만) |
| 배움의 가치 | "레고 키트 사용법" 배움 | "CSS 원리" 직접 배움 |
| 현재 프로젝트 | ❌ 사용 안 함 | ✅ 사용 중 |

---

## 🔧 현재 프로젝트에서 Bootstrap 대신 직접 구현한 것들

`static/css/style.css` 파일 안에 Bootstrap이 제공했던 것들을 직접 만들어 뒀음:

```css
/* Bootstrap의 .btn, .btn-primary 대신 → 직접 만든 것 */
.btn { display: inline-flex; align-items: center; ... }
.btn-primary { background: var(--orange-main); ... }
.btn-secondary { background: rgba(255,255,255,0.06); ... }
.btn-danger { background: var(--red-vivid); ... }
.btn-outline { border: 1px solid var(--border-accent); ... }
.btn-sm { padding: 6px 14px; ... }
.btn-lg { padding: 13px 32px; ... }
```

이렇게 Bootstrap의 클래스 이름 규칙을 참고해서 직접 CSS를 짰기 때문에,
HTML 파일에서 `class="btn btn-danger"` 처럼 쓰면 여전히 동작함.
단, Bootstrap 라이브러리 없이도!

---

## 📌 결론 — 왜 우리 프로젝트는 Bootstrap을 안 쓰는가?

1. **인터넷 의존 없이 실행** — Bootstrap CDN이 없어도 로컬에서 완전히 작동
2. **우리 디자인에 맞게 자유롭게** — 소방 관제 시스템만의 색상, 크기, 애니메이션
3. **CSS 학습 효과** — Bootstrap이 "완성된 답지"라면, 순수 CSS는 "직접 풀기"
4. **파일 크기 최적화** — Bootstrap 전체(140KB+) 대신 우리에게 필요한 것만

Bootstrap은 나쁜 게 아니고, 실제 회사에서도 많이 씀.
다만 배우는 입장에서는 순수 CSS를 먼저 이해하는 게 기초가 더 탄탄해짐!
