<template>
	<view class="container">
		
		<!-- 科普动态搜索 -->
		<view class="section-header">
			<view class="search-bar">
				<text class="search-icon">🔍</text>
				<input 
					class="search-input" 
					type="text" 
					v-model="keyword" 
					placeholder="搜索感兴趣的心理文章..." 
					@input="onSearchInput"
				/>
				<text class="clear-icon" v-if="keyword" @click="clearSearch">✕</text>
			</view>
		</view>

		<!-- 瀑布流文章列表 -->
		<view class="waterfall-container">
			<view class="waterfall-column">
				<view 
					class="article-card" 
					v-for="item in leftList" 
					:key="item.id"
					@click="goToArticle(item)"
				>
					<image class="article-cover" :src="item.cover_image" mode="widthFix" v-if="item.cover_image" />
					<view class="article-info">
						<text class="article-title">{{ item.title }}</text>
						<text class="article-author">{{ item.author || '心邻空间' }}</text>
					</view>
				</view>
			</view>
			<view class="waterfall-column">
				<view 
					class="article-card" 
					v-for="item in rightList" 
					:key="item.id"
					@click="goToArticle(item)"
				>
					<image class="article-cover" :src="item.cover_image" mode="widthFix" v-if="item.cover_image" />
					<view class="article-info">
						<text class="article-title">{{ item.title }}</text>
						<text class="article-author">{{ item.author || '心邻空间' }}</text>
					</view>
				</view>
			</view>
		</view>
		
		<view class="loading-status" v-if="loading || !hasMore">
			<text v-if="loading">加载中...</text>
			<view v-else-if="!hasMore && articles.length > 0" class="no-more">
				<text>没有更多文章了</text>
			</view>
			<view v-else-if="!loading && articles.length === 0" class="empty-list">
				<text>暂无相关文章</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onReachBottom } from '@dcloudio/uni-app'
import request from '@/utils/request.js'

const articles = ref([])
const leftList = ref([])
const rightList = ref([])
const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)

const keyword = ref('')
let searchTimer = null

onMounted(() => {
	fetchArticles(true)
})

onReachBottom(() => {
	if (!loading.value && hasMore.value) {
		fetchArticles()
	}
})

const onSearchInput = () => {
	if (searchTimer) clearTimeout(searchTimer)
	searchTimer = setTimeout(() => {
		fetchArticles(true)
	}, 500)
}

const clearSearch = () => {
	keyword.value = ''
	fetchArticles(true)
}

const fetchArticles = async (isRefresh = false) => {
	if (loading.value && !isRefresh) return
	if (isRefresh) {
		page.value = 1
		articles.value = []
		leftList.value = []
		rightList.value = []
		hasMore.value = true
	}
	
	loading.value = true
	try {
		const url = `/articles/?page=${page.value}${keyword.value ? '&search=' + keyword.value : ''}`
		const res = await request({
			url: url,
			method: 'GET'
		})
		
		const newItems = res.results || []
		
		newItems.forEach((item, index) => {
			if ((articles.value.length + index) % 2 === 0) {
				leftList.value.push(item)
			} else {
				rightList.value.push(item)
			}
		})

		articles.value.push(...newItems)
		
		hasMore.value = !!res.next
		if (hasMore.value) {
			page.value++
		}
	} catch (e) {
		console.error('Fetch articles error:', e)
	} finally {
		loading.value = false
	}
}

const goToArticle = (article) => {
	uni.navigateTo({
		url: `/pages/discovery/article-detail?id=${article.id}`
	})
}
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}

.section-header {
	margin-top: 20rpx;
	margin-bottom: 40rpx;
	.search-bar {
		height: 80rpx;
		background: #fff;
		border-radius: 40rpx;
		display: flex;
		align-items: center;
		padding: 0 30rpx;
		border: 1rpx solid rgba($sh-primary, 0.1);
		box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
		.search-icon {
			font-size: 32rpx;
			margin-right: 16rpx;
			color: $sh-text-sub;
		}
		.search-input {
			flex: 1;
			font-size: 28rpx;
			color: $sh-text-main;
		}
		.clear-icon {
			padding: 10rpx;
			font-size: 28rpx;
			color: $sh-text-sub;
		}
	}
}

// 瀑布流布局
.waterfall-container {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
}
.waterfall-column {
	width: 48.5%;
	display: flex;
	flex-direction: column;
}
.article-card {
	@include sh-card;
	padding: 0;
	margin-bottom: 24rpx;
	overflow: hidden;
	background: #fff;
	border-radius: 24rpx;
	.article-cover {
		width: 100%;
		display: block;
		background: #f0f0f0;
	}
	.article-info {
		padding: 24rpx;
		.article-title {
			font-size: 28rpx;
			font-weight: 600;
			color: $sh-text-main;
			display: -webkit-box;
			-webkit-box-orient: vertical;
			-webkit-line-clamp: 2;
			line-clamp: 2;
			overflow: hidden;
			line-height: 1.5;
			margin-bottom: 12rpx;
		}
		.article-author {
			font-size: 22rpx;
			color: $sh-text-sub;
		}
	}
}

.loading-status {
	text-align: center;
	padding: 60rpx 0;
	font-size: 26rpx;
	color: $sh-text-sub;
	.empty-list {
		padding: 100rpx 0;
	}
}
</style>
