<template>
	<view class="article-card" @click="handleNavigate">
		<view class="article-info">
			<text class="article-title">{{ data.title }}</text>
			<view class="article-meta">
				<text class="meta-icon">📖</text>
				<text class="meta-text">{{ data.content || '校心理咨询中心' }}</text>
			</view>
		</view>
		<view class="article-image">
			<image 
				v-if="imageUrl && !imageError" 
				:src="imageUrl" 
				mode="aspectFill"
				class="img"
				@error="handleImageError"
			></image>
			<view v-else class="image-placeholder">
				<text class="placeholder-icon">🖼️</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
	data: {
		type: Object,
		required: true
	}
})

const imageError = ref(false)

// 基础媒体地址，实际应从统一配置文件读取，此处暂与 request.js 保持一致
const MEDIA_BASE_URL = 'http://127.0.0.1:8000/'

const imageUrl = computed(() => {
	const img = props.data.extra_info?.image
	if (!img) return ''
	// 如果是完整 URL 则直接返回
	if (img.startsWith('http')) return img
	// 否则拼接后端媒体路径
	return MEDIA_BASE_URL + (img.startsWith('/') ? img.slice(1) : img)
})

const handleImageError = () => {
	imageError.value = true
}

const handleNavigate = () => {
	// 模拟跳转，实际项目中可以根据 data.extra_info.id 跳转
	uni.navigateTo({
		url: '/pages/discovery/article-detail?id=' + (props.data.extra_info?.id || 'default'),
		fail: () => {
			uni.showToast({
				title: '文章正在努力加载中...',
				icon: 'none'
			})
		}
	})
}
</script>

<style lang="scss" scoped>
.article-card {
	@include sh-card;
	display: flex;
	padding: 24rpx;
	align-items: center;
	transition: all 0.3s $sh-bezier;
	margin-bottom: 24rpx;
	
	&:active {
		transform: translateY(2rpx);
		box-shadow: 0 4rpx 12rpx rgba(138, 187, 161, 0.04);
	}
}

.article-info {
	flex: 1;
	margin-right: 24rpx;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
}

.article-title {
	font-size: 28rpx;
	font-weight: 600;
	color: $sh-text-main;
	line-height: 1.5;
	margin-bottom: 16rpx;
	display: -webkit-box;
	-webkit-box-orient: vertical;
	-webkit-line-clamp: 2;
	line-clamp: 2;
	overflow: hidden;
}

.article-meta {
	display: flex;
	align-items: center;
	.meta-icon {
		font-size: 24rpx;
		margin-right: 8rpx;
	}
	.meta-text {
		font-size: 22rpx;
		color: $sh-text-sub;
		white-space: pre-wrap;
	}
}

.article-image {
	width: 140rpx;
	height: 140rpx;
	border-radius: $sh-radius-sm;
	overflow: hidden;
	background: #f0f4f2;
	flex-shrink: 0;
	
	.img {
		width: 100%;
		height: 100%;
	}
	
	.image-placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		.placeholder-icon {
			font-size: 40rpx;
			opacity: 0.3;
		}
	}
}
</style>
