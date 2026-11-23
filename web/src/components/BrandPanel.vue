<script setup>
import BrandMark from './BrandMark.vue'
</script>

<template>
  <aside class="brand-panel">
    <div class="brand-top">
      <BrandMark :size="42" />
      <div>
        <p class="brand-kicker">SALEOR ASSISTANT</p>
        <p class="brand-name">智能购物助手</p>
      </div>
    </div>

    <div class="brand-copy">
      <h1>把逛店<br />变成一句话</h1>
      <p class="brand-subtitle">
        找商品、加购物车、查配送，直接告诉助手就好。
      </p>

      <ul class="feature-list">
        <li>
          <span class="feature-icon">🔎</span>
          <span>
            <strong>自然语言找商品</strong>
            <small>描述需求即可获得推荐</small>
          </span>
        </li>
        <li>
          <span class="feature-icon">🛒</span>
          <span>
            <strong>一句话加入购物车</strong>
            <small>自动处理规格和数量</small>
          </span>
        </li>
        <li>
          <span class="feature-icon">🚚</span>
          <span>
            <strong>配送与下单</strong>
            <small>确认地址和配送方式后提交</small>
          </span>
        </li>
      </ul>
    </div>

    <div class="brand-decor" aria-hidden="true">
      <div class="decor-card card-one">
        <span>👕</span>
        <b>T 恤</b>
        <small>¥129</small>
      </div>
      <div class="decor-card card-two">
        <span>🎧</span>
        <b>耳机</b>
        <small>¥299</small>
      </div>
      <div class="decor-orb"></div>
    </div>

    <p class="brand-footer">体验版 · 对话暂不保存</p>
  </aside>
</template>

<style scoped>
.brand-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 44px 52px;
  overflow: hidden;
  color: #fffaf4;
  background:
    radial-gradient(circle at 18% 18%, rgba(255, 255, 255, 0.14), transparent 32%),
    radial-gradient(circle at 88% 82%, rgba(255, 173, 128, 0.28), transparent 36%),
    linear-gradient(145deg, #1f1b18 0%, #3a241c 48%, #a63f1e 100%);
}

.brand-panel::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.16;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(to bottom, black, transparent 75%);
}

.brand-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.62);
}

.brand-name {
  margin: 2px 0 0;
  font-size: 17px;
  font-weight: 650;
}

.brand-copy {
  position: relative;
  z-index: 1;
  margin-top: clamp(48px, 9vh, 96px);
  max-width: 480px;
}

.brand-copy h1 {
  margin: 0;
  font-size: clamp(40px, 4.2vw, 62px);
  line-height: 1.06;
  letter-spacing: -0.04em;
  color: #fff;
}

.brand-subtitle {
  margin: 22px 0 0;
  max-width: 360px;
  font-size: 16px;
  line-height: 1.7;
  color: rgba(255, 250, 244, 0.72);
}

.feature-list {
  display: grid;
  gap: 16px;
  margin: 40px 0 0;
  padding: 0;
  list-style: none;
}

.feature-list li {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  border-radius: 12px;
  font-size: 19px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
}

.feature-list strong {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.feature-list small {
  display: block;
  margin-top: 3px;
  font-size: 12px;
  color: rgba(255, 250, 244, 0.58);
}

.brand-decor {
  position: absolute;
  right: 40px;
  bottom: 110px;
  width: 260px;
  height: 220px;
  pointer-events: none;
}

.decor-orb {
  position: absolute;
  right: 8px;
  bottom: 4px;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #ff9a72, #d34f21 52%, #7b2b11);
  filter: blur(0.2px);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.3);
}

.decor-card {
  position: absolute;
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 116px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(14px);
}

.decor-card span {
  font-size: 26px;
}

.decor-card b {
  font-size: 13px;
  color: #fff;
}

.decor-card small {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.66);
}

.card-one {
  top: 10px;
  left: 6px;
  transform: rotate(-8deg);
}

.card-two {
  right: 0;
  bottom: 50px;
  transform: rotate(7deg);
}

.brand-footer {
  position: relative;
  z-index: 1;
  margin-top: auto;
  padding-top: 40px;
  font-size: 12px;
  color: rgba(255, 250, 244, 0.46);
}

@media (max-width: 980px) {
  .brand-panel {
    display: none;
  }
}
</style>