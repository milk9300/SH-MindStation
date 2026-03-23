<template>
	<view class="article-container">
		<view class="article-header" v-if="article">
			<text class="title">{{ article.title }}</text>
			<view class="meta">
				<text class="author">{{ article.author }}</text>
				<text class="dot">·</text>
				<text class="date">{{ formatDate(article.created_at) }}</text>
			</view>
		</view>

		<view class="content-scroll">
			<view class="article-content" v-if="article">
				<!-- 用 text 渲染内容，实际项目中可使用 mp-html 等插件支持富文本 -->
				<text v-if="article.content" class="text-p">{{ article.content }}</text>
			</view>
		</view>

		<view class="footer-action" v-if="article">
			<view class="action-btn" :class="{ active: isFavorite }" @click="toggleFavorite">
				<text class="icon">{{ isFavorite ? '❤️' : '🤍' }}</text>
				<text class="label">{{ isFavorite ? '已收藏' : '收藏' }}</text>
			</view>
			<view class="action-btn share" @click="doShare">
				<text class="icon">↗️</text>
				<text class="label">转发</text>
			</view>
		</view>

		<view v-if="loading" class="loading-state">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const id = ref('')
const article = ref(null)
const loading = ref(false)
const isFavorite = ref(false)

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	return dateStr.substring(0, 10)
}

const fetchData = async () => {
	loading.value = true
	try {
		const res = await request({
			url: `/articles/${id.value}/`,
			method: 'GET'
		})
		article.value = res
		// 检查是否已收藏
		checkFavorite()
	} catch (err) {
		console.error('Fetch article error:', err)
	} finally {
		loading.value = false
	}
}

const checkFavorite = async () => {
	try {
		const favorites = await request({
			url: '/favorites/',
			method: 'GET',
			data: { target_type: 'article', target_id: id.value }
		})
		// 如果返回的列表里有这条，说明已收藏 (Backend filters by user/type/id if needed)
		// 简单起见，如果后端没做过滤，我们前端 Filter 一下
		isFavorite.value = favorites.some(f => f.target_id === id.value && f.target_type === 'article')
	} catch (e) {}
}

const toggleFavorite = async () => {
	try {
		if (isFavorite.value) {
			// 取消收藏 (通常 DELETE 需要 ID，或者自定义 Action)
			// 这里我们为了简单，假设后端支持 POST 同一个数据切换状态，或者我们先查到收藏记录 ID
			const favorites = await request({ url: '/favorites/', method: 'GET' })
			const fav = favorites.find(f => f.target_id === id.value && f.target_type === 'article')
			if (fav) {
				await request({ url: `/favorites/${fav.id}/`, method: 'DELETE' })
				isFavorite.value = false
				uni.showToast({ title: '已取消', icon: 'none' })
			}
		} else {
			// 添加收藏
			await request({
				url: '/favorites/',
				method: 'POST',
				data: {
					target_type: 'article',
					target_id: id.value,
					target_title: article.value.title
				}
			})
			isFavorite.value = true
			uni.showToast({ title: '已收藏' })
		}
	} catch (err) {
		console.error('Toggle favorite error:', err)
	}
}

const doShare = () => {
	uni.showToast({ title: '点击右上角转发给好友吧', icon: 'none' })
}

onMounted(() => {
	// 获取 URL 参数 id
	const pages = getCurrentPages()
	const curPage = pages[pages.length - 1]
	if (curPage && curPage.options && curPage.options.id) {
		id.value = curPage.options.id
		fetchData()
	}
})
</script>

<style lang="scss">
.article-container {
	background: #fff;
	min-height: 100vh;
	display: flex;
	flex-direction: column;
	padding-bottom: 120rpx;
}
.article-header {
	padding: 40rpx 40rpx 20rpx;
	.title {
		font-size: 44rpx;
		font-weight: 600;
		color: $sh-text-main;
		line-height: 1.4;
		margin-bottom: 24rpx;
		display: block;
	}
	.meta {
		display: flex;
		align-items: center;
		font-size: 26rpx;
		color: $sh-text-sub;
		.author {
			color: $sh-primary;
			font-weight: 500;
		}
		.dot {
			margin: 0 12rpx;
		}
	}
}
.content-scroll {
	flex: 1;
	padding: 20rpx 40rpx;
}
.article-content {
	line-height: 1.8;
	font-size: 30rpx;
	color: $sh-text-main;
	.text-p {
		white-space: pre-wrap;
		word-break: break-all;
	}
}
.footer-action {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 100rpx;
	background: #fff;
	border-top: 1rpx solid $sh-border;
	display: flex;
	align-items: center;
	padding: 0 40rpx;
	padding-bottom: env(safe-area-inset-bottom);
	z-index: 100;
	.action-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		height: 80rpx;
		.icon {
			font-size: 36rpx;
			margin-right: 12rpx;
		}
		.label {
			font-size: 28rpx;
			color: $sh-text-main;
		}
		&.active {
			.label {
				color: $sh-primary;
				font-weight: 600;
			}
		}
	}
}
.loading-state {
	padding: 100rpx;
	text-align: center;
	color: $sh-text-sub;
}
</style>
