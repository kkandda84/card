import os
import sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

BASE_URL = "https://www.amoremall.com"


SSO_LOGIN_DOMAIN = "one3-ap.amorepacific.com"

POPUP_CLOSE_SELECTORS = [
    # 닫기 버튼 일반
    "button.btn-close", "a.btn-close", ".btn_close",
    "button.close", "a.close",
    # 팝업/레이어 내부 닫기
    ".layer-popup button.close", ".layer-popup .btn-close",
    ".modal button.close", ".modal .btn-close",
    "[class*='popup'] button[class*='close']",
    "[class*='layer'] button[class*='close']",
    # 팝업 외부 딤 클릭
    ".dimmed", ".dim", ".overlay",
]


def close_popup(page):
    """로그인 후 레이어 팝업을 닫는다. 팝업이 없으면 조용히 넘어간다."""
    page.wait_for_timeout(1500)  # 팝업 렌더링 대기

    for sel in POPUP_CLOSE_SELECTORS:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                page.evaluate("el => el.click()", el)
                page.wait_for_timeout(800)
                print(f"  팝업 닫기: {sel}")
                # 팝업이 여러 개일 수 있으므로 한 번 더 확인
                for sel2 in POPUP_CLOSE_SELECTORS:
                    el2 = page.query_selector(sel2)
                    if el2 and el2.is_visible():
                        page.evaluate("el => el.click()", el2)
                        page.wait_for_timeout(500)
                return
        except Exception:
            continue


def login(page, user_id, password):
    # 메인 페이지 접속
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 우측 상단 로그인 버튼 → href를 직접 추출해서 이동 (뷰포트 밖 클릭 오류 방지)
    login_link = (
        page.query_selector("header a[href*='signin']")
        or page.query_selector("header a[href*='login']")
        or page.query_selector(".gnb a[href*='signin']")
        or page.query_selector(".gnb a[href*='login']")
        or page.query_selector("header a:has-text('로그인')")
        or page.query_selector("a[href*='signin']")
        or page.query_selector("a[href*='login']")
        or page.query_selector("a:has-text('로그인')")
    )
    if not login_link:
        raise RuntimeError("메인 페이지에서 로그인 버튼을 찾을 수 없습니다.")

    # href 추출 후 직접 이동 (뷰포트 밖 요소 클릭 오류 우회)
    href = login_link.get_attribute("href")
    if href:
        if href.startswith("http"):
            page.goto(href)
        else:
            page.goto(f"{BASE_URL}{href}")
    else:
        # href가 없으면 JS로 강제 클릭
        page.evaluate("el => el.click()", login_link)

    # SSO 페이지 로드 대기
    page.wait_for_url(f"**{SSO_LOGIN_DOMAIN}**", timeout=20000)
    page.wait_for_load_state("domcontentloaded")

    print(f"  SSO 로그인 페이지 접속: {page.url[:60]}...")

    # 아이디 입력
    page.wait_for_selector("#loginid", timeout=10000)
    page.fill("#loginid", user_id)

    # 비밀번호 입력 (#password-span 내부 input 우선, 없으면 span 자체)
    pw_input = (
        page.query_selector("#password-span input[type='password']")
        or page.query_selector("#password-span")
    )
    if not pw_input:
        raise RuntimeError("비밀번호 입력 필드(#password-span)를 찾을 수 없습니다.")
    pw_input.click()
    pw_input.fill(password)

    # 로그인 버튼 클릭
    page.click("#dologin")

    # 아모레몰로 복귀 대기
    page.wait_for_url(f"**amoremall.com**", timeout=20000)
    page.wait_for_load_state("domcontentloaded")

    # 로그인 실패 체크
    if SSO_LOGIN_DOMAIN in page.url:
        error = page.query_selector(".error, .alert, [class*='error']")
        msg = error.inner_text() if error else "아이디 또는 비밀번호를 확인하세요."
        raise RuntimeError(f"로그인 실패: {msg.strip()}")

    print("✅ 로그인 성공")
    close_popup(page)


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
