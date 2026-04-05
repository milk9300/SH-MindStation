<template>
	<scroll-view 
		scroll-y 
		class="message-list" 
		:scroll-top="scrollTop"
		:scroll-with-animation="true"
		:style="{ paddingTop: headerHeight + 'px' }"
	>
		<view class="scroll-inner">
			<!-- 欢迎页插槽或直接显示 -->
			<slot name="welcome"></slot>
			
			<!-- 消息流 -->
			<view 
				v-for="(msg, idx) in messages" 
				:key="msg.id || idx"
				class="message-item"
				:class="[msg.role, msg.isNew ? 'fade-in-up' : '']"
			>
				<view v-if="msg.role === 'ai'" class="avatar ai-avatar">
					<text>SH</text>
				</view>
				
				<view class="message-main">
					<view class="bubble" :class="msg.role">
						<text>{{ msg.content }}</text>
					</view>
					
					<!-- 选项渲染 (只在最后一条 AI 消息显示) -->
					<view v-if="msg.role === 'ai' && msg.options && msg.options.length && (idx === messages.length - 1)" class="options-container animate-fade-in">
						<view class="options-grid">
							<view 
								v-for="(opt, oi) in msg.options" 
								:key="oi"
								class="option-chip"
								@click="$emit('select-option', opt)"
							>
								<text class="option-name">{{ opt.name }}</text>
								<text class="option-arrow">➔</text>
							</view>
						</view>
					</view>
					
					<!-- 结构化卡片渲染 -->
					<view v-if="(msg.cards && msg.cards.length) || msg.suggested_assessment" class="cards-area animate-slide-up">
						<block v-for="(card, ci) in msg.cards" :key="ci">
							<TreatmentCard v-if="card.type === 'TREATMENT'" :data="card" />
							<PolicyCard v-else-if="card.type === 'POLICY'" :data="card" />
							<CrisisCard v-else-if="card.type === 'CRISIS'" :data="card" />
							<ArticleCard v-else-if="card.type === 'ARTICLE'" :data="card" />
						</block>
						
						<!-- [新增] 测评建议卡片 -->
						<AssessmentCard v-if="msg.suggested_assessment" :data="msg.suggested_assessment" :msgId="msg.id" />
						
						<!-- 更多建议入口 -->
						<view 
							v-if="msg.knowledge_base_uuid" 
							class="more-suggestions-btn"
							@click="goToKnowledgeBase(msg.knowledge_base_uuid)"
						>
							<text>查看更多建议</text>
							<text class="btn-icon">➜</text>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 加载中动画 -->
			<view v-if="loading" class="message-item ai fade-in">
				<view class="avatar ai-avatar">SH</view>
				<view class="message-main">
					<view class="bubble ai thinking-bubble">
						<view class="dot-loader">
							<view class="dot"></view><view class="dot"></view><view class="dot"></view>
						</view>
						<text class="thinking-text">SH 正在思考...</text>
					</view>
				</view>
			</view>
			
			<!-- 底部给 fixed 输入框留出的占位空间 -->
			<view class="input-placeholder"></view>
		</view>
	</scroll-view>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import TreatmentCard from '@/components/cards/TreatmentCard.vue'
import PolicyCard from '@/components/cards/PolicyCard.vue'
import CrisisCard from '@/components/cards/CrisisCard.vue'
import ArticleCard from '@/components/cards/ArticleCard.vue'
import AssessmentCard from '@/components/cards/AssessmentCard.vue'

const props = defineProps({
	messages: {
		type: Array,
		default: () => []
	},
	loading: Boolean,
	scrollTop: {
		type: Number,
		default: 0
	},
	headerHeight: {
		type: Number,
		default: 64
	}
})

const emit = defineEmits(['select-option'])

const goToKnowledgeBase = (uuid) => {
	uni.navigateTo({
		url: `/pages/knowledge/detail?uuid=${uuid}`
	})
}
</script>

<style lang="scss" scoped>
.message-list {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: #F7FAF9;
	z-index: 1;
	box-sizing: border-box;
}

.scroll-inner { padding: 20rpx 30rpx; }

/* 为 fixed 定位的输入框预留底部空间 */
.input-placeholder { height: 200rpx; }

.message-item { display: flex; margin-bottom: 48rpx; &.user { flex-direction: row-reverse; } }
.avatar { width: 80rpx; height: 80rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ai-avatar { background: linear-gradient(135deg, $sh-primary, #6AA285); color: #fff; margin-right: 20rpx; font-weight: bold; }
.bubble { padding: 28rpx 36rpx; border-radius: $sh-radius-md; font-size: 30rpx; line-height: 1.6; word-break: break-all;
	&.ai { background: #fff; border-top-left-radius: 4rpx; box-shadow: 0 4rpx 15rpx rgba(0,0,0,0.04); color: $sh-text-main; }
	&.user { background: $sh-primary; color: #fff; border-top-right-radius: 4rpx; margin-left: auto; }
}

.options-container { margin-top: 24rpx; }
.options-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.option-chip {
	background: #fff; border: 1px solid rgba($sh-primary, 0.2); padding: 18rpx 32rpx; border-radius: 100rpx; display: flex; align-items: center; gap: 12rpx;
	.option-name { font-size: 26rpx; color: $sh-text-main; } .option-arrow { font-size: 24rpx; color: $sh-primary; }
}

.thinking-bubble { display: flex; align-items: center; gap: 16rpx; .dot-loader { display: flex; gap: 8rpx; .dot { width: 12rpx; height: 12rpx; background: $sh-primary; border-radius: 50%; opacity: 0.4; } } .thinking-text { font-size: 26rpx; color: $sh-text-sub; } }

.cards-area { 
	margin-top: 24rpx; display: flex; flex-direction: column; gap: 20rpx; 
}

.animate-slide-up { animation: slideUp 0.5s ease-out both; }
@keyframes slideUp { from { opacity: 0; transform: translateY(30rpx); } to { opacity: 1; transform: translateY(0); } }

.more-suggestions-btn { 
	margin-top: 32rpx; background: rgba($sh-primary, 0.04); border: 1px dashed rgba($sh-primary, 0.3); padding: 24rpx; border-radius: $sh-radius-md; display: flex; align-items: center; justify-content: center; gap: 12rpx; color: $sh-primary; font-size: 28rpx; font-weight: 500; transition: all 0.2s;
	&:active { background: rgba($sh-primary, 0.1); transform: scale(0.98); }
	.btn-icon { font-size: 24rpx; }
}

.fade-in-up { animation: fadeInUp 0.4s ease-out both; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
</style>
