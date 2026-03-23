<template>
	<view class="chat-container">
		<!-- 消息列表 -->
		<scroll-view 
			scroll-y 
			class="message-list" 
			:scroll-top="scrollTop"
			:scroll-with-animation="true"
		>
			<!-- 欢迎语 -->
			<view class="welcome-banner">
				<view class="welcome-icon">🌿</view>
				<text class="welcome-title">你好，我是你的 AI 心理咨询师</text>
				<text class="welcome-desc">在这里可以放心倾诉，我会认真聆听每一句话。所有对话内容严格保密。</text>
			</view>
			
			<view 
				class="message-item" 
				v-for="(msg, idx) in messages" 
				:key="idx"
				:class="msg.role"
			>
				<!-- AI 头像 -->
				<view v-if="msg.role === 'ai'" class="avatar ai-avatar">🌱</view>
				
				<view class="message-main">
					<!-- 消息气泡 -->
					<view class="bubble" :class="msg.role">
						<text>{{ msg.content }}</text>
					</view>
					
					<!-- 结构化卡片分发 -->
					<view v-if="msg.cards && msg.cards.length" class="cards-area">
						<block v-for="(card, ci) in msg.cards" :key="ci">
							<TreatmentCard v-if="card.type === 'TREATMENT'" :data="card" />
							<PolicyCard v-else-if="card.type === 'POLICY'" :data="card" />
							<CrisisCard v-else-if="card.type === 'CRISIS'" :data="card" />
							<ArticleCard v-else-if="card.type === 'ARTICLE'" :data="card" />
						</block>
					</view>
				</view>
			</view>
			
			<!-- “思考中” 状态优化 -->
			<view v-if="isLoading" class="message-item ai">
				<view class="avatar ai-avatar">🌱</view>
				<view class="message-main">
					<view class="bubble ai thinking-bubble">
						<view class="dot-loader">
							<view class="dot"></view>
							<view class="dot"></view>
							<view class="dot"></view>
						</view>
						<text class="thinking-text">SH 正在思考中...</text>
					</view>
				</view>
			</view>
		</scroll-view>
		
		<!-- 输入区域 -->
		<view class="input-area">
			<input 
				class="message-input"
				v-model="inputText"
				placeholder="轻声说出你的心事..."
				:confirm-type="'send'"
				@confirm="sendMessage"
			/>
			<view class="send-btn" :class="{ active: inputText.trim() }" @click="sendMessage">
				<text>发送</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import request from '@/utils/request.js'
import TreatmentCard from '@/components/cards/TreatmentCard.vue'
import PolicyCard from '@/components/cards/PolicyCard.vue'
import CrisisCard from '@/components/cards/CrisisCard.vue'
import ArticleCard from '@/components/cards/ArticleCard.vue'

const inputText = ref('')
const messages = ref([])
const isLoading = ref(false)
const scrollTop = ref(0)
const sessionId = ref('')

// 生成简陋但唯一的会话 ID
const generateSessionId = () => {
	return 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8)
}

// 滚动到底部
const scrollToBottom = () => {
	nextTick(() => {
		scrollTop.value = scrollTop.value === 99999 ? 100000 : 99999
	})
}

// 发送消息
const sendMessage = async () => {
	const text = inputText.value.trim()
	if (!text || isLoading.value) return
	
	// 初始化会话
	if (!sessionId.value) {
		sessionId.value = generateSessionId()
	}
	
	// 1. 追加用户消息到列表
	messages.value.push({ role: 'user', content: text })
	inputText.value = ''
	scrollToBottom()
	
	// 2. 显示加载状态
	isLoading.value = true
	
	try {
		// 3. 调用后端 RAG 接口 (使用封装好的 request)
		const data = await request({
			url: '/chat/interact/',
			method: 'POST',
			data: {
				session_id: sessionId.value,
				content: text
			}
		})
		
		if (data && data.reply) {
			messages.value.push({
				role: 'ai',
				content: data.reply,
				cards: data.structured_cards || []
			})
		} else {
			messages.value.push({
				role: 'ai',
				content: '抱歉，我暂时无法回复，请稍后再试。'
			})
		}
	} catch (err) {
		// request 工具会自动处理 401 报错，此处仅捕获网络或其他异常
		console.error('Chat error:', err)
	} finally {
		isLoading.value = false
		scrollToBottom()
	}
}
</script>

<style lang="scss">
.chat-container {
	display: flex;
	flex-direction: column;
	height: 100vh;
	background-color: $sh-bg;
}

.message-list {
	flex: 1;
	height: 100%;
	background-color: transparent;
	padding: 0 30rpx;
	box-sizing: border-box;
}

.welcome-banner {
	@include sh-card;
	margin: 20rpx 10rpx 50rpx;
	text-align: center;
	padding: 60rpx 40rpx;
	background: linear-gradient(to bottom, #ffffff, #f9fdfb);
	
	.welcome-icon {
		font-size: 80rpx;
		margin-bottom: 30rpx;
		display: block;
	}
	.welcome-title {
		display: block;
		font-size: 34rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-bottom: 20rpx;
	}
	.welcome-desc {
		display: block;
		font-size: 26rpx;
		color: $sh-text-sub;
		line-height: 1.6;
		padding: 0 20rpx;
	}
}

.message-item {
	display: flex;
	margin-bottom: 30rpx;
	align-items: flex-start;
	
	&.user {
		flex-direction: row-reverse;
	}
}

.avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 36rpx;
	flex-shrink: 0;
}
.ai-avatar {
	background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
	margin-right: 16rpx;
}

.message-main {
	flex: 1;
	max-width: 80%;
	display: flex;
	flex-direction: column;
}

.bubble {
	padding: 24rpx 30rpx;
	border-radius: 28rpx;
	font-size: 28rpx;
	line-height: 1.6;
	white-space: pre-wrap;
	width: fit-content;
	max-width: 100%;
	
	&.ai {
		background: $sh-white;
		color: $sh-text-main;
		border-top-left-radius: 6rpx;
		box-shadow: $sh-shadow;
	}
	&.user {
		background: $sh-primary;
		color: #fff;
		border-top-right-radius: 6rpx;
		margin-left: auto;
	}
}

// 思考中动画增强
.thinking-bubble {
	display: flex;
	align-items: center;
	gap: 16rpx;
	background: linear-gradient(to right, #ffffff, #f9fdfb) !important;
	border: 1px solid rgba($sh-primary, 0.1);
	
	.dot-loader {
		display: flex;
		align-items: center;
		gap: 8rpx;
		.dot {
			width: 10rpx;
			height: 10rpx;
			background: $sh-primary;
			border-radius: 50%;
			animation: bounce 1.4s infinite ease-in-out both;
			&:nth-child(1) { animation-delay: -0.32s; }
			&:nth-child(2) { animation-delay: -0.16s; }
		}
	}
	
	.thinking-text {
		font-size: 24rpx;
		color: $sh-text-sub;
		font-style: italic;
	}
}

@keyframes bounce {
	0%, 80%, 100% { transform: scale(0.6); opacity: 0.3; }
	40% { transform: scale(1.2); opacity: 1; }
}

// 结构化卡片区域
.cards-area {
	width: 100%;
	margin-top: 16rpx;
}

// 输入区域
.input-area {
	display: flex;
	align-items: center;
	padding: 20rpx 30rpx;
	padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
	background: $sh-white;
	box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.03);
}
.message-input {
	flex: 1;
	height: 76rpx;
	background: $sh-bg;
	border-radius: 38rpx;
	padding: 0 30rpx;
	font-size: 28rpx;
	color: $sh-text-main;
}
.send-btn {
	margin-left: 16rpx;
	padding: 16rpx 36rpx;
	background: $sh-border;
	border-radius: 38rpx;
	font-size: 28rpx;
	color: $sh-text-sub;
	transition: all 0.3s $sh-bezier;
	
	&.active {
		background: $sh-primary;
		color: #fff;
	}
}
</style>
