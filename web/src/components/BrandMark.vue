<script setup>
defineProps({
  size: {
    type: Number,
    default: 36,
  },
})
</script>

<template>
  <span
    class="brand-mark"
    :style="{ width: `${size}px`, height: `${size}px` }"
    aria-hidden="true"
  >
    <svg viewBox="0 0 24 24" fill="none">
      <path
        d="M6.2 8.4h11.6l-1 10.2H7.2L6.2 8.4Z"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linejoin="round"
      />
      <path
        d="M9.2 8.4V7a2.8 2.8 0 0 1 5.6 0v1.4"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
      />
      <path
        d="m17.4 4.2.55 1.35 1.35.55-1.35.55-.55 1.35-.55-1.35L15.5 6.1l1.35-.55.55-1.35Z"
        fill="currentColor"
      />
    </svg>
  </span>
</template>

<style scoped>
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 28%;
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  box-shadow: 0 6px 16px rgba(232, 93, 42, 0.25);
}

svg {
  width: 64%;
  height: 64%;
}
</style>