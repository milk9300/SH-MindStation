<template>
	<view class="container">
		<view class="favorite-list" v-if="favorites.length > 0">
			<!-- 这里我们假设后端返回的 favorite 对象里包含了 article 的简要信息，或者我们根据 target_id 匹配 -->
			<!-- 实际生产中通常用 SerializerMethodField 或嵌套 Serializer 直接返回 article 标题和封面 -->
			<view 
				class="fav-card" 
				v-for="item in favorites" 
				:key="item.id"
				@click="goToDetail(item)"
			>
				<view class="fav-type-tag">{{ item.target_type === 'article' ? '科普' : '内容' }}</view>
				<view class="fav-info">
					<text class="fav-title">{{ item.target_title || '收藏内容' }}</text>
					<text class="fav-date">收藏于 {{ formatDate(item.created_at) }}</text>
				</view>
				<view class="fav-arrow">›</view>
			</view>
		</view>

		<view class="empty-state" v-else-if="!loading">
			<view class="icon">⭐</view>
			<text>暂无收藏内容</text>
			<view class="go-btn" @click="goToDiscovery">去发现好文</view>
		</view>

		<view v-if="loading" class="loading-state">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const favorites = ref([])
const loading = ref(false)

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	return dateStr.substring(0, 10)
}

const fetchFavorites = async () => {
	loading.value = true
	try {
		const res = await request({
			url: '/favorites/',
			method: 'GET',
			data: { target_type: 'article' }
		})
		const list = res.results || res || []
		favorites.value = Array.isArray(list) ? list : []
	} catch (err) {
		console.error('Fetch favorites error:', err)
	} finally {
		loading.value = false
	}
}

const goToDetail = (item) => {
	if (item.target_type === 'article') {
		uni.navigateTo({
			url: `/pages/discovery/article-detail?id=${item.target_id}`
		})
	}
}

const goToDiscovery = () => {
	uni.switchTab({ url: '/pages/discovery/index' })
}

onMounted(() => {
	fetchFavorites()
})
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.favorite-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}
.fav-card {
	@include sh-card;
	padding: 30rpx;
	display: flex;
	align-items: center;
	.fav-type-tag {
		background: rgba($sh-primary, 0.1);
		color: $sh-primary;
		font-size: 20rpx;
		padding: 4rpx 12rpx;
		border-radius: 4rpx;
		margin-right: 20rpx;
	}
	.fav-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		.fav-title {
			font-size: 30rpx;
			font-weight: 500;
			color: $sh-text-main;
			margin-bottom: 8rpx;
			// 标题过长省略
			display: -webkit-box;
			-webkit-box-orient: vertical;
			-webkit-line-clamp: 1;
			line-clamp: 1;
			overflow: hidden;
		}
		.fav-date {
			font-size: 22rpx;
			color: $sh-text-sub;
		}
	}
	.fav-arrow {
		font-size: 40rpx;
		color: $sh-text-sub;
	}
}
.empty-state {
	padding: 200rpx 0;
	text-align: center;
	color: $sh-text-sub;
	.icon {
		font-size: 80rpx;
		margin-bottom: 20rpx;
	}
	.go-btn {
		margin-top: 40rpx;
		color: $sh-primary;
		font-size: 28rpx;
		text-decoration: underline;
	}
}
.loading-state {
	text-align: center;
	padding: 100rpx;
	color: $sh-text-sub;
}
</style>
