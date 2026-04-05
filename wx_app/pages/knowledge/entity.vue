<template>
	<view class="entity-detail">
		<!-- Header -->
		<view class="entity-header" :class="labelClass">
			<view class="header-main" v-if="detail">
				<text class="label-tag">{{ detail.label || '知识条目' }}</text>
				<text class="entity-name">{{ detail.name || detail.名称 || '未命名内容' }}</text>
			</view>
		</view>

		<scroll-view scroll-y class="entity-content" v-if="detail">
			<view class="content-wrapper">
				<!-- Main Description / Content -->
				<view class="info-card animate-fade-in" v-if="displayContent">
					<view class="section-title">
						<text class="icon">📄</text>
						<text>核心说明</text>
					</view>
					<text class="main-text">{{ displayContent }}</text>
				</view>

				<!-- Specific Methods / Steps (for Treatments) -->
				<view class="info-card animate-fade-in" v-if="detail.method">
					<view class="section-title">
						<text class="icon">🛠️</text>
						<text>操作方法 / 步骤</text>
					</view>
					<text class="main-text">{{ detail.method }}</text>
				</view>

				<!-- Location Info (for Treatments/Policies) -->
				<view class="info-card animate-fade-in" v-if="detail.location">
					<view class="section-title">
						<text class="icon">📍</text>
						<text>相关地点 & 资源</text>
					</view>
					<view class="location-item">
						<text class="loc-name">{{ detail.location }}</text>
						<text class="loc-time" v-if="detail.open_hours">（{{ detail.open_hours }}）</text>
					</view>
				</view>

				<!-- REVERSE CONNECTIONS: Related Psychological Problems -->
				<view class="related-section animate-fade-in" v-if="detail.related_problems && detail.related_problems.length">
					<view class="section-title">
						<text class="icon">🔗</text>
						<text>关联心理问题</text>
					</view>
					<scroll-view scroll-x class="problem-scroll-view" :show-scrollbar="false">
						<view class="problem-h-list">
							<view 
								class="problem-card" 
								v-for="p in detail.related_problems" 
								:key="p.uuid"
								@click="goToProblem(p.uuid)"
							>
								<view class="p-header">
									<text class="p-name">{{ p.name || p.名称 }}</text>
									<text class="p-cat">{{ p.category || '心理健康' }}</text>
								</view>
								<view class="p-risk" :class="getRiskClass(p.risk_level)">
									{{ p.risk_level || '一般' }}
								</view>
							</view>
						</view>
					</scroll-view>
					<text class="related-tip">该内容对以上问题具有缓解或指导作用，点击可查看深度分析</text>
				</view>

				<view class="empty-hint" v-if="!displayContent && !detail.method && (!detail.related_problems || !detail.related_problems.length)">
					<text>该条目暂无详细文本描述，建议咨询在线导师了解更多。</text>
				</view>

				<view class="footer-tip">—— 心理知识不仅是理论，更是力量 ——</view>
			</view>
		</scroll-view>

		<!-- Loading -->
		<view class="loading-overlay" v-if="isLoading">
			<view class="spinner"></view>
			<text>正在检索专项详情...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/utils/request.js'

const detail = ref(null)
const isLoading = ref(true)

onLoad((options) => {
	if (options.uuid) {
		fetchEntityDetail(options.uuid)
	} else {
		uni.showToast({ title: '参数丢失', icon: 'none' })
		setTimeout(() => uni.navigateBack(), 1500)
	}
})

const fetchEntityDetail = async (uuid) => {
	isLoading.value = true
	try {
		const res = await request({
			url: `/graph/knowledge-base/${uuid}/`,
			method: 'GET'
		})
		detail.value = res
		uni.setNavigationBarTitle({ title: res.name || res.名称 || '内容详情' })
	} catch (e) {
		uni.showToast({ title: '内容加载失败', icon: 'none' })
	} finally {
		isLoading.value = false
	}
}

const displayContent = computed(() => {
	if (!detail.value) return ''
	const c = detail.value.content || detail.value.内容 || detail.value.描述 || detail.value.说明
	if (c === '暂无详细描述') return '' // 让 empty-hint 处理
	return c
})

const labelClass = computed(() => {
	if (!detail.value) return ''
	const label = detail.value.label
	if (label === '应对技巧') return 'treatment'
	if (label === '校园政策') return 'policy'
	if (label === '症状') return 'symptom'
	if (label === '文章' || label === '科普文章') return 'article'
	return ''
})

const getRiskClass = (risk) => {
	if (!risk) return 'low'
	if (risk.includes('高')) return 'high'
	if (risk.includes('中')) return 'medium'
	return 'low'
}

const goToProblem = (uuid) => uni.navigateTo({ url: `/pages/knowledge/detail?uuid=${uuid}` })
</script>

<style lang="scss" scoped>
.entity-detail {
	height: 100vh; background-color: #F8FBF9; display: flex; flex-direction: column;
}

.entity-header {
	padding: 60rpx 40rpx 80rpx; color: #fff; position: relative;
	background: #6AA285; // Default primary-like fallback
	
	&.treatment { background: linear-gradient(135deg, $sh-primary, #6AA285); }
	&.policy { background: linear-gradient(135deg, #1890FF, #40A9FF); }
	&.symptom { background: linear-gradient(135deg, #722ED1, #9254DE); }
	&.article { background: linear-gradient(135deg, #FAAD14, #FFC53D); }

	
	.header-main {
		.label-tag { 
			display: inline-block; font-size: 20rpx; background: rgba(255,255,255,0.25);
			padding: 4rpx 16rpx; border-radius: 6rpx; margin-bottom: 16rpx;
		}
		.entity-name { font-size: 48rpx; font-weight: bold; display: block; line-height: 1.2; }
	}
}

.entity-content {
	flex: 1; margin-top: -30rpx; border-top-left-radius: 30rpx; border-top-right-radius: 30rpx;
	background: #F8FBF9; overflow: hidden;
}
.content-wrapper { padding: 40rpx 30rpx; }

.info-card {
	background: #fff; border-radius: 20rpx; padding: 30rpx; margin-bottom: 30rpx;
	box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
	.section-title {
		display: flex; align-items: center; gap: 12rpx; font-size: 28rpx; font-weight: bold; 
		color: $sh-text-main; margin-bottom: 20rpx; border-bottom: 1px solid #f8f8f8; padding-bottom: 16rpx;
		.icon { font-size: 32rpx; }
	}
	.main-text { font-size: 28rpx; line-height: 1.7; color: $sh-text-main; text-align: justify; word-break: break-all; }
}

.empty-hint {
	padding: 60rpx 40rpx; background: #fff; border-radius: 20rpx; text-align: center;
	color: $sh-text-sub; font-size: 24rpx; line-height: 1.6;
}

.location-item {
	display: flex; align-items: baseline; gap: 12rpx;
	.loc-name { font-size: 30rpx; color: $sh-primary; font-weight: bold; }
	.loc-time { font-size: 22rpx; color: $sh-text-sub; }
}

.related-section {
	margin-top: 50rpx;
	.section-title {
		display: flex; align-items: center; gap: 12rpx; font-size: 30rpx; font-weight: bold; 
		color: $sh-text-main; margin-bottom: 30rpx;
	}
	.problem-scroll-view {
		width: 100%; white-space: nowrap;
	}
	.problem-h-list {
		display: flex; gap: 20rpx; padding: 10rpx 0;
	}
	.problem-card {
		width: 320rpx; flex-shrink: 0; background: #fff; border-radius: 16rpx; padding: 24rpx;
		box-shadow: 0 4rpx 15rpx rgba(0,0,0,0.03); border: 1px solid #f0f0f0;
		white-space: normal; // Allow text wrap inside card

		.p-header {
			margin-bottom: 12rpx;
			.p-name { 
				font-size: 28rpx; font-weight: bold; color: $sh-primary; display: -webkit-box; 
				-webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; 
				overflow: hidden; line-height: 1.4; height: 80rpx;
			}
			.p-cat { font-size: 20rpx; color: $sh-text-sub; margin-top: 6rpx; display: block; }
		}
		.p-risk {
			font-size: 18rpx; border-radius: 4rpx; padding: 2rpx 12rpx; width: fit-content;
			&.low { background: #F6FFED; color: #52C41A; }
			&.medium { background: #FFF7E6; color: #FAAD14; }
			&.high { background: #FFF1F0; color: #F5222D; }
		}
	}
	.related-tip { display: block; text-align: center; font-size: 22rpx; color: $sh-text-sub; margin-top: 24rpx; }
}

.footer-tip { text-align: center; font-size: 20rpx; color: $sh-text-sub; opacity: 0.3; padding: 60rpx 0; }

.loading-overlay { 
	position: fixed; inset: 0; background: rgba(255, 255, 255, 0.8); z-index: 100;
	display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20rpx;
	.spinner { width: 44rpx; height: 44rpx; border: 3rpx solid #eee; border-top: 3rpx solid $sh-primary; border-radius: 50%; animation: spin 1s linear infinite; }
	text { font-size: 24rpx; color: $sh-text-sub; }
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.animate-fade-in { animation: fadeIn 0.5s ease-out both; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10rpx); } to { opacity: 1; transform: translateY(0); } }
</style>
