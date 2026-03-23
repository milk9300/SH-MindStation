<template>
	<view class="container">
		<view class="header-card">
			<text class="header-title">今天心情怎么样？</text>
			<text class="header-desc">选择一个最符合此刻感受的表情</text>
		</view>
		
		<view class="mood-selector">
			<view 
				class="mood-option" 
				v-for="(m, idx) in moodOptions" 
				:key="idx"
				:class="{ selected: selectedMood === m.level }"
				@click="selectedMood = m.level"
			>
				<text class="mood-emoji">{{ m.emoji }}</text>
				<text class="mood-label">{{ m.label }}</text>
			</view>
		</view>
		
		<view class="note-area">
			<textarea 
				class="note-input"
				v-model="note"
				placeholder="想记录点什么吗...（选填）"
				maxlength="500"
				:auto-height="true"
			/>
		</view>
		
		<view class="submit-btn" :class="{ active: selectedMood > 0 }" @click="submitMood">
			<text>记录心情</text>
		</view>
		
		<view class="history-section">
			<text class="section-title">最近 7 天</text>
			<view class="history-list">
				<view class="history-item" v-for="(log, idx) in recentLogs" :key="idx">
					<text class="history-date">{{ log.created_at }}</text>
					<text class="history-emoji">{{ getMoodEmoji(log.mood_level) }}</text>
					<text class="history-note" v-if="log.note">{{ log.note }}</text>
				</view>
				<view v-if="!recentLogs.length" class="empty-tip">
					<text>暂无记录，现在就开始打卡吧 ✨</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const moodOptions = [
	{ level: 1, emoji: '😢', label: '很差' },
	{ level: 2, emoji: '😟', label: '低落' },
	{ level: 3, emoji: '😐', label: '一般' },
	{ level: 4, emoji: '😊', label: '不错' },
	{ level: 5, emoji: '🤩', label: '超棒' }
]

const selectedMood = ref(0)
const note = ref('')
const recentLogs = ref([])

const getMoodEmoji = (level) => {
	const found = moodOptions.find(m => m.level === level)
	return found ? found.emoji : '😐'
}

const fetchLogs = async () => {
	try {
		const res = await request({
			url: '/moods/',
			method: 'GET'
		})
		recentLogs.value = (res || []).slice(0, 7)
	} catch (err) {
		console.error('Fetch mood logs error:', err)
	}
}

const submitMood = async () => {
	if (selectedMood.value === 0) return
	try {
		await request({
			url: '/moods/',
			method: 'POST',
			data: {
				mood_level: selectedMood.value,
				mood_tag: moodOptions.find(m => m.level === selectedMood.value)?.label || '',
				note: note.value
			}
		})
		uni.showToast({ title: '打卡成功 🌟', icon: 'none' })
		selectedMood.value = 0
		note.value = ''
		fetchLogs()
	} catch (err) {
		console.error('Submit mood error:', err)
	}
}

onMounted(() => {
	fetchLogs()
})
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.header-card {
	text-align: center;
	padding: 50rpx 30rpx 30rpx;
	.header-title {
		display: block;
		font-size: 40rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-bottom: 12rpx;
	}
	.header-desc {
		display: block;
		font-size: 26rpx;
		color: $sh-text-sub;
	}
}
.mood-selector {
	display: flex;
	justify-content: space-around;
	padding: 40rpx 20rpx;
}
.mood-option {
	text-align: center;
	padding: 20rpx;
	border-radius: $sh-radius-md;
	transition: all 0.3s $sh-bezier;
	.mood-emoji {
		display: block;
		font-size: 56rpx;
		margin-bottom: 10rpx;
	}
	.mood-label {
		display: block;
		font-size: 22rpx;
		color: $sh-text-sub;
	}
	&.selected {
		background: rgba($sh-primary, 0.15);
		transform: scale(1.15);
		.mood-label {
			color: $sh-primary;
			font-weight: 600;
		}
	}
}
.note-area {
	@include sh-card;
	margin-bottom: 30rpx;
}
.note-input {
	width: 100%;
	min-height: 120rpx;
	font-size: 28rpx;
	color: $sh-text-main;
	line-height: 1.6;
}
.submit-btn {
	text-align: center;
	padding: 26rpx;
	border-radius: $sh-radius-lg;
	background: $sh-border;
	color: $sh-text-sub;
	font-size: 30rpx;
	font-weight: 500;
	margin-bottom: 50rpx;
	transition: all 0.3s $sh-bezier;
	&.active {
		background: $sh-primary;
		color: #fff;
	}
}
.history-section {
	margin-top: 20rpx;
}
.section-title {
	font-size: 30rpx;
	font-weight: 600;
	color: $sh-text-main;
	margin-bottom: 24rpx;
}
.history-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}
.history-item {
	@include sh-card;
	display: flex;
	align-items: center;
	padding: 24rpx;
	.history-date {
		font-size: 24rpx;
		color: $sh-text-sub;
		margin-right: 20rpx;
		min-width: 140rpx;
	}
	.history-emoji {
		font-size: 40rpx;
		margin-right: 20rpx;
	}
	.history-note {
		flex: 1;
		font-size: 24rpx;
		color: $sh-text-main;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
}
.empty-tip {
	text-align: center;
	padding: 60rpx;
	color: $sh-text-sub;
	font-size: 26rpx;
}
</style>
