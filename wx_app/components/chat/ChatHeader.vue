<template>
	<view class="custom-header" :style="{ paddingTop: statusBarHeight + 'px' }">
		<view class="header-content">
			<!-- 左侧区域：导航及标题 -->
			<view class="header-left">
				<view class="menu-btn" @click="$emit('toggle-sidebar')">
					<text class="menu-icon">☰</text>
				</view>
				<view class="title-wrap">
					<text class="header-title">SH MindStation</text>
					<view class="new-chat-btn" @click="$emit('new-chat')">
						<text class="plus-icon">＋</text>
					</view>
				</view>
			</view>
			
			<!-- 右侧区域：留空给微信胶囊 -->
			<view class="header-right"></view>
		</view>
	</view>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
	statusBarHeight: {
		type: Number,
		default: 20
	}
})

const emit = defineEmits(['toggle-sidebar', 'new-chat'])
</script>

<style lang="scss" scoped>
.custom-header {
	background: #fff;
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 200;
	box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.02);
	.header-content {
		height: 88rpx;
		display: flex;
		align-items: center;
		padding: 0 20rpx 0 30rpx;
		
		.header-left {
			display: flex;
			align-items: center;
			gap: 20rpx;
			flex: 1;
		}

		.menu-btn {
			padding: 10rpx;
			display: flex;
			align-items: center;
			justify-content: center;
			.menu-icon {
				font-size: 40rpx;
				color: $sh-text-main;
			}
		}

		.title-wrap {
			display: flex;
			align-items: center;
			gap: 16rpx;
			
			.header-title {
				font-size: 32rpx;
				font-weight: 700;
				color: $sh-text-main;
				letter-spacing: 0.5rpx;
			}
			
			.new-chat-btn {
				background: rgba($sh-primary, 0.1);
				color: $sh-primary;
				width: 48rpx;
				height: 48rpx;
				border-radius: 12rpx;
				display: flex;
				align-items: center;
				justify-content: center;
				transition: all 0.2s;
				
				.plus-icon {
					font-size: 32rpx;
					font-weight: bold;
				}
				
				&:active {
					transform: scale(0.9);
					background: rgba($sh-primary, 0.2);
				}
			}
		}

		.header-right {
			width: 180rpx; // 预留给微信胶囊按钮的宽度
		}
	}
}
</style>
