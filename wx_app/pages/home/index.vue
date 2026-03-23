<template>
	<view class="container">
		<view class="status-bar"></view>
		<view class="header">
			<text class="greeting">你好，{{ studentName }}</text>
			<text class="title">在这个空间，你可以安心倾诉</text>
		</view>
		
		<view class="chat-entrance" @click="goToChat">
			<view class="entrance-content">
				<text class="entrance-title">开启心灵对话</text>
				<text class="entrance-desc">AI 咨询师 24小时为你守护</text>
			</view>
			<text class="entrance-icon">🍀</text>
		</view>
		
		<view class="section-title">每日心情</view>
		<view class="mood-card" @click="goToMood">
			<view class="mood-inner" v-if="todayMood">
				<view class="mood-display">
					<text class="emoji">{{ todayMood.emoji }}</text>
					<text class="remark">{{ todayMood.note || '保持好心情' }}</text>
				</view>
				<view class="mood-btn mini">已记录</view>
			</view>
			<block v-else>
				<text>记录下此刻的感觉吧...</text>
				<view class="mood-btn">去记录</view>
			</block>
		</view>
		
		<view class="section-title">为您推荐</view>
		<scroll-view scroll-x class="article-scroll">
			<view 
				class="article-item" 
				v-for="item in recommendations" 
				:key="item.id"
				@click="goToArticle(item)"
			>
				<image 
					class="article-img" 
					:src="item.cover_image" 
					mode="aspectFill" 
					v-if="item.cover_image"
				/>
				<view class="article-cover" v-else></view>
				<text class="article-title">{{ item.title }}</text>
			</view>
		</scroll-view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const studentName = ref('匿名同学')
const todayMood = ref(null)
const recommendations = ref([])

onMounted(() => {
	const userStr = uni.getStorageSync('student_user')
	if (userStr) {
		try {
			const user = JSON.parse(userStr)
			studentName.value = user.nickname || '同学'
		} catch (e) {}
	}
	
	fetchTodayMood()
	fetchRecommendations()
})

const fetchTodayMood = async () => {
	try {
		const res = await request({
			url: '/moods/',
			method: 'GET'
		})
		if (res && res.length > 0) {
			const latest = res[0]
			const today = new Date().toISOString().split('T')[0]
			// 兼容不同格式的日期字符串
			const logDate = latest.created_at.split('T')[0]
			if (today === logDate) {
				// 转换为展示用的对象
				const emojis = { 1: '😢', 2: '😟', 3: '😐', 4: '😊', 5: '🤩' }
				todayMood.value = {
					emoji: emojis[latest.mood_level] || '😐',
					note: latest.note
				}
			}
		}
	} catch (e) {}
}

const fetchRecommendations = async () => {
	try {
		const res = await request({
			url: '/articles/',
			method: 'GET'
		})
		// 取前 3 篇作为推荐
		recommendations.value = Array.isArray(res) ? res.slice(0, 3) : []
	} catch (e) {}
}

const goToChat = () => {
	uni.switchTab({ url: '/pages/chat/index' })
}
const goToMood = () => {
	uni.navigateTo({ url: '/pages/mood/index' })
}
const goToArticle = (article) => {
	uni.navigateTo({
		url: `/pages/discovery/article-detail?id=${article.id}`
	})
}
</script>

<style lang="scss">
.container {
	padding: 40rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.status-bar {
	height: var(--status-bar-height);
}
.header {
	margin-top: 40rpx;
	margin-bottom: 60rpx;
	.greeting {
		font-size: 28rpx;
		color: $sh-text-sub;
		display: block;
	}
	.title {
		font-size: 44rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-top: 10rpx;
		display: block;
	}
}
.chat-entrance {
	@include sh-card;
	background: linear-gradient(135deg, $sh-primary, #9ED4B7);
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 50rpx 40rpx;
	margin-bottom: 40rpx;
	.entrance-title {
		color: #fff;
		font-size: 36rpx;
		font-weight: 600;
		display: block;
	}
	.entrance-desc {
		color: rgba(255, 255, 255, 0.8);
		font-size: 24rpx;
		margin-top: 10rpx;
		display: block;
	}
	.entrance-icon {
		font-size: 80rpx;
	}
}
.mood-card {
	@include sh-card;
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40rpx;
	color: $sh-text-sub;
	font-size: 28rpx;
	.mood-inner {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		.mood-display {
			display: flex;
			align-items: center;
			.emoji {
				font-size: 48rpx;
				margin-right: 20rpx;
			}
			.remark {
				font-size: 30rpx;
				color: $sh-text-main;
				font-weight: 500;
			}
		}
	}
	.mood-btn {
		background: $sh-border;
		color: $sh-text-main;
		padding: 10rpx 30rpx;
		border-radius: 30rpx;
		font-size: 24rpx;
		&.mini {
			background: rgba($sh-primary, 0.1);
			color: $sh-primary;
		}
	}
}
.section-title {
	font-size: 32rpx;
	font-weight: 600;
	color: $sh-text-main;
	margin-bottom: 30rpx;
	padding-left: 10rpx;
}
.article-scroll {
	white-space: nowrap;
	padding-bottom: 20rpx;
	.article-item {
		display: inline-block;
		width: 400rpx;
		margin-right: 30rpx;
		vertical-align: top;
		.article-img, .article-cover {
			width: 100%;
			height: 240rpx;
			background: #eee;
			border-radius: $sh-radius-md;
			margin-bottom: 15rpx;
		}
		.article-title {
			font-size: 28rpx;
			color: $sh-text-main;
			white-space: normal;
			display: -webkit-box;
			-webkit-box-orient: vertical;
			-webkit-line-clamp: 2;
			line-clamp: 2;
			overflow: hidden;
			height: 80rpx;
			line-height: 40rpx;
		}
	}
}
</style>
