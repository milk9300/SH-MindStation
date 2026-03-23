<template>
	<view class="assessment-container">
		<!-- 进度条 -->
		<view class="progress-bar" v-if="state === 'answering' && scale">
			<view class="progress-inner" :style="{ width: progress + '%' }"></view>
		</view>

		<!-- 1. 简介/开始页 -->
		<view class="intro-card" v-if="state === 'intro' && scale">
			<view class="icon-box">📋</view>
			<text class="scale-name">{{ scale.name }}</text>
			<text class="scale-desc">{{ scale.description || '请根据您最近一周的实际感受进行选择。' }}</text>
			<view class="info-row">
				<text>题目数量：{{ scale.questions?.length || 0 }} 题</text>
				<text>预计用时：约 {{ Math.ceil((scale.questions?.length || 0) * 0.5) }} 分钟</text>
			</view>
			<view class="start-btn" @click="start">开始测评</view>
		</view>

		<!-- 2. 答题中 -->
		<view class="quiz-area" v-if="state === 'answering' && currentQuestion">
			<view class="question-card">
				<text class="q-index">第 {{ currentIdx + 1 }} / {{ scale.questions.length }} 题</text>
				<text class="q-content">{{ currentQuestion.content }}</text>
				
				<view class="options-list">
					<view 
						class="option-item" 
						v-for="(opt, oIdx) in currentQuestion.options" 
						:key="oIdx"
						@click="selectOption(opt)"
					>
						<text class="opt-label">{{ opt.label }}</text>
					</view>
				</view>
			</view>
			<view class="back-link" v-if="currentIdx > 0" @click="prev">返回上一题</view>
		</view>

		<!-- 3. 结果展示 -->
		<view class="result-card" v-if="state === 'result'">
			<view class="result-header">
				<text class="title">测评完成</text>
				<view class="score-circle">
					<text class="score">{{ finalScore }}</text>
					<text class="unit">分</text>
				</view>
				<text class="result-level">{{ resultLevel }}</text>
			</view>
			
			<view class="result-advice">
				<text class="advice-title">👋 温馨提示</text>
				<text class="advice-content">本测评结果仅供参考，不作为临床诊断依据。如果您感到困扰，建议预约学校心理咨询室进行深层交流。</text>
			</view>

			<view class="footer-btns">
				<view class="btn primary" @click="goHome">返回首页</view>
				<view class="btn secondary" @click="reStart">重新测评</view>
			</view>
		</view>

		<view v-if="loading" class="loading-overlay">
			<text>数据处理中...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request.js'

const id = ref('')
const scale = ref(null)
const state = ref('intro') // intro, answering, result
const currentIdx = ref(0)
const answers = ref([])
const loading = ref(false)
const finalScore = ref(0)
const resultLevel = ref('正在计算...')

const currentQuestion = computed(() => {
	if (!scale.value || !scale.value.questions) return null
	return scale.value.questions[currentIdx.value]
})

const progress = computed(() => {
	if (!scale.value || !scale.value.questions) return 0
	return ((currentIdx.value) / scale.value.questions.length) * 100
})

const fetchData = async () => {
	loading.value = true
	try {
		const res = await request({
			url: `/scales/${id.value}/`,
			method: 'GET'
		})
		scale.value = res
	} catch (err) {
		console.error('Fetch scale error:', err)
	} finally {
		loading.value = false
	}
}

const start = () => {
	state.value = 'answering'
	currentIdx.value = 0
	answers.value = []
}

const selectOption = (opt) => {
	answers.value[currentIdx.value] = opt
	if (currentIdx.value < scale.value.questions.length - 1) {
		setTimeout(() => {
			currentIdx.value++
		}, 200)
	} else {
		finish()
	}
}

const prev = () => {
	if (currentIdx.value > 0) {
		currentIdx.value--
	}
}

const finish = async () => {
	loading.value = true
	// 1. 计算总分 (兼容 weight 和 score 两个字段名)
	let score = 0
	answers.value.forEach(ans => {
		score += (ans.score !== undefined ? ans.score : (ans.weight || 0))
	})
	finalScore.value = score

	// 2. 匹配结果等级
	let level = '数据异常'
	if (scale.value.scoring_rules) {
		for (const rule of scale.value.scoring_rules) {
			if (score >= rule.min && score <= rule.max) {
				level = rule.result
				break
			}
		}
	}
	resultLevel.value = level

	// 3. 提交记录
	try {
		await request({
			url: '/assessments/',
			method: 'POST',
			data: {
				scale_name: scale.value.name,
				total_score: score,
				result_level: level,
				report_json: answers.value.map((ans, idx) => ({
					q: scale.value.questions[idx].content,
					a: ans.label,
					s: (ans.score !== undefined ? ans.score : (ans.weight || 0))
				}))
			}
		})
		state.value = 'result'
	} catch (err) {
		console.error('Save result error:', err)
		uni.showToast({ title: '结果保存失败', icon: 'none' })
		state.value = 'result' // 即使保存失败也显示结果，但 UI 提示
	} finally {
		loading.value = false
	}
}

const goHome = () => {
	uni.reLaunch({ url: '/pages/home/index' })
}

const reStart = () => {
	state.value = 'intro'
}

onMounted(() => {
	const pages = getCurrentPages()
	const curPage = pages[pages.length - 1]
	if (curPage && curPage.options && curPage.options.id) {
		id.value = curPage.options.id
		fetchData()
	}
})
</script>

<style lang="scss">
.assessment-container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.progress-bar {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	height: 6rpx;
	background: #eee;
	z-index: 100;
	.progress-inner {
		height: 100%;
		background: $sh-primary;
		transition: width 0.3s;
	}
}

// Intro
.intro-card {
	@include sh-card;
	padding: 60rpx 40rpx;
	text-align: center;
	margin-top: 40rpx;
	.icon-box {
		font-size: 80rpx;
		margin-bottom: 30rpx;
	}
	.scale-name {
		font-size: 36rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-bottom: 24rpx;
		display: block;
	}
	.scale-desc {
		font-size: 26rpx;
		color: $sh-text-sub;
		line-height: 1.6;
		margin-bottom: 40rpx;
		display: block;
	}
	.info-row {
		display: flex;
		justify-content: center;
		gap: 30rpx;
		font-size: 24rpx;
		color: $sh-primary;
		margin-bottom: 60rpx;
	}
	.start-btn {
		background: $sh-primary;
		color: #fff;
		padding: 26rpx;
		border-radius: $sh-radius-lg;
		font-size: 30rpx;
		font-weight: 500;
	}
}

// Quiz
.question-card {
	@include sh-card;
	padding: 40rpx;
	margin-top: 40rpx;
	.q-index {
		font-size: 24rpx;
		color: $sh-primary;
		margin-bottom: 20rpx;
		display: block;
	}
	.q-content {
		font-size: 34rpx;
		color: $sh-text-main;
		font-weight: 500;
		line-height: 1.5;
		margin-bottom: 60rpx;
		display: block;
	}
}
.options-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}
.option-item {
	background: #f8f9fa;
	border: 2rpx solid $sh-border;
	padding: 30rpx;
	border-radius: $sh-radius-md;
	text-align: center;
	transition: all 0.2s;
	&:active {
		background: rgba($sh-primary, 0.1);
		border-color: $sh-primary;
	}
	.opt-label {
		font-size: 28rpx;
		color: $sh-text-main;
	}
}
.back-link {
	text-align: center;
	margin-top: 40rpx;
	color: $sh-text-sub;
	font-size: 26rpx;
}

// Result
.result-card {
	@include sh-card;
	padding: 60rpx 40rpx;
	text-align: center;
	margin-top: 40rpx;
	.result-header {
		margin-bottom: 60rpx;
		.title {
			font-size: 30rpx;
			color: $sh-text-sub;
			margin-bottom: 30rpx;
			display: block;
		}
		.score-circle {
			width: 200rpx;
			height: 200rpx;
			border-radius: 50%;
			background: rgba($sh-primary, 0.1);
			display: flex;
			align-items: center;
			justify-content: center;
			margin: 0 auto 30rpx;
			.score {
				font-size: 64rpx;
				font-weight: bold;
				color: $sh-primary;
			}
			.unit {
				font-size: 24rpx;
				color: $sh-primary;
				margin-left: 4rpx;
				margin-top: 20rpx;
			}
		}
		.result-level {
			font-size: 40rpx;
			font-weight: 600;
			color: $sh-text-main;
		}
	}
	.result-advice {
		background: #fdf6ec;
		padding: 30rpx;
		border-radius: $sh-radius-md;
		text-align: left;
		margin-bottom: 60rpx;
		.advice-title {
			font-size: 28rpx;
			font-weight: 600;
			color: #e6a23c;
			margin-bottom: 12rpx;
			display: block;
		}
		.advice-content {
			font-size: 24rpx;
			color: #8c939d;
			line-height: 1.6;
		}
	}
}
.footer-btns {
	display: flex;
	gap: 20rpx;
	.btn {
		flex: 1;
		padding: 24rpx;
		border-radius: $sh-radius-lg;
		font-size: 28rpx;
		&.primary {
			background: $sh-primary;
			color: #fff;
		}
		&.secondary {
			background: #eee;
			color: $sh-text-sub;
		}
	}
}

.loading-overlay {
	position: fixed;
	top: 0; left: 0; right: 0; bottom: 0;
	background: rgba(255,255,255,0.8);
	display: flex;
	align-items: center;
	justify-content: center;
	color: $sh-text-sub;
	z-index: 999;
}
</style>
