<template>
	<view class="container">
		<view class="record-list" v-if="records.length > 0">
			<view class="record-card" v-for="item in records" :key="item.id">
				<view class="record-header">
					<text class="scale-name">{{ item.scale_name }}</text>
					<text class="record-date">{{ formatDate(item.created_at) }}</text>
				</view>
				<view class="record-body">
					<view class="score-info">
						<text class="label">得分</text>
						<text class="value">{{ item.total_score }}</text>
					</view>
					<view class="level-info">
						<text class="label">测评结果</text>
						<text class="value highlight">{{ item.result_level }}</text>
					</view>
				</view>
			</view>
		</view>

		<view class="empty-state" v-else-if="!loading">
			<view class="icon">📦</view>
			<text>暂无测评记录</text>
			<view class="go-btn" @click="goToDiscovery">去试试测评</view>
		</view>

		<view v-if="loading" class="loading-state">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const records = ref([])
const loading = ref(false)

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	return dateStr.substring(0, 16).replace('T', ' ')
}

const fetchRecords = async () => {
	loading.value = true
	try {
		const res = await request({
			url: '/assessments/',
			method: 'GET'
		})
		records.value = Array.isArray(res) ? res : []
	} catch (err) {
		console.error('Fetch records error:', err)
	} finally {
		loading.value = false
	}
}

const goToDiscovery = () => {
	uni.switchTab({ url: '/pages/discovery/index' })
}

onMounted(() => {
	fetchRecords()
})
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.record-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}
.record-card {
	@include sh-card;
	padding: 30rpx;
}
.record-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
	padding-bottom: 20rpx;
	border-bottom: 1rpx solid #f0f0f0;
	.scale-name {
		font-size: 30rpx;
		font-weight: 600;
		color: $sh-text-main;
	}
	.record-date {
		font-size: 22rpx;
		color: $sh-text-sub;
	}
}
.record-body {
	display: flex;
	justify-content: space-around;
	.score-info, .level-info {
		display: flex;
		flex-direction: column;
		align-items: center;
		.label {
			font-size: 22rpx;
			color: $sh-text-sub;
			margin-bottom: 8rpx;
		}
		.value {
			font-size: 32rpx;
			font-weight: 500;
			color: $sh-text-main;
		}
		.highlight {
			color: $sh-primary;
			font-weight: 600;
		}
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
