<template>
	<view class="welcome-container" v-if="show">
		<view class="welcome-header">
			<text class="greeting">你好，{{ nickname }}</text>
			<text class="sub-text">今天有什么想跟我聊聊的吗？</text>
		</view>
		
		<view class="guidance-grid">
			<view 
				v-for="(q, index) in guidanceQuestions" 
				:key="index"
				class="guidance-card"
				@click="$emit('select-guidance', q.text)"
			>
				<text class="card-text">{{ q.text }}</text>
				<text class="card-arrow">➔</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
	show: Boolean,
	nickname: String,
	guidanceQuestions: {
		type: Array,
		default: () => []
	}
})

const emit = defineEmits(['select-guidance'])
</script>

<style lang="scss" scoped>
.welcome-container {
	padding: 60rpx 40rpx 40rpx;
	.welcome-header {
		margin-bottom: 60rpx;
		.greeting { display: block; font-size: 52rpx; font-weight: 800; background: linear-gradient(90deg, $sh-primary, #4285F4, #34A853); -webkit-background-clip: text; background-clip: text; color: transparent; margin-bottom: 20rpx; }
		.sub-text { font-size: 38rpx; color: #5f6368; line-height: 1.4; font-weight: 500; }
	}
	.guidance-grid { display: flex; flex-direction: column; gap: 20rpx; }
	.guidance-card {
		background: #fff; border: 1rpx solid #efefef; padding: 32rpx; border-radius: 24rpx; display: flex; align-items: center; gap: 24rpx; transition: all 0.2s; box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.02);
		&:active { background: #f8f9fa; transform: scale(0.98); }
		.card-icon { font-size: 40rpx; }
		.card-text { flex: 1; font-size: 28rpx; color: #3c4043; font-weight: 500; }
		.card-arrow { font-size: 24rpx; color: #dadce0; }
	}
}
</style>
