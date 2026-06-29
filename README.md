# 아모레몰 결제 자동화

아모레몰(www.amoremall.com) 로그인 → 상품 장바구니 담기 → 결제 자동화

## 빠른 시작 (Windows)

**`run.bat` 를 더블클릭**하면 됩니다.

- 최초 실행 시 패키지·브라우저를 자동 설치합니다 (Python 3.x 필요)
- 상품번호를 입력하면 자동으로 로그인 → 장바구니 → 결제까지 진행합니다

## 설정 (선택)

아이디·비밀번호를 매번 입력하기 싫으면 `.env` 파일을 만드세요:

```bash
cp .env.example .env
```

`.env` 파일:
```
AMOREMALL_ID=아이디
AMOREMALL_PASSWORD=비밀번호
PAYMENT_METHOD=card   # card / naver_pay / kakao_pay
HEADLESS=false        # false면 브라우저 창 표시
```

## Python 직접 실행

```bash
pip install -r requirements.txt
playwright install chromium

# 상품번호를 인자로 전달
python amoremall.py 1234567

# 여러 상품
python amoremall.py 1234567 2345678

# 인자 없이 실행하면 상품번호 입력 프롬프트 표시
python amoremall.py
```

## 주의사항

- 실제 결제까지 자동으로 진행됩니다. 신중하게 사용하세요.
- 사이트 구조 변경 시 `amoremall.py` 의 CSS 셀렉터를 수정해야 할 수 있습니다.
- 오류 발생 시 `error-screenshot.png` 를 확인하세요.

## 파일 구조

```
├── run.bat           # Windows 실행 파일 (더블클릭)
├── amoremall.py      # Python 자동화 스크립트
├── requirements.txt  # Python 패키지 목록
├── .env.example      # 환경변수 예시
└── (JS 버전)
    ├── playwright.config.js
    ├── scripts/checkout.js
    ├── tests/amoremall-checkout.spec.js
    └── utils/amoremall.js
```
