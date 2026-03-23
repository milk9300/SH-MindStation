<template>
	<view class="crisis-card">
		<view class="card-header">
			<text class="header-icon">🚨</text>
			<text class="header-title">{{ data.title }}</text>
		</view>
		<view class="card-body">
			<text class="crisis-content">{{ data.content }}</text>
			
			<view class="risk-indicator" v-if="data.extra_info && data.extra_info.level">
				<text class="risk-label">风险等级：</text>
				<text class="risk-value">{{ data.extra_info.level }}</text>
			</view>
			
			<view class="hotline-section">
				<view class="hotline-info">
					<text class="label">联系电话：</text>
					<text class="phone-number">{{ phoneDisplay }}</text>
				</view>
				<view class="call-btn" @click="handleCall">
					<text class="call-icon">📞</text>
					<text class="call-text">立即拨打热线</text>
				</view>
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

// 处理电话显示逻辑，优先从 extra_info 获取，否则从 content 匹配
const phoneDisplay = computed(() => {
	if (props.data.extra_info && props.data.extra_info.phone) {
		return props.data.extra_info.phone
	}
	// 简单正则匹配内容里的电话
	const phoneMatch = props.data.content.match(/\d{3}-\d{3,4}-\d{4}/) || props.data.content.match(/\d{10,11}/)
	return phoneMatch ? phoneMatch[0] : '400-123-4567'
})

const handleCall = () => {
	uni.makePhoneCall({
		phoneNumber: phoneDisplay.value.replace(/-/g, ''),
		fail: () => {
			uni.showToast({
				title: '拨打失败',
				icon: 'none'
			})
		}
	})
}
</script>

<style lang="scss" scoped>
.crisis-card {
	@include sh-card;
	border: 2rpx solid $sh-error;
	background: #FFF5F5;
	padding: 0;
	overflow: hidden;
	margin-bottom: 24rpx;
}

.card-header {
	padding: 24rpx 30rpx;
	display: flex;
	align-items: center;
	border-bottom: 1px solid rgba($sh-error, 0.1);
	
	.header-icon {
		margin-right: 12rpx;
		font-size: 32rpx;
	}
	.header-title {
		font-size: 32rpx;
		font-weight: 700;
		color: $sh-error;
	}
}

.card-body {
	padding: 34rpx 30rpx;
}

.crisis-content {
	display: block;
	font-size: 28rpx;
	color: $sh-text-main;
	line-height: 1.8;
	margin-bottom: 30rpx;
	font-weight: 500;
}

.risk-indicator {
	display: flex;
	align-items: center;
	margin-bottom: 24rpx;
	.risk-label {
		font-size: 24rpx;
		color: $sh-text-sub;
	}
	.risk-value {
		font-size: 24rpx;
		color: $sh-error;
		font-weight: bold;
	}
}

.hotline-section {
	border-top: 1px dashed rgba($sh-error, 0.15);
	padding-top: 30rpx;
}

.hotline-info {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
	
	.label {
		font-size: 26rpx;
		color: $sh-text-sub;
	}
	.phone-number {
		font-size: 32rpx;
		color: $sh-error;
		font-weight: bold;
		font-family: 'Courier New', Courier, monospace;
	}
}

.call-btn {
	background: $sh-error;
	padding: 24rpx;
	border-radius: $sh-radius-md;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 20rpx rgba($sh-error, 0.2);
	
	.call-icon {
		margin-right: 16rpx;
		font-size: 32rpx;
		color: #fff;
	}
	.call-text {
		color: #fff;
		font-size: 30rpx;
		font-weight: 600;
	}
	
	&:active {
		opacity: 0.8;
		transform: scale(0.98);
	}
}
</style>
