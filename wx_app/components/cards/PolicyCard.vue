<template>
	<view class="policy-card">
		<view class="card-header">
			<text class="header-icon">🏢</text>
			<text class="header-title">{{ data.title }}</text>
		</view>
		<view class="card-body">
			<text class="policy-content">{{ data.content }}</text>
			<view class="policy-details">
				<view class="detail-item" v-if="data.extra_info && data.extra_info.org">
					<text class="detail-icon">💼</text>
					<text class="detail-label">负责部门：</text>
					<text class="detail-value">{{ data.extra_info.org }}</text>
				</view>
				<view class="detail-item" v-if="data.extra_info && data.extra_info.location">
					<text class="detail-icon">📍</text>
					<text class="detail-label">办理地点：</text>
					<text class="detail-value">{{ data.extra_info.location }}</text>
				</view>
			</view>
		</view>
		<view class="card-footer" @click="handleCopyLocation" v-if="data.extra_info && data.extra_info.location">
			<text class="footer-btn">复制办理地址</text>
		</view>
	</view>
</template>

<script setup>
const props = defineProps({
	data: {
		type: Object,
		required: true
	}
})

const handleCopyLocation = () => {
	if (!props.data.extra_info || !props.data.extra_info.location) return
	
	uni.setClipboardData({
		data: props.data.extra_info.location,
		success: () => {
			uni.showToast({
				title: '地址已复制',
				icon: 'none'
			})
		}
	})
}
</script>

<style lang="scss" scoped>
.policy-card {
	@include sh-card;
	border-top: 6rpx solid $sh-secondary;
	background: linear-gradient(to bottom, #ffffff, #f7fbff);
	padding: 0;
	overflow: hidden;
	margin-bottom: 24rpx;
}

.card-header {
	padding: 24rpx 30rpx;
	display: flex;
	align-items: center;
	border-bottom: 1px solid rgba($sh-secondary, 0.1);
	
	.header-icon {
		margin-right: 12rpx;
		font-size: 32rpx;
	}
	.header-title {
		font-size: 30rpx;
		font-weight: 600;
		color: #4a90e2; // $sh-secondary is #AFC8D8, for text we need something darker
	}
}

.card-body {
	padding: 30rpx;
	
	.policy-content {
		display: block;
		font-size: 28rpx;
		color: $sh-text-main;
		line-height: 1.6;
		margin-bottom: 24rpx;
		white-space: pre-wrap;
	}
}

.policy-details {
	background: rgba($sh-secondary, 0.05);
	border-radius: $sh-radius-sm;
	padding: 16rpx 20rpx;
	
	.detail-item {
		display: flex;
		align-items: flex-start;
		margin-bottom: 12rpx;
		&:last-child { margin-bottom: 0; }
		
		.detail-icon {
			font-size: 24rpx;
			margin-right: 12rpx;
			margin-top: 4rpx;
		}
		.detail-label {
			font-size: 24rpx;
			color: $sh-text-sub;
			white-space: nowrap;
		}
		.detail-value {
			font-size: 24rpx;
			color: $sh-text-main;
			font-weight: 500;
		}
	}
}

.card-footer {
	padding: 24rpx 30rpx;
	border-top: 1px solid $sh-border;
	text-align: center;
	
	.footer-btn {
		font-size: 26rpx;
		color: #4a90e2;
		font-weight: 500;
	}
	
	&:active {
		background: rgba($sh-secondary, 0.05);
	}
}
</style>
