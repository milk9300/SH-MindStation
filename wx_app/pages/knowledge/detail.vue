<template>
	<view class="knowledge-detail">
		<view class="kb-header">
			<view class="back-home-wrap" @click="goHome">
				<text class="icon">🏠</text>
				<text>发现厅</text>
			</view>
			<view class="header-content" v-if="knowledge">
				<text class="problem-name">{{ knowledge.problem_name || knowledge.名称 }}</text>
				<view class="meta-row">
					<view class="risk-badge" :class="riskLevelClass">
						{{ riskLevelText }}
					</view>
					<text class="problem-desc" v-if="knowledge.description">{{ knowledge.description }}</text>
				</view>
			</view>
		</view>

		<scroll-view scroll-y class="content-scroll" v-if="knowledge">
			<view class="scroll-inner">
				<!-- Scenario Analysis -->
				<view class="section-card animate-fade-in" v-if="hasEvents">
					<view class="section-title">
						<text class="icon">📅</text>
						<text>场景化诱发因素</text>
					</view>
					<view class="scenario-content">
						<view class="event-item" v-for="(ev, ei) in knowledge.current_events" :key="ei">
							<text class="event-time">[{{ ev.month }}月相关]</text>
							<text class="event-desc">{{ ev.name }}: {{ ev.description }}</text>
						</view>
						<view class="symptom-tags" v-if="knowledge.symptoms && knowledge.symptoms.length">
							<text class="tag" v-for="(s, si) in knowledge.symptoms" :key="si">{{ s.name || s }}</text>
						</view>
					</view>
				</view>

				<!-- Treatments -->
				<view class="section-card animate-fade-in" v-if="knowledge.treatments && knowledge.treatments.length">
					<view class="section-title">
						<text class="icon">💡</text>
						<text>应对方案建议</text>
					</view>
					<view class="treatment-list">
						<view 
							class="treatment-item" 
							v-for="(t, ti) in knowledge.treatments" 
							:key="ti"
							@click="goEntity(t.uuid)"
						>
							<view class="t-main">
								<text class="t-name">{{ t.name }}</text>
								<text class="t-method">{{ t.method || t.content || '暂无详细步骤' }}</text>
							</view>
							<text class="more-arrow">></text>
						</view>
					</view>
				</view>

				<!-- Policies -->
				<view class="section-card animate-fade-in" v-if="knowledge.policies && knowledge.policies.length">
					<view class="section-title">
						<text class="icon">🛡️</text>
						<text>相关政策支撑</text>
					</view>
					<view class="policy-list">
						<view 
							class="policy-item" 
							v-for="(p, pi) in knowledge.policies" 
							:key="pi"
							@click="goEntity(p.uuid)"
						>
							<text class="p-name">{{ p.name }}</text>
							<text class="p-desc">{{ p.content }}</text>
							<text class="p-dept" v-if="p.department">受理部门：{{ p.department }}</text>
						</view>
					</view>
				</view>

				<!-- Articles -->
				<view class="section-card animate-fade-in" v-if="knowledge.articles && knowledge.articles.length">
					<view class="section-title">
						<text class="icon">📖</text>
						<text>扩展阅读</text>
					</view>
					<view class="article-grid">
						<view class="article-inline" v-for="(a, ai) in knowledge.articles" :key="ai" @click="goArticle(a.uuid)">
							<image class="a-cover" :src="a.cover" mode="aspectFill" v-if="a.cover" />
							<view class="a-info">
								<text class="a-title">{{ a.name }}</text>
							</view>
						</view>
					</view>
				</view>

				<view class="footer-tip">—— 心理中心 24H 守护您的成长 ——</view>
			</view>
		</scroll-view>

		<view class="loading-overlay" v-if="isLoading">
			<view class="spinner"></view>
			<text>正在通过图谱检索...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/utils/request.js'

const knowledge = ref(null)
const isLoading = ref(true)

onLoad((options) => {
	if (options.uuid) {
		fetchKnowledge(options.uuid)
	} else {
		uni.showToast({ title: '参数错误', icon: 'none' })
		setTimeout(() => uni.navigateBack(), 1500)
	}
})

const fetchKnowledge = async (uuid) => {
	isLoading.value = true
	try {
		const res = await request({
			url: `/graph/knowledge-base/${uuid}/`,
			method: 'GET'
		})
		knowledge.value = res
	} catch (e) {
		uni.showToast({ title: '加载失败', icon: 'none' })
	} finally {
		isLoading.value = false
	}
}

const hasEvents = computed(() => {
	return (knowledge.value?.current_events && knowledge.value.current_events.length) || 
		   (knowledge.value?.symptoms && knowledge.value.symptoms.length)
})

const riskLevelText = computed(() => {
	const level = knowledge.value?.risk_level?.priority || knowledge.value?.risk_details?.priority || 0
	if (level >= 3) return '极高风险'
	if (level === 2) return '中高风险'
	return '正常范围'
})

const riskLevelClass = computed(() => {
	const level = knowledge.value?.risk_level?.priority || knowledge.value?.risk_details?.priority || 0
	if (level >= 3) return 'high'
	if (level === 2) return 'medium'
	return 'low'
})

const goHome = () => uni.reLaunch({ url: '/pages/knowledge/index' })
const goEntity = (uuid) => uni.navigateTo({ url: `/pages/knowledge/entity?uuid=${uuid}` })
const goArticle = (uuid) => uni.navigateTo({ url: `/pages/discovery/article-detail?uuid=${uuid}` })
</script>

<style lang="scss" scoped>
.knowledge-detail {
	height: 100vh; background-color: #F8FBF9; display: flex; flex-direction: column;
}

.kb-header {
	background: linear-gradient(135deg, $sh-primary, #6AA285);
	color: #fff; padding: 60rpx 40rpx 100rpx; position: relative;
	.back-home-wrap {
		display: flex; align-items: center; gap: 8rpx; background: rgba(255,255,255,0.15);
		padding: 8rpx 20rpx; border-radius: 30rpx; font-size: 22rpx; margin-bottom: 30rpx; width: fit-content;
	}
	.header-content {
		.problem-name { font-size: 44rpx; font-weight: bold; margin-bottom: 20rpx; display: block; }
		.meta-row {
			display: flex; align-items: center; gap: 20rpx;
			.risk-badge { 
				font-size: 20rpx; padding: 4rpx 16rpx; border-radius: 40rpx;
				&.low { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); }
				&.medium { background: #FF9F00; }
				&.high { background: #FF4D4F; }
			}
			.problem-desc { font-size: 24rpx; opacity: 0.8; flex: 1; display: -webkit-box; -webkit-line-clamp: 1; line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
		}
	}
}

.content-scroll { 
	flex: 1; margin-top: -40rpx; border-top-left-radius: 40rpx; border-top-right-radius: 40rpx;
	background: #F8FBF9; padding-top: 40rpx;
}
.scroll-inner { padding: 0 30rpx 40rpx; }

.section-card {
	background: #fff; border-radius: 24rpx; padding: 30rpx; margin-bottom: 30rpx;
	box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
	.section-title {
		display: flex; align-items: center; gap: 12rpx; font-size: 30rpx; font-weight: bold; margin-bottom: 24rpx;
		.icon { font-size: 34rpx; }
	}
}

.scenario-content {
	.event-item { font-size: 26rpx; margin-bottom: 16rpx; line-height: 1.5; color: $sh-text-main; .event-time { color: $sh-primary; font-weight: bold; margin-right: 8rpx; } }
	.symptom-tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 10rpx; .tag { font-size: 22rpx; background: #F0F5F2; color: #5C8C71; padding: 4rpx 20rpx; border-radius: 30rpx; } }
}

.treatment-list {
	.treatment-item {
		display: flex; align-items: center; padding: 20rpx 0; border-bottom: 1px solid #f5f5f5;
		&:last-child { border-bottom: none; }
		.t-main { flex: 1; }
		.t-name { font-size: 28rpx; font-weight: bold; color: $sh-text-main; display: block; margin-bottom: 6rpx; }
		.t-method { font-size: 24rpx; color: $sh-text-sub; display: -webkit-box; -webkit-line-clamp: 1; line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
		.more-arrow { color: #ccc; font-size: 24rpx; margin-left: 20rpx; }
	}
}

.policy-list {
	.policy-item {
		background: #FAFAFA; padding: 20rpx; border-radius: 12rpx; margin-bottom: 16rpx;
		.p-name { font-size: 26rpx; font-weight: bold; display: block; margin-bottom: 10rpx; }
		.p-desc { font-size: 24rpx; color: $sh-text-sub; line-height: 1.5; display: block; }
		.p-dept { display: block; margin-top: 10rpx; font-size: 20rpx; color: $sh-text-sub; text-align: right; }
	}
}

.article-grid {
	display: flex; flex-wrap: wrap; gap: 20rpx;
	.article-inline {
		width: calc(50% - 10rpx);
		.a-cover { width: 100%; height: 160rpx; border-radius: 12rpx; }
		.a-title { font-size: 24rpx; color: $sh-text-main; margin-top: 10rpx; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
	}
}

.footer-tip { text-align: center; font-size: 20rpx; color: $sh-text-sub; opacity: 0.3; padding: 40rpx 0; }

.loading-overlay { 
	position: fixed; inset: 0; background: rgba(255, 255, 255, 0.8); z-index: 100;
	display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20rpx;
	.spinner { width: 40rpx; height: 40rpx; border: 3rpx solid #eee; border-top: 3rpx solid $sh-primary; border-radius: 50%; animation: spin 1s linear infinite; }
	text { font-size: 24rpx; color: $sh-text-sub; }
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.animate-fade-in { animation: fadeIn 0.5s ease-out both; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10rpx); } to { opacity: 1; transform: translateY(0); } }
</style>
