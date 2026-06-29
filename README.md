# 아모레몰 결제 자동화

아모레몰(www.amoremall.com) 로그인 → 상품 장바구니 담기 → 결제 자동화

## 설치

```bash
npm install
npx playwright install chromium
```

## 설정

```bash
cp .env.example .env
# .env 파일에 로그인 정보와 상품번호 입력
```

`.env` 파일:
```
AMOREMALL_ID=아이디
AMOREMALL_PASSWORD=비밀번호
PRODUCT_NUMBERS=1234567
PAYMENT_METHOD=card
HEADLESS=false
```

## 실행 방법

### 방법 1: 스크립트 직접 실행 (권장)

```bash
# 상품번호를 인자로 전달
node scripts/checkout.js 1234567

# 여러 상품
node scripts/checkout.js 1234567 2345678

# 결제수단 지정
PAYMENT_METHOD=kakao_pay node scripts/checkout.js 1234567
```

### 방법 2: Playwright 테스트 실행

```bash
# 전체 테스트 (headless)
npm test

# 브라우저 창 표시
npm run test:headed

# 디버그 모드
npm run test:debug

# 특정 테스트만 실행
npx playwright test --grep "전체 플로우"
```

## 주의사항

- `selectPaymentAndPay()` 함수는 **실제 결제**를 진행합니다.
- 테스트 시 `tests/amoremall-checkout.spec.js` 에서 해당 줄이 주석 처리되어 있습니다.
- 실제 결제를 원하면 `scripts/checkout.js` 를 사용하거나 주석을 해제하세요.
- 사이트 구조 변경 시 `utils/amoremall.js` 의 셀렉터를 수정해야 할 수 있습니다.

## 파일 구조

```
├── .env.example          # 환경변수 예시
├── playwright.config.js  # Playwright 설정
├── scripts/
│   └── checkout.js       # 단독 실행 스크립트
├── tests/
│   └── amoremall-checkout.spec.js  # Playwright 테스트
└── utils/
    └── amoremall.js      # 공통 헬퍼 함수 (로그인, 장바구니, 결제)
```
