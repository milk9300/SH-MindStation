<template>
	<view class="container">
		<view class="section-header">
			<text class="section-title">📋 心理测评列表</text>
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
					<text class="scale-desc">{{ scale.question_count || 0 }} 道题 · 约 {{ Math.ceil((scale.question_count || 0) * 0.5) }} 分钟</text>
				</view>
				<view class="scale-arrow">›</view>
			</view>
		</view>
		
		<view class="loading-status" v-if="loading || !hasMore">
			<text v-if="loading">正在加载测评量表...</text>
			<text v-else-if="!hasMore && scales.length > 0">已加载全部测评</text>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onReachBottom } from '@dcloudio/uni-app'
import request from '@/utils/request.js'

const scales = ref([])
const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)

const fetchData = async (isRefresh = false) => {
	if (loading.value) return
	if (isRefresh) {
		page.value = 1
		scales.value = []
		hasMore.value = true
	}
	
	loading.value = true
	try {
		const res = await request({ 
			url: `/scales/?page=${page.value}`, 
			method: 'GET' 
		})
		const newItems = res.results || []
		scales.value.push(...newItems)
		
		hasMore.value = !!res.next
		if (hasMore.value) {
			page.value++
		}
	} catch (err) {
		console.error('Fetch scale data error:', err)
	} finally {
		loading.value = false
	}
}

const startAssessment = (scale) => {
	uni.navigateTo({
		url: `/pages/discovery/assessment?id=${scale.id}`
	})
}

onMounted(() => {
	fetchData(true)
})

onReachBottom(() => {
	if (!loading.value && hasMore.value) {
		fetchData()
	}
})
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.section-header {
	margin-bottom: 30rpx;
	padding: 10rpx 0;
}
.section-title {
	font-size: 34rpx;
	font-weight: 600;
	color: $sh-text-main;
}

// 量表卡片
.scale-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}
.scale-card {
	@include sh-card;
	display: flex;
	align-items: center;
	padding: 32rpx;
	background: #fff;
	.scale-icon {
		font-size: 52rpx;
		margin-right: 24rpx;
	}
	.scale-body {
		flex: 1;
	}
	.scale-name {
		display: block;
		font-size: 30rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-bottom: 10rpx;
	}
	.scale-desc {
		display: block;
		font-size: 24rpx;
		color: $sh-text-sub;
	}
	.scale-arrow {
		font-size: 40rpx;
		color: $sh-border;
		margin-left: 10rpx;
	}
}

.loading-status {
	text-align: center;
	padding: 50rpx 0;
	color: $sh-text-sub;
	font-size: 24rpx;
}
</style>
