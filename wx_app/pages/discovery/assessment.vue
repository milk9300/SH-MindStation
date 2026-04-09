<template>
	<view class="assessment-container">
		<!-- 进度条 (基于 sort_order 估算) -->
		<view class="progress-bar" v-if="state === 'answering'">
			<view class="progress-inner" :style="{ width: progress + '%' }"></view>
		</view>

		<!-- 1. 简介/开始页 -->
		<view class="intro-card" v-if="state === 'intro'">
			<view class="icon-box">📋</view>
			<text class="scale-name">校园生活压力场景测评</text>
			<text class="scale-desc">本测评基于校园高频发生的真实场景设计，将评估你在焦虑、抑郁、人际敏感等维度的表现，并为你匹配专属的校园干预资源。</text>
			<view class="info-row">
				<text>形式：场景化会话</text>
				<text>特性：自适应跳题</text>
			</view>
			<view class="start-btn" @click="startAssessment">开始专业测评</view>
		</view>

		<!-- 2. 答题中 (对话式气泡版) -->
		<scroll-view 
			class="chat-quiz-area" 
			scroll-y 
			:scroll-into-view="lastMsgId"
			v-if="state === 'answering'"
		>
			<view class="msg-list">
				<view class="msg-item ai" id="current_q">
					<view class="avatar">🤖</view>
					<view class="bubble">
						<text class="q-dim" v-if="currentQuestion?.dimension">【{{ currentQuestion.dimension }}挑战】</text>
						<text>{{ currentQuestion?.content }}</text>
					</view>
				</view>

				<!-- 选项选择器 -->
				<view class="options-container" v-if="currentQuestion">
					<view 
						class="option-bubble" 
						v-for="(opt, idx) in currentQuestion.options" 
						:key="idx"
						@click="submitStep(opt)"
					>
						{{ opt.label }}
					</view>
				</view>
			</view>
		</scroll-view>

		<!-- 3. 结果展示 (深度分析报告) -->
		<view class="report-area" v-if="state === 'result' && report">
			<view class="report-card">
				<view class="score-section">
					<view class="score-val">{{ report.total_score }}</view>
					<view class="score-label">综合得分 ({{ report.level }})</view>
				</view>

				<!-- 雷达图容器 -->
				<view class="chart-section">
					<text class="section-title">维度风险分布图</text>
					<canvas canvas-id="radarCanvas" id="radarCanvas" class="radar-canvas"></canvas>
				</view>

				<!-- 趋势图容器 -->
				<view class="chart-section" v-if="report.history && report.history.length > 1">
					<view class="section-header">
						<text class="section-title">状态演变趋势</text>
						<text class="trend-tip">{{ trendFeedback }}</text>
					</view>
					<canvas canvas-id="trendCanvas" id="trendCanvas" class="trend-canvas"></canvas>
				</view>

				<!-- RAG 推荐资源 -->
				<view class="recommend-section" v-if="hasRecommendations">
					<text class="section-title">专属干预方案</text>
					<block v-for="(resList, dim) in report.recommendations" :key="dim">
						<view class="dim-group" v-if="resList && resList.length > 0">
							<text class="dim-tag">{{ dim }}专项建议</text>
							<view v-for="(res, sIdx) in resList" :key="sIdx">
								<!-- 修复位置：name 展示策略名，location 展示物理地点 -->
								<LocationCard :data="{ name: res.name, location: res.location, contact: res.contact }" />
							</view>
						</view>
					</block>
				</view>
				
				<view class="tip-box">
					<text>💡 提示：本评估由 SH MindStation AI 引擎根据你的近期行为偏好生成，非正式医疗诊断。</text>
				</view>
			</view>

			<view class="footer-btns">
				<view class="btn primary" @click="goHome">返回首页</view>
				<view class="btn secondary" @click="reStart">重新测评</view>
			</view>
		</view>

		<view v-if="loading" class="loading-overlay">
			<view class="loading-spinner"></view>
			<text>AI 正在分析...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import request from '@/utils/request.js'
import LocationCard from '@/components/cards/LocationCard.vue'

const scale_id = ref('')
const state = ref('intro')
const loading = ref(false)
const session_id = ref(null)
const currentQuestion = ref(null)
const report = ref(null)
const lastMsgId = ref('')
const trigger_msg_id = ref('')

import { onLoad } from '@dcloudio/uni-app'
onLoad((options) => {
	if (options.id) {
		scale_id.value = options.id
	} else {
		scale_id.value = 'scale_campus_life_v1'
	}
	if (options.record_id) {
		fetchRecord(options.record_id)
	}
	if (options.trigger_msg_id) {
		trigger_msg_id.value = options.trigger_msg_id
	}
})

const fetchRecord = async (record_id) => {
	loading.value = true
	try {
		const res = await request({
			url: `/assessments/${record_id}/`,
			method: 'GET'
		})
		
		// 映射后端数据到前端报表结构
		report.value = {
			scale_name: res.scale_name,
			total_score: res.total_score,
			level: res.result_level,
			dimension_scores: res.dimension_scores,
			recommendations: res.recommendations || {}
		}
		
		// 获取历史趋势数据 (获取同类型量表的最近10条)
		const historyRes = await request({
			url: `/assessments/?page=1&page_size=10`,
			method: 'GET'
		})
		const historyItems = historyRes.results || historyRes || []
		// 过滤同名量表
		const filteredHistory = historyItems.filter(h => h.scale_name === res.scale_name)
		
		report.value.history = filteredHistory.reverse().map(h => ({
			date: h.created_at.substring(5, 10).replace('-', '/'),
			score: h.total_score
		}))

		state.value = 'result'
		nextTick(() => {
			drawRadarChart()
			drawTrendChart()
		})
	} catch (err) {
		console.error('Fetch record error:', err)
		uni.showToast({ title: '加载记录失败', icon: 'none' })
	} finally {
		loading.value = false
	}
}

const progress = computed(() => {
	if (!currentQuestion.value) return 0
	return (currentQuestion.value.sort_order / 6) * 100 
})

const hasRecommendations = computed(() => {
	if (!report.value || !report.value.recommendations) return false
	return Object.keys(report.value.recommendations).some(k => report.value.recommendations[k] && report.value.recommendations[k].length > 0)
})

const trendFeedback = computed(() => {
	if (!report.value || !report.value.history || report.value.history.length < 2) return ''
	const history = report.value.history
	const current = history[history.length - 1].score
	const prev = history[history.length - 2].score
	
	if (current < prev) return '✨ 状态正在好转，压力有所减轻'
	if (current > prev) return '💡 压力有所上升，建议加强放松'
	return '✅ 状态平稳，请继续保持'
})

const startAssessment = async () => {
	loading.value = true
	try {
		const res = await request({
			url: `/scales/${scale_id.value}/start/`,
			method: 'POST'
		})
		session_id.value = res.session_id
		currentQuestion.value = res.question
		state.value = 'answering'
		lastMsgId.value = 'current_q'
	} catch (err) {
		uni.showToast({ title: '启动失败', icon: 'none' })
	} finally {
		loading.value = false
	}
}

const submitStep = async (opt) => {
	if (loading.value) return
	loading.value = true
	try {
		const res = await request({
			url: '/scales/submit-step/',
			method: 'POST',
			data: {
				session_id: session_id.value,
				q_id: currentQuestion.value.id,
				label: opt.label,
				score: opt.score,
				trigger_msg_id: trigger_msg_id.value
			}
		})

		if (res.is_finished) {
			report.value = res.report
			state.value = 'result'
			// [新增] 标记为已完成，等回到聊天页时刷新状态
			uni.setStorageSync('refresh_chat_session', true)
			nextTick(() => {
				drawRadarChart()
				drawTrendChart()
			})
		} else {
			currentQuestion.value = res.next_question
			lastMsgId.value = 'current_q'
		}
	} catch (err) {
		uni.showToast({ title: '提交失败', icon: 'none' })
	} finally {
		loading.value = false
	}
}

// 原生 Canvas 绘制折线图
const drawTrendChart = () => {
	const history = report.value.history || []
	if (history.length < 2) return

	const ctx = uni.createCanvasContext('trendCanvas')
	const width = uni.upx2px(600)
	const height = uni.upx2px(300)
	const padding = 40
	
	const maxScore = 50 // 假设压力阈值范围
	const xStep = (width - padding * 2) / (history.length - 1)
	const getX = (i) => padding + i * xStep
	const getY = (score) => height - padding - (score / maxScore) * (height - padding * 2)

	// 1. 绘制背景网格线
	ctx.setStrokeStyle('#F2F6FC')
	ctx.setLineWidth(1)
	for (let i = 0; i <= 4; i++) {
		const y = getY(i * 12.5) // 0, 12.5, 25...
		ctx.beginPath()
		ctx.moveTo(padding, y)
		ctx.lineTo(width - padding, y)
		ctx.stroke()
	}

	// 2. 绘制折线
	ctx.beginPath()
	ctx.setStrokeStyle('#5BB18C')
	ctx.setLineWidth(3)
	ctx.setLineJoin('round')
	history.forEach((h, i) => {
		const x = getX(i)
		const y = getY(h.score)
		if (i === 0) ctx.moveTo(x, y)
		else ctx.lineTo(x, y)
	})
	ctx.stroke()

	// 3. 绘制数据点
	history.forEach((h, i) => {
		const x = getX(i)
		const y = getY(h.score)
		const isLast = i === history.length - 1
		
		// 外部光晕
		ctx.beginPath()
		ctx.setFillStyle(isLast ? 'rgba(91, 177, 140, 0.4)' : 'rgba(91, 177, 140, 0.1)')
		ctx.arc(x, y, isLast ? 10 : 6, 0, Math.PI * 2)
		ctx.fill()

		// 核心圆点
		ctx.beginPath()
		ctx.setFillStyle('#5BB18C')
		ctx.arc(x, y, isLast ? 5 : 3, 0, Math.PI * 2)
		ctx.fill()

		// 标注 X 轴日期
		ctx.setFillStyle('#909399')
		ctx.setFontSize(uni.upx2px(20))
		ctx.setTextAlign('center')
		ctx.fillText(h.date, x, height - 10)
	})

	ctx.draw()
}

// 原生 Canvas 绘制雷达图
const drawRadarChart = () => {
	const scores = report.value.dimension_scores || {}
	const dims = Object.keys(scores)
	if (dims.length < 3) return

	const ctx = uni.createCanvasContext('radarCanvas')
	const centerX = uni.upx2px(600) / 2
	const centerY = uni.upx2px(350) / 2
	const radius = centerY * 0.65 // 进一步缩小半径，确保标签完全可见
	const angleStep = (Math.PI * 2) / dims.length

	// 1. 绘制底图（多边形网格）
	ctx.setStrokeStyle('#E4E7ED')
	ctx.setLineWidth(1)
	for (let r = 1; r <= 4; r++) {
		const curR = (radius / 4) * r
		ctx.beginPath()
		for (let i = 0; i < dims.length; i++) {
			const x = centerX + curR * Math.cos(i * angleStep - Math.PI / 2)
			const y = centerY + curR * Math.sin(i * angleStep - Math.PI / 2)
			if (i === 0) ctx.moveTo(x, y)
			else ctx.lineTo(x, y)
		}
		ctx.closePath()
		ctx.stroke()
	}

	// 2. 绘制数据区域
	ctx.beginPath()
	ctx.setStrokeStyle('#5BB18C')
	ctx.setLineWidth(2)
	ctx.setFillStyle('rgba(91, 177, 140, 0.3)')
	dims.forEach((dim, i) => {
		const score = Math.min(scores[dim], 20)
		const r = (score / 20) * radius
		const x = centerX + r * Math.cos(i * angleStep - Math.PI / 2)
		const y = centerY + r * Math.sin(i * angleStep - Math.PI / 2)
		if (i === 0) ctx.moveTo(x, y)
		else ctx.lineTo(x, y)
	})
	ctx.closePath()
	ctx.fill()
	ctx.stroke()

	// 3. 标注文字
	ctx.setFillStyle('#606266')
	ctx.setFontSize(uni.upx2px(24))
	ctx.setTextAlign('center')
	ctx.setTextBaseline('middle')
	
	dims.forEach((dim, i) => {
		const x = centerX + (radius + uni.upx2px(45)) * Math.cos(i * angleStep - Math.PI / 2)
		const y = centerY + (radius + uni.upx2px(45)) * Math.sin(i * angleStep - Math.PI / 2)
		ctx.fillText(dim, x, y)
	})

	ctx.draw()
}

const goHome = () => uni.reLaunch({ url: '/pages/chat/index' })
const reStart = () => {
	state.value = 'intro'
	report.value = null
}
</script>

<style lang="scss" scoped>
.assessment-container {
	background: #F5F7FA;
	min-height: 100vh;
	display: flex;
	flex-direction: column;
}

.progress-bar {
	position: fixed;
	top: 0; left: 0; right: 0; height: 8rpx;
	background: #E4E7ED; z-index: 100;
	.progress-inner { height: 100%; background: #5BB18C; transition: width 0.3s; }
}

.intro-card {
	margin: 100rpx 40rpx; padding: 60rpx 40rpx;
	background: #fff; border-radius: 32rpx; text-align: center;
	box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.05);
	.icon-box { font-size: 80rpx; margin-bottom: 20rpx; }
	.scale-name { font-size: 40rpx; font-weight: 700; color: #303133; display: block; margin-bottom: 20rpx; }
	.scale-desc { font-size: 28rpx; color: #606266; line-height: 1.6; margin-bottom: 40rpx; display: block; }
	.info-row { display: flex; justify-content: center; gap: 40rpx; font-size: 24rpx; color: #5BB18C; margin-bottom: 60rpx; }
	.start-btn { 
		background: #5BB18C; color: #fff; padding: 30rpx; border-radius: 60rpx;
		font-size: 32rpx; font-weight: 600; box-shadow: 0 8rpx 20rpx rgba(91,177,140,0.3);
	}
}

.chat-quiz-area {
	flex: 1; padding: 40rpx 30rpx;
	.msg-item {
		display: flex; margin-bottom: 30rpx;
		animation: fadeIn 0.4s ease-out;
		&.ai {
			.avatar { 
				width: 72rpx; height: 72rpx; background: #fff; border-radius: 50%; 
				display: flex; align-items: center; justify-content: center; 
				font-size: 36rpx; margin-right: 20rpx; 
				box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.05);
			}
			.bubble { 
				flex: 1; background: #fff; padding: 30rpx; border-radius: 24rpx;
				font-size: 30rpx; color: #303133; line-height: 1.6; 
				box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.03);
				max-width: 85%;
				.q-dim { color: #5BB18C; font-weight: 600; font-size: 24rpx; display: block; margin-bottom: 12rpx; }
			}
		}
	}
}

.options-container {
	padding: 20rpx 0 60rpx 92rpx; 
	display: flex; flex-wrap: wrap; gap: 20rpx;
	.option-bubble {
		background: #fff; color: #5BB18C; border: 2rpx solid #5BB18C;
		padding: 18rpx 36rpx; border-radius: 40rpx; font-size: 28rpx;
		transition: all 0.2s;
		min-width: 140rpx; text-align: center;
		&:active { background: #5BB18C; color: #fff; transform: scale(0.95); }
	}
}

@keyframes fadeIn {
	from { opacity: 0; transform: translateY(10rpx); }
	to { opacity: 1; transform: translateY(0); }
}

.report-area {
	padding: 40rpx 30rpx;
	.report-card {
		background: #fff; border-radius: 40rpx; padding: 60rpx 40rpx; box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.05);
		.score-section {
			text-align: center; margin-bottom: 60rpx;
			.score-val { font-size: 100rpx; font-weight: 800; color: #5BB18C; line-height: 1; }
			.score-label { font-size: 28rpx; color: #909399; margin-top: 10rpx; }
		}
		.section-header {
			display: flex; justify-content: space-between; align-items: center; margin: 40rpx 0 20rpx; padding-left: 20rpx; border-left: 8rpx solid #5BB18C;
			.section-title { font-size: 34rpx; font-weight: 700; color: #303133; margin: 0; border: none; padding: 0; }
			.trend-tip { font-size: 24rpx; color: #5BB18C; font-weight: 500; }
		}
		.radar-canvas { width: 600rpx; height: 350rpx; margin: 0 auto; }
		.trend-canvas { width: 600rpx; height: 300rpx; margin: 0 auto; }
	}
}

.dim-group {
	margin-bottom: 30rpx;
	.dim-tag { font-size: 24rpx; background: #f0f9f4; color: #5BB18C; padding: 4rpx 16rpx; border-radius: 8rpx; margin-bottom: 20rpx; display: inline-block; }
}

.tip-box { background: #fdf6ec; padding: 24rpx; border-radius: 16rpx; margin-top: 40rpx; text-align: left; text { font-size: 24rpx; color: #e6a23c; line-height: 1.5; } }

.footer-btns { display: flex; gap: 20rpx; margin-top: 40rpx; .btn { flex: 1; padding: 26rpx; text-align: center; border-radius: 50rpx; font-size: 30rpx; &.primary { background: #5BB18C; color: #fff; } &.secondary { background: #fff; color: #909399; border: 1px solid #DCDFE6; } } }

.loading-overlay { 
	position: fixed; inset: 0; background: rgba(255,255,255,0.7); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000;
	.loading-spinner { width: 60rpx; height: 60rpx; border: 6rpx solid #f3f3f3; border-top: 6rpx solid #5BB18C; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20rpx; }
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
