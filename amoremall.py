import os
import sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

BASE_URL = "https://www.amoremall.com"


def _find_and_fill(page, selectors, value, label):
    """여러 셀렉터를 순서대로 시도해서 첫 번째로 찾은 요소에 입력"""
    for sel in selectors:
        el = page.query_selector(sel)
        if el and el.is_visible():
            el.click()
            el.fill(value)
            return sel
    raise RuntimeError(
        f"{label} 입력 필드를 찾지 못했습니다.\n"
        f"  시도한 셀렉터: {selectors}\n"
        f"  현재 URL: {page.url}\n"
        f"  → amoremall.py 의 ID_SELECTORS / PW_SELECTORS 를 실제 사이트 셀렉터로 수정하세요."
    )


# 로그인 폼 셀렉터 후보 목록 (실제 사이트에 맞게 수정 가능)
ID_SELECTORS = [
    "#memId", "#loginId", "#userId", "#id", "#user_id",
    "input[name='memId']", "input[name='loginId']", "input[name='userId']",
    "input[name='id']", "input[name='user_id']",
    "input[type='text'][placeholder*='아이디']",
    "input[type='email'][placeholder*='이메일']",
]
PW_SELECTORS = [
    "#memPwd", "#loginPwd", "#password", "#passwd", "#pwd",
    "input[name='memPwd']", "input[name='loginPwd']",
    "input[name='password']", "input[name='passwd']",
    "input[type='password']",
]
LOGIN_BTN_SELECTORS = [
    "button[type='submit']", "input[type='submit']",
    ".btn-login", ".login-btn", ".btn_login",
    "button:has-text('로그인')", "a:has-text('로그인')",
]
LOGIN_URLS = [
    f"{BASE_URL}/member/loginForm.do",
    f"{BASE_URL}/member/login.do",
    f"{BASE_URL}/login",
]


def login(page, user_id, password):
    # 로그인 페이지 접속 (여러 URL 후보 시도)
    for url in LOGIN_URLS:
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")
        # 실제 로그인 폼이 있는 페이지인지 확인
        if page.query_selector("input[type='password']"):
            break

    # 팝업/레이어 닫기
    for close_sel in [".btn-close", ".popup-close", ".layer-close", "button.close"]:
        el = page.query_selector(close_sel)
        if el and el.is_visible():
            try:
                el.click()
                page.wait_for_timeout(300)
            except Exception:
                pass

    # 아이디 입력
    used_id_sel = _find_and_fill(page, ID_SELECTORS, user_id, "아이디")
    print(f"  아이디 필드: {used_id_sel}")

    # 비밀번호 입력
    used_pw_sel = _find_and_fill(page, PW_SELECTORS, password, "비밀번호")
    print(f"  비밀번호 필드: {used_pw_sel}")

    # 로그인 버튼 클릭
    for sel in LOGIN_BTN_SELECTORS:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            btn.click()
            print(f"  로그인 버튼: {sel}")
            break

    try:
        page.wait_for_navigation(wait_until="domcontentloaded", timeout=15000)
    except PlaywrightTimeoutError:
        pass

    error = page.query_selector(".login-error, .error-msg, .msg-error")
    if error and error.is_visible():
        text = error.inner_text()
        if any(k in text for k in ["아이디", "비밀번호", "오류", "실패"]):
            raise RuntimeError(f"로그인 실패: {text.strip()}")

    print("✅ 로그인 성공")


def add_to_cart(page, product_number):
    page.goto(f"{BASE_URL}/product/productView.do?prdtNo={product_number}")
    page.wait_for_load_state("domcontentloaded")

    print(f"📦 상품 페이지 접속: {page.title()}")

    # 옵션 선택 (사이즈, 색상 등)
    selects = page.query_selector_all("select.opt-select, select[name*='opt'], .option-select select")
    for sel in selects:
        options = sel.query_selector_all("option")
        for opt in options[1:]:
            value = opt.get_attribute("value") or ""
            text = opt.inner_text()
            if value and "선택" not in text and "품절" not in text:
                sel.select_option(value=value)
                page.wait_for_timeout(500)
                break

    # 장바구니 버튼 클릭
    cart_btn = page.query_selector(
        'button.btn-cart, a.btn-cart, .add-cart, button:has-text("장바구니"), a:has-text("장바구니 담기")'
    )
    if not cart_btn:
        raise RuntimeError("장바구니 버튼을 찾을 수 없습니다. 셀렉터를 확인하세요.")

    cart_btn.click()
    page.wait_for_timeout(1500)

    # 팝업 처리
    popup = page.query_selector(".layer-cart, .modal-cart, [class*='cartLayer'], [class*='alertPop']")
    if popup:
        go_cart = popup.query_selector('button:has-text("장바구니"), a:has-text("장바구니로 이동")')
        if go_cart:
            go_cart.click()
        else:
            close = popup.query_selector('.btn-close, button.close, [class*="close"]')
            if close:
                close.click()

    print(f"🛒 상품 {product_number} 장바구니 담기 완료")


def proceed_to_checkout(page):
    page.goto(f"{BASE_URL}/cart/cartView.do")
    page.wait_for_load_state("domcontentloaded")
    print("🛒 장바구니 페이지 이동")

    # 전체 선택
    all_check = page.query_selector('input[id*="allCheck"], input[class*="all-check"]')
    if all_check and not all_check.is_checked():
        all_check.click()

    # 구매하기 버튼
    order_btn = page.query_selector(
        'button:has-text("구매하기"), a:has-text("구매하기"), button:has-text("주문하기"), .btn-order'
    )
    if not order_btn:
        raise RuntimeError("구매하기 버튼을 찾을 수 없습니다.")

    order_btn.click()
    try:
        page.wait_for_navigation(wait_until="domcontentloaded", timeout=15000)
    except PlaywrightTimeoutError:
        pass

    print("💳 결제 페이지 이동")


def select_payment_and_pay(page, method="card"):
    page.wait_for_load_state("domcontentloaded")

    method_labels = {
        "card": ["신용카드", "신용/체크카드", "카드"],
        "naver_pay": ["네이버페이", "NAVER Pay"],
        "kakao_pay": ["카카오페이", "KakaoPay"],
    }
    labels = method_labels.get(method, method_labels["card"])

    for label in labels:
        btn = page.query_selector(f'label:has-text("{label}"), [class*="pay"]:has-text("{label}")')
        if btn:
            btn.click()
            print(f"💳 결제 수단 선택: {label}")
            break

    page.wait_for_timeout(1000)

    pay_btn = page.query_selector(
        'button:has-text("결제하기"), a:has-text("결제하기"), button:has-text("주문 완료"), .btn-pay'
    )
    if not pay_btn:
        raise RuntimeError("결제하기 버튼을 찾을 수 없습니다.")

    pay_btn.click()
    print("✅ 결제 요청 완료")
    page.wait_for_timeout(2000)


def main():
    user_id = os.getenv("AMOREMALL_ID", "").strip()
    password = os.getenv("AMOREMALL_PASSWORD", "").strip()
    payment_method = os.getenv("PAYMENT_METHOD", "card").strip()
    headless = os.getenv("HEADLESS", "false").lower() != "false"

    # 로그인 정보 확인
    if not user_id:
        user_id = input("아모레몰 아이디: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("비밀번호: ").strip()

    # 상품번호 입력 (CLI 인자 → 환경변수 → 직접 입력 순서)
    if len(sys.argv) > 1:
        product_numbers = [p.strip() for p in sys.argv[1:] if p.strip()]
    elif os.getenv("PRODUCT_NUMBERS"):
        product_numbers = [p.strip() for p in os.getenv("PRODUCT_NUMBERS").split(",") if p.strip()]
    else:
        raw = input("구매할 상품번호 입력 (여러 개는 쉼표로 구분): ").strip()
        product_numbers = [p.strip() for p in raw.split(",") if p.strip()]

    if not product_numbers:
        print("❌ 상품번호가 입력되지 않았습니다.")
        sys.exit(1)

    print()
    print("=" * 45)
    print("  아모레몰 결제 자동화 시작")
    print(f"  상품번호: {', '.join(product_numbers)}")
    print(f"  결제수단: {payment_method}")
    print("=" * 45)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=150)
        context = browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # 1. 로그인
            login(page, user_id, password)

            # 2. 장바구니 담기
            for pno in product_numbers:
                add_to_cart(page, pno)

            # 3. 결제 페이지 진입
            proceed_to_checkout(page)

            # 4. 결제 수단 선택 및 결제
            select_payment_and_pay(page, payment_method)

            # 결제 완료 대기
            print("⏳ 결제 처리 중... (최대 60초 대기)")
            try:
                page.wait_for_url("**/complete**", timeout=60000)
            except PlaywrightTimeoutError:
                print("ℹ️  결제 완료 페이지 자동 감지 실패 - 브라우저에서 직접 확인하세요.")

            page.screenshot(path="checkout-complete.png", full_page=True)
            print()
            print("✅ 결제 자동화 완료!")
            print("📸 스크린샷: checkout-complete.png")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            try:
                page.screenshot(path="error-screenshot.png", full_page=True)
                print("📸 오류 스크린샷: error-screenshot.png")
                # 현재 페이지 HTML 저장 (셀렉터 디버깅용)
                with open("error-page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("🔍 페이지 HTML: error-page.html (셀렉터 확인용)")
            except Exception:
                pass
            browser.close()
            sys.exit(1)

        browser.close()


if __name__ == "__main__":
    main()
