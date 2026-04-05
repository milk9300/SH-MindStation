<template>
	<view class="location-card">
		<view class="card-header">
			<text class="header-icon">📍</text>
			<text class="header-title">{{ data.name }}</text>
		</view>
		<view class="card-body">
			<view class="info-row">
				<text class="info-label">具体地点：</text>
				<text class="info-value highlight">{{ data.location || '校内指定地点' }}</text>
			</view>
			<view class="info-row">
				<text class="info-label">开放时间：</text>
				<text class="info-value">{{ data.open_hours || '详见校内公告' }}</text>
			</view>
			<view class="info-row" v-if="data.contact">
				<text class="info-label">负 责 人：</text>
				<text class="info-value">{{ data.contact }}</text>
			</view>
		</view>
		<view class="card-footer">
			<button class="action-btn" @tap="handleNavigate">
				<text class="btn-icon">🚀</text>
				<text>立即前往</text>
			</button>
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

const handleNavigate = () => {
	uni.showToast({
		title: '地图导航功能正在接入...',
		icon: 'none'
	})
}
</script>

<style lang="scss" scoped>
.location-card {
	@include sh-card;
	border-left: 8rpx solid $sh-primary;
	background: #ffffff;
	padding: 0;
	overflow: hidden;
	margin-bottom: 24rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.05);
}

.card-header {
	padding: 24rpx 30rpx;
	display: flex;
	align-items: center;
	background: rgba($sh-primary, 0.03);
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
	
	.header-icon {
		margin-right: 12rpx;
		font-size: 32rpx;
	}
	.header-title {
		font-size: 30rpx;
		font-weight: 600;
		color: $sh-text-main;
	}
}

.card-body {
	padding: 30rpx;
	
	.info-row {
		display: flex;
		margin-bottom: 16rpx;
		&:last-child { margin-bottom: 0; }
		
		.info-label {
			width: 140rpx;
			font-size: 26rpx;
			color: $sh-text-sub;
		}
		.info-value {
			flex: 1;
			font-size: 28rpx;
			color: $sh-text-main;
			&.highlight {
				color: $sh-primary;
				font-weight: 500;
			}
		}
	}
}

.card-footer {
	padding: 20rpx 30rpx;
	border-top: 1px dashed rgba(0, 0, 0, 0.05);
	
	.action-btn {
		width: 100%;
		height: 72rpx;
		background: $sh-primary;
		color: #ffffff;
		border-radius: 36rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 28rpx;
		border: none;
		
		.btn-icon {
			margin-right: 8rpx;
		}
		
		&:active {
			opacity: 0.8;
		}
	}
}
</style>
