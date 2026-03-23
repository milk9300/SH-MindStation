<template>
	<view class="container">
		<view class="section-header">
			<text class="section-title">📚 心理科普</text>
		</view>
		
		<view class="article-list">
			<view 
				class="article-card" 
				v-for="item in articles" 
				:key="item.id"
				@click="openArticle(item)"
			>
				<image class="article-cover" :src="item.cover_image" mode="aspectFill"></image>
				<view class="article-info">
					<text class="article-title">{{ item.title }}</text>
					<text class="article-meta">{{ item.author }} · {{ formatDate(item.created_at) }}</text>
				</view>
			</view>
		</view>
		
		<view class="section-header" style="margin-top: 40rpx;">
			<text class="section-title">📋 心理测评</text>
		</view>
		
		<view class="scale-list">
			<view 
				class="scale-card" 
				v-for="scale in scales" 
				:key="scale.id"
				@click="startAssessment(scale)"
			>
				<view class="scale-icon">📝</view>
				<view class="scale-body">
					<text class="scale-name">{{ scale.name }}</text>
					<text class="scale-desc">{{ scale.question_count }} 道题 · 约 {{ Math.ceil(scale.question_count * 0.5) }} 分钟</text>
				</view>
				<view class="scale-arrow">›</view>
			</view>
		</view>
		
		<view v-if="loading" class="loading-tip">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const articles = ref([])
const scales = ref([])
const loading = ref(false)

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	return dateStr.substring(0, 10)
}

const fetchData = async () => {
	loading.value = true
	try {
		const artRes = await request({ url: '/articles/', method: 'GET' })
		const scaleRes = await request({ url: '/scales/', method: 'GET' })
		articles.value = Array.isArray(artRes) ? artRes : []
		scales.value = Array.isArray(scaleRes) ? scaleRes : []
	} catch (err) {
		console.error('Fetch discovery data error:', err)
	} finally {
		loading.value = false
	}
}

const openArticle = (item) => {
	uni.navigateTo({
		url: `/pages/discovery/article-detail?id=${item.id}`
	})
}

const startAssessment = (scale) => {
	uni.navigateTo({
		url: `/pages/discovery/assessment?id=${scale.id}`
	})
}

onMounted(() => {
	fetchData()
})
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.section-header {
	margin-bottom: 24rpx;
}
.section-title {
	font-size: 34rpx;
	font-weight: 600;
	color: $sh-text-main;
}

// 文章卡片
.article-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}
.article-card {
	@include sh-card;
	display: flex;
	align-items: center;
	padding: 20rpx;
	.article-cover {
		width: 180rpx;
		height: 120rpx;
		border-radius: $sh-radius-sm;
		flex-shrink: 0;
		background: #eee;
	}
	.article-info {
		flex: 1;
		margin-left: 24rpx;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	.article-title {
		font-size: 28rpx;
		font-weight: 500;
		color: $sh-text-main;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		overflow: hidden;
		margin-bottom: 10rpx;
	}
	.article-meta {
		font-size: 22rpx;
		color: $sh-text-sub;
	}
}

// 量表卡片
.scale-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}
.scale-card {
	@include sh-card;
	display: flex;
	align-items: center;
	padding: 28rpx;
	.scale-icon {
		font-size: 48rpx;
		margin-right: 20rpx;
	}
	.scale-body {
		flex: 1;
	}
	.scale-name {
		display: block;
		font-size: 28rpx;
		font-weight: 500;
		color: $sh-text-main;
		margin-bottom: 6rpx;
	}
	.scale-desc {
		display: block;
		font-size: 22rpx;
		color: $sh-text-sub;
	}
	.scale-arrow {
		font-size: 40rpx;
		color: $sh-text-sub;
	}
}

.loading-tip {
	text-align: center;
	padding: 40rpx;
	color: $sh-text-sub;
	font-size: 24rpx;
}
</style>
