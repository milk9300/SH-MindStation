<template>
	<view class="chat-container">
		<!-- 消息列表 -->
		<scroll-view 
			scroll-y 
			class="message-list" 
			:scroll-top="scrollTop"
			:scroll-with-animation="true"
		>
			<view class="scroll-inner">
				<!-- 欢迎语 -->
				<view class="welcome-banner">
					<view class="welcome-icon">🌱</view>
					<text class="welcome-title">你好，我是你的 AI 心理咨询师</text>
					<text class="welcome-desc">在这里可以放心倾诉，我会认真聆听每一句话。所有对话内容严格加密，保障你的隐私安全。</text>
				</view>
				
				<view 
					class="message-item" 
					v-for="(msg, idx) in messages" 
					:key="idx"
					:class="[msg.role, msg.isNew ? 'fade-in-up' : '']"
				>
					<!-- AI 头像 -->
					<view v-if="msg.role === 'ai'" class="avatar ai-avatar">
						<text>SH</text>
					</view>
					
					<view class="message-main">
						<!-- 消息气泡 -->
						<view class="bubble" :class="msg.role">
							<text>{{ msg.content }}</text>
						</view>
						
						<!-- 交互选项 (只在最新的一条 AI 推荐消息后显示) -->
						<view v-if="msg.role === 'ai' && msg.options && msg.options.length && (idx === messages.length - 1)" class="options-container animate-fade-in">
							<view class="options-title">
								<el-icon><Compass /></el-icon>
								<text>你可以试着了解以下内容：</text>
							</view>
							<view class="options-grid">
								<view 
									class="option-chip" 
									v-for="(opt, oi) in msg.options" 
									:key="oi"
									@click="handleOptionClick(opt)"
								>
									<text class="option-name">{{ opt.name }}</text>
									<text class="option-arrow">➔</text>
								</view>
							</view>
						</view>
						
						<!-- 结构化卡片区域 -->
						<view v-if="msg.cards && msg.cards.length" class="cards-area animate-slide-up">
							<block v-for="(card, ci) in msg.cards" :key="ci">
								<TreatmentCard v-if="card.type === 'TREATMENT'" :data="card" />
								<PolicyCard v-else-if="card.type === 'POLICY'" :data="card" />
								<CrisisCard v-else-if="card.type === 'CRISIS'" :data="card" />
								<ArticleCard v-else-if="card.type === 'ARTICLE'" :data="card" />
							</block>
						</view>
					</view>
				</view>
				
				<!-- 加载状态 -->
				<view v-if="isLoading" class="message-item ai fade-in">
					<view class="avatar ai-avatar">SH</view>
					<view class="message-main">
						<view class="bubble ai thinking-bubble">
							<view class="dot-loader">
								<view class="dot"></view>
								<view class="dot"></view>
								<view class="dot"></view>
							</view>
							<text class="thinking-text">SH 正在感知中...</text>
						</view>
					</view>
				</view>
				
				<view style="height: 40rpx;"></view>
			</view>
		</scroll-view>
		
		<!-- 输入区域 -->
		<view class="input-area" :class="{ 'input-focus': isFocused }">
			<view class="input-wrapper">
				<input 
					class="message-input"
					v-model="inputText"
					placeholder="轻声说出你的心事..."
					placeholder-style="color: #A7B6AF"
					:confirm-type="'send'"
					@confirm="sendMessage"
					@focus="isFocused = true"
					@blur="isFocused = false"
				/>
				<view class="send-btn" :class="{ active: inputText.trim() }" @click="sendMessage">
					<text class="btn-text">发送</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
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
const isFocused = ref(false)

// 生成会话 ID 逻辑
const getStoredSession = () => {
	const sid = uni.getStorageSync('active_session_id')
	if (sid) sessionId.value = sid
}

const generateSessionId = () => {
	const sid = 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8)
	sessionId.value = sid
	uni.setStorageSync('active_session_id', sid)
	return sid
}

const scrollToBottom = () => {
	nextTick(() => {
		setTimeout(() => {
			scrollTop.value = scrollTop.value >= 99999 ? scrollTop.value + 1 : 100000
		}, 100)
	})
}

// 核心：处理选项点击 (二阶段交互)
const handleOptionClick = async (option) => {
	if (isLoading.value) return
	
	// 1. 模拟用户发送的一条“隐含”消息（或直接转入加载态）
	messages.value.push({ 
		role: 'user', 
		content: `我想了解：${option.name}`,
		isNew: true 
	})
	scrollToBottom()
	
	isLoading.value = true
	try {
		const data = await request({
			url: '/chat/interact/',
			method: 'POST',
			data: {
				session_id: sessionId.value,
				selected_node_uuid: option.uuid, // 发送 UUID 触发 Stage 2
				content: ''
			}
		})
		
		if (data && data.reply) {
			messages.value.push({
				role: 'ai',
				content: data.reply,
				cards: data.structured_cards || [],
				isNew: true
			})
		}
	} catch (err) {
		console.error('Fetch deep context failed:', err)
	} finally {
		isLoading.value = false
		scrollToBottom()
	}
}

// 发送普通文本消息
const sendMessage = async () => {
	const text = inputText.value.trim()
	if (!text || isLoading.value) return
	
	if (!sessionId.value) generateSessionId()
	
	messages.value.push({ role: 'user', content: text, isNew: true })
	inputText.value = ''
	scrollToBottom()
	
	isLoading.value = true
	try {
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
				options: data.options || [], // 保存 Stage 1 的选项
				cards: data.structured_cards || [],
				isNew: true
			})
		}
	} catch (err) {
		console.error('Chat error:', err)
	} finally {
		isLoading.value = false
		scrollToBottom()
	}
}

onMounted(() => {
	getStoredSession()
})
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
	overflow: hidden;
}

.scroll-inner {
	padding: 40rpx 30rpx;
}

.welcome-banner {
	@include sh-card;
	margin-bottom: 60rpx;
	text-align: center;
	border: 1px solid rgba($sh-primary, 0.1);
	background: linear-gradient(180deg, #FFFFFF 0%, #F4F9F7 100%);
	
	.welcome-icon {
		font-size: 88rpx;
		margin-bottom: 24rpx;
	}
	.welcome-title {
		display: block;
		font-size: 34rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-bottom: 16rpx;
	}
	.welcome-desc {
		display: block;
		font-size: 26rpx;
		color: $sh-text-sub;
		line-height: 1.6;
		padding: 0 20rpx;
		opacity: 0.8;
	}
}

.message-item {
	display: flex;
	margin-bottom: 48rpx;
	align-items: flex-start;
	
	&.user {
		flex-direction: row-reverse;
		.avatar { margin-left: 20rpx; margin-right: 0; }
	}
}

.avatar {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
	font-weight: bold;
	flex-shrink: 0;
}

.ai-avatar {
	background: linear-gradient(135deg, $sh-primary, #6AA285);
	color: #fff;
	margin-right: 20rpx;
	box-shadow: 0 4rpx 12rpx rgba(138, 187, 161, 0.3);
}

.message-main {
	flex: 1;
	max-width: 82%;
	display: flex;
	flex-direction: column;
}

.bubble {
	padding: 28rpx 36rpx;
	border-radius: $sh-radius-md;
	font-size: 30rpx;
	line-height: 1.6;
	word-break: break-all;
	position: relative;
	
	&.ai {
		background: $sh-white;
		color: $sh-text-main;
		border-top-left-radius: 4rpx;
		box-shadow: $sh-shadow;
	}
	&.user {
		background: linear-gradient(135deg, $sh-primary, #76A68D);
		color: #fff;
		border-top-right-radius: 4rpx;
		margin-left: auto;
		box-shadow: 0 6rpx 20rpx rgba(138, 187, 161, 0.2);
	}
}

/* 交互选项样式 */
.options-container {
	margin-top: 24rpx;
	padding: 24rpx;
	background: rgba($sh-primary, 0.05);
	border-radius: $sh-radius-md;
	border: 1px dashed rgba($sh-primary, 0.3);
	
	.options-title {
		display: flex;
		align-items: center;
		gap: 8rpx;
		font-size: 24rpx;
		color: $sh-text-sub;
		margin-bottom: 16rpx;
		font-weight: 500;
	}
}

.options-grid {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
}

.option-chip {
	background: $sh-white;
	border: 1px solid rgba($sh-primary, 0.2);
	padding: 16rpx 28rpx;
	border-radius: 100rpx;
	display: flex;
	align-items: center;
	gap: 12rpx;
	transition: all 0.2s $sh-bezier;
	box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
	
	&:active {
		transform: scale(0.96);
		background: $sh-primary;
		.option-name, .option-arrow { color: #fff; }
	}
	
	.option-name {
		font-size: 26rpx;
		color: $sh-text-main;
		font-weight: 500;
	}
	.option-arrow {
		font-size: 24rpx;
		color: $sh-primary;
	}
}

/* 输入区域升级 */
.input-area {
	padding: 24rpx 40rpx;
	padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
	background: $sh-white;
	box-shadow: 0 -10rpx 40rpx rgba(0,0,0,0.03);
	transition: all 0.3s $sh-bezier;
	
	&.input-focus {
		padding-top: 32rpx;
		box-shadow: 0 -15rpx 50rpx rgba($sh-primary, 0.1);
	}
}

.input-wrapper {
	display: flex;
	align-items: center;
	background: #F0F4F2;
	border-radius: 50rpx;
	padding: 8rpx 8rpx 8rpx 36rpx;
	border: 1px solid transparent;
	transition: all 0.3s;
	
	.message-input {
		flex: 1;
		height: 80rpx;
		font-size: 30rpx;
		color: $sh-text-main;
	}
	
	.send-btn {
		width: 100rpx;
		height: 80rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #D1DED8;
		border-radius: 40rpx;
		margin-left: 20rpx;
		transition: all 0.3s $sh-bezier;
		
		&.active {
			background: $sh-primary;
			width: 140rpx;
			box-shadow: 0 6rpx 16rpx rgba($sh-primary, 0.3);
			.btn-text { color: #fff; font-weight: 600; }
		}
		
		.btn-text {
			font-size: 28rpx;
			color: #fff;
		}
	}
}

/* 动画库 */
.fade-in-up {
	animation: fadeInUp 0.5s $sh-bezier both;
}

@keyframes fadeInUp {
	from { opacity: 0; transform: translateY(30rpx); }
	to { opacity: 1; transform: translateY(0); }
}

.thinking-bubble {
	display: flex;
	align-items: center;
	gap: 16rpx;
	background: $sh-white !important;
	border: 1px solid rgba($sh-primary, 0.15);
	
	.dot-loader {
		display: flex;
		gap: 8rpx;
		.dot {
			width: 12rpx;
			height: 12rpx;
			background: $sh-primary;
			border-radius: 50%;
			animation: bounce 1.4s infinite ease-in-out both;
			&:nth-child(2) { animation-delay: 0.2s; }
			&:nth-child(3) { animation-delay: 0.4s; }
		}
	}
	.thinking-text {
		font-size: 26rpx;
		color: $sh-text-sub;
		font-style: italic;
	}
}

@keyframes bounce {
	0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
	40% { transform: scale(1); opacity: 1; }
}

.animate-fade-in { animation: fadeIn 0.6s ease both; }
.animate-slide-up { animation: slideUp 0.6s $sh-bezier 0.2s both; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }

</style>
