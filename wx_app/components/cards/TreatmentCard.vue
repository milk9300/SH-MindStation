<template>
	<view class="treatment-card">
		<view class="card-header">
			<text class="header-icon">✨</text>
			<text class="header-title">{{ data.title }}</text>
		</view>
		<view class="card-body">
			<view v-for="(step, index) in steps" :key="index" class="step-item">
				<text class="step-text">{{ step }}</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	data: {
		type: Object,
		required: true
	}
})

// 将 content 按换行符拆分为步骤
const steps = computed(() => {
	if (!props.data.content) return []
	return props.data.content.split('\n').filter(s => s.trim())
})

</script>

<style lang="scss" scoped>
.treatment-card {
	@include sh-card;
	border-top: 6rpx solid $sh-primary;
	background: linear-gradient(to bottom, #ffffff, #f9fdfb);
	padding: 0;
	overflow: hidden;
	margin-bottom: 24rpx;
}

.card-header {
	padding: 24rpx 30rpx;
	display: flex;
	align-items: center;
	border-bottom: 1px solid rgba($sh-primary, 0.1);
	
	.header-icon {
		margin-right: 12rpx;
		font-size: 32rpx;
	}
	.header-title {
		font-size: 30rpx;
		font-weight: 600;
		color: $sh-primary;
	}
}

.card-body {
	padding: 30rpx;
	
	.step-item {
		margin-bottom: 16rpx;
		&:last-child { margin-bottom: 0; }
	}
	.step-text {
		font-size: 28rpx;
		color: $sh-text-main;
		line-height: 1.6;
	}
}

</style>
