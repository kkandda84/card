/**
 * 아모레몰 결제 자동화 - 단독 실행 스크립트
 *
 * 사용법:
 *   node scripts/checkout.js 1234567
 *   node scripts/checkout.js 1234567 2345678
 *   PAYMENT_METHOD=kakao_pay node scripts/checkout.js 1234567
 */

require('dotenv').config();
const { chromium } = require('@playwright/test');
const {
  login,
  addToCart,
  proceedToCheckout,
  selectPaymentAndPay,
} = require('../utils/amoremall');

const ID = process.env.AMOREMALL_ID;
const PASSWORD = process.env.AMOREMALL_PASSWORD;
const PAYMENT_METHOD = process.env.PAYMENT_METHOD || 'card';
const HEADLESS = process.env.HEADLESS !== 'false';
const SLOW_MO = parseInt(process.env.SLOW_MO || '150');

// CLI 인자 또는 환경변수에서 상품번호 가져오기
const productNumbers = process.argv.slice(2).length > 0
  ? process.argv.slice(2)
  : (process.env.PRODUCT_NUMBERS || '').split(',').map((p) => p.trim()).filter(Boolean);

(async () => {
  if (!ID || !PASSWORD) {
    console.error('❌ .env 파일에 AMOREMALL_ID 와 AMOREMALL_PASSWORD 를 설정하세요.');
    process.exit(1);
  }

  if (productNumbers.length === 0) {
    console.error('❌ 상품번호를 입력하세요.');
    console.error('   사용법: node scripts/checkout.js 1234567');
    process.exit(1);
  }

  console.log('🚀 아모레몰 자동화 시작');
  console.log(`   상품번호: ${productNumbers.join(', ')}`);
  console.log(`   결제수단: ${PAYMENT_METHOD}`);
  console.log(`   브라우저: ${HEADLESS ? 'headless' : '창 표시'}`);
  console.log('');

  const browser = await chromium.launch({
    headless: HEADLESS,
    slowMo: SLOW_MO,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined,
  });

  const context = await browser.newContext({
    locale: 'ko-KR',
    timezoneId: 'Asia/Seoul',
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  });

  const page = await context.newPage();

  try {
    // 1. 로그인
    await login(page, ID, PASSWORD);

    // 2. 상품 장바구니 담기
    for (const productNo of productNumbers) {
      await addToCart(page, productNo);
    }

    // 3. 결제 페이지 진입
    await proceedToCheckout(page);

    // 4. 결제 수단 선택 및 결제
    await selectPaymentAndPay(page, PAYMENT_METHOD);

    // 결제 완료 페이지 대기 (PG사 창에서 처리 후 복귀)
    console.log('⏳ 결제 처리 중... (최대 60초 대기)');
    await page.waitForURL(/complete|finish|done|success|주문완료/i, {
      timeout: 60000,
    }).catch(() => {
      console.log('ℹ️  결제 완료 페이지 자동 감지 실패 - 브라우저에서 직접 확인하세요.');
    });

    await page.screenshot({ path: 'checkout-complete.png', fullPage: true });
    console.log('');
    console.log('✅ 결제 자동화 완료!');
    console.log('📸 스크린샷: checkout-complete.png');

  } catch (err) {
    console.error('');
    console.error(`❌ 오류 발생: ${err.message}`);
    await page.screenshot({ path: 'error-screenshot.png', fullPage: true }).catch(() => {});
    console.error('📸 오류 스크린샷: error-screenshot.png');
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
