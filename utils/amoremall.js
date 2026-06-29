/**
 * 아모레몰 자동화 공통 헬퍼 함수
 */

const BASE_URL = 'https://www.amoremall.com';

/**
 * 아모레몰 로그인
 */
async function login(page, id, password) {
  await page.goto(`${BASE_URL}/member/loginForm.do`);
  await page.waitForLoadState('domcontentloaded');

  // 로그인 폼 입력
  await page.fill('#memId', id);
  await page.fill('#memPwd', password);
  await page.click('button[type="submit"], .btn-login, input[type="submit"]');

  // 로그인 완료 대기 (메인 페이지 또는 마이페이지로 이동)
  await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 });

  // 로그인 실패 체크
  const errorMsg = await page.$('.login-error, .error-msg, .alert');
  if (errorMsg) {
    const text = await errorMsg.textContent();
    if (text && (text.includes('아이디') || text.includes('비밀번호') || text.includes('오류'))) {
      throw new Error(`로그인 실패: ${text.trim()}`);
    }
  }

  console.log('✅ 로그인 성공');
}

/**
 * 상품 페이지로 이동
 */
async function navigateToProduct(page, productNumber) {
  // 아모레몰 상품 URL 패턴
  const productUrl = `${BASE_URL}/product/productView.do?prdtNo=${productNumber}`;
  await page.goto(productUrl);
  await page.waitForLoadState('domcontentloaded');

  // 상품 존재 여부 확인
  const notFound = await page.$('.no-product, .sold-out-page, [class*="notFound"]');
  if (notFound) {
    throw new Error(`상품번호 ${productNumber}를 찾을 수 없습니다.`);
  }

  const title = await page.title();
  console.log(`📦 상품 페이지 접속: ${title}`);
}

/**
 * 장바구니 담기
 */
async function addToCart(page, productNumber) {
  await navigateToProduct(page, productNumber);

  // 옵션이 있는 경우 첫 번째 옵션 선택 (사이즈, 색상 등)
  const optionSelects = await page.$$('select.opt-select, select[name*="opt"], .option-select select');
  for (const select of optionSelects) {
    const options = await select.$$('option');
    // 첫 번째 유효 옵션 선택 (기본 안내 문구 제외)
    for (let i = 1; i < options.length; i++) {
      const value = await options[i].getAttribute('value');
      const text = await options[i].textContent();
      if (value && value !== '' && !text.includes('선택') && !text.includes('품절')) {
        await select.selectOption({ index: i });
        await page.waitForTimeout(500);
        break;
      }
    }
  }

  // 장바구니 버튼 클릭
  const cartBtn = await page.$(
    'button.btn-cart, a.btn-cart, .add-cart, [class*="cart"][class*="btn"], button:has-text("장바구니"), a:has-text("장바구니 담기")'
  );
  if (!cartBtn) {
    throw new Error('장바구니 버튼을 찾을 수 없습니다. 셀렉터를 확인하세요.');
  }

  await cartBtn.click();
  await page.waitForTimeout(1500);

  // 팝업/레이어 처리 (장바구니 담기 완료 팝업)
  const popup = await page.$('.layer-cart, .modal-cart, [class*="cartLayer"], [class*="alertPop"]');
  if (popup) {
    // "장바구니 이동" 또는 "계속 쇼핑" 버튼 처리
    const goCartBtn = await popup.$('button:has-text("장바구니"), a:has-text("장바구니로 이동")');
    if (goCartBtn) {
      await goCartBtn.click();
    } else {
      // 팝업 닫기
      const closeBtn = await popup.$('.btn-close, button.close, [class*="close"]');
      if (closeBtn) await closeBtn.click();
    }
  }

  console.log(`🛒 상품 ${productNumber} 장바구니 담기 완료`);
}

/**
 * 장바구니 페이지로 이동
 */
async function goToCart(page) {
  await page.goto(`${BASE_URL}/cart/cartView.do`);
  await page.waitForLoadState('domcontentloaded');
  console.log('🛒 장바구니 페이지 이동');
}

/**
 * 결제 진행
 */
async function proceedToCheckout(page) {
  await goToCart(page);

  // 전체 상품 선택 확인
  const allCheck = await page.$('input[id*="allCheck"], input[class*="all-check"]');
  if (allCheck) {
    const checked = await allCheck.isChecked();
    if (!checked) await allCheck.click();
  }

  // 구매하기 버튼 클릭
  const orderBtn = await page.$(
    'button:has-text("구매하기"), a:has-text("구매하기"), button:has-text("주문하기"), .btn-order'
  );
  if (!orderBtn) {
    throw new Error('구매하기 버튼을 찾을 수 없습니다.');
  }

  await orderBtn.click();
  await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 });
  console.log('💳 결제 페이지 이동');
}

/**
 * 결제 수단 선택 및 결제
 * @param {string} method - 'card' | 'naver_pay' | 'kakao_pay'
 */
async function selectPaymentAndPay(page, method = 'card') {
  await page.waitForLoadState('domcontentloaded');

  const methodMap = {
    card: ['신용카드', '신용/체크카드', '카드'],
    naver_pay: ['네이버페이', 'NAVER Pay'],
    kakao_pay: ['카카오페이', 'KakaoPay'],
  };

  const labels = methodMap[method] || methodMap['card'];

  // 결제 수단 선택
  for (const label of labels) {
    const payOption = await page.$(`label:has-text("${label}"), input[title="${label}"] + label, [class*="pay"]:has-text("${label}")`);
    if (payOption) {
      await payOption.click();
      console.log(`💳 결제 수단 선택: ${label}`);
      break;
    }
  }

  await page.waitForTimeout(1000);

  // 결제하기 버튼 클릭
  const payBtn = await page.$(
    'button:has-text("결제하기"), a:has-text("결제하기"), button:has-text("주문 완료"), .btn-pay'
  );
  if (!payBtn) {
    throw new Error('결제하기 버튼을 찾을 수 없습니다.');
  }

  await payBtn.click();
  console.log('✅ 결제 요청 완료 - 결제 팝업 또는 페이지로 이동합니다.');

  // 결제 팝업 대기 (PG사 페이지)
  await page.waitForTimeout(2000);
}

module.exports = { login, navigateToProduct, addToCart, goToCart, proceedToCheckout, selectPaymentAndPay };
