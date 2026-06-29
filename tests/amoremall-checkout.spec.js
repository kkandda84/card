/**
 * 아모레몰 자동화 테스트
 * - 로그인 → 상품 장바구니 담기 → 결제
 *
 * 실행 방법:
 *   PRODUCT_NUMBERS=1234567 npx playwright test
 *   npx playwright test --headed   (브라우저 표시)
 *   npx playwright test --debug    (디버그 모드)
 */

require('dotenv').config();
const { test, expect } = require('@playwright/test');
const {
  login,
  addToCart,
  proceedToCheckout,
  selectPaymentAndPay,
} = require('../utils/amoremall');

const ID = process.env.AMOREMALL_ID;
const PASSWORD = process.env.AMOREMALL_PASSWORD;
const PRODUCT_NUMBERS = (process.env.PRODUCT_NUMBERS || '').split(',').map((p) => p.trim()).filter(Boolean);
const PAYMENT_METHOD = process.env.PAYMENT_METHOD || 'card';

test.beforeAll(() => {
  if (!ID || !PASSWORD) {
    throw new Error('.env 파일에 AMOREMALL_ID 와 AMOREMALL_PASSWORD 를 설정하세요.');
  }
  if (PRODUCT_NUMBERS.length === 0) {
    throw new Error('.env 파일 또는 환경변수에 PRODUCT_NUMBERS 를 설정하세요. (예: PRODUCT_NUMBERS=1234567)');
  }
});

test('아모레몰 로그인 확인', async ({ page }) => {
  await login(page, ID, PASSWORD);

  // 로그인 후 마이페이지 또는 메인에 아이디가 표시되는지 확인
  const url = page.url();
  expect(url).not.toContain('loginForm');
});

test('상품 장바구니 담기', async ({ page }) => {
  await login(page, ID, PASSWORD);

  for (const productNo of PRODUCT_NUMBERS) {
    await addToCart(page, productNo);
  }

  // 장바구니 페이지로 이동해서 상품이 담겼는지 확인
  await page.goto('https://www.amoremall.com/cart/cartView.do');
  await page.waitForLoadState('domcontentloaded');

  const cartItems = await page.$$('.cart-item, .cart-list li, [class*="cartItem"], [class*="cart-prod"]');
  expect(cartItems.length).toBeGreaterThan(0);
  console.log(`✅ 장바구니에 ${cartItems.length}개 상품 확인`);
});

test('결제 페이지 진입', async ({ page }) => {
  await login(page, ID, PASSWORD);

  for (const productNo of PRODUCT_NUMBERS) {
    await addToCart(page, productNo);
  }

  await proceedToCheckout(page);

  // 결제 페이지 URL 확인
  const url = page.url();
  expect(url).toMatch(/order|checkout|payment/i);
  console.log(`✅ 결제 페이지 접속: ${url}`);
});

test('전체 플로우: 로그인 → 장바구니 → 결제', async ({ page }) => {
  // 1. 로그인
  await login(page, ID, PASSWORD);

  // 2. 상품 장바구니 담기
  for (const productNo of PRODUCT_NUMBERS) {
    await addToCart(page, productNo);
  }

  // 3. 결제 페이지 진입
  await proceedToCheckout(page);

  // 4. 결제 수단 선택 및 결제 요청
  // ⚠️ 실제 결제가 이루어집니다. 테스트 시 주석 처리하세요.
  // await selectPaymentAndPay(page, PAYMENT_METHOD);

  console.log('');
  console.log('========================================');
  console.log('⚠️  결제 단계까지 진입했습니다.');
  console.log('   실제 결제를 진행하려면 아래 주석을 해제하세요:');
  console.log('   selectPaymentAndPay(page, PAYMENT_METHOD)');
  console.log('========================================');

  // 결제 페이지 스크린샷 저장
  await page.screenshot({ path: 'checkout-ready.png', fullPage: true });
  console.log('📸 결제 페이지 스크린샷: checkout-ready.png');
});
