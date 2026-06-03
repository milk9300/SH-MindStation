<template>
	<view class="dashboard-card animate-fade-in">
		<view class="card-header">
			<view class="title-wrap">
				<text class="title">心理状态实时引擎</text>
				<text class="subtitle">Multi-level Intent Analysis</text>
			</view>
			<view class="status-tag">
				<view class="pulse-dot"></view>
				<text>AI 实时分析中</text>
			</view>
		</view>

		<view class="content-row">
			<!-- 左侧：雷达图 -->
			<view class="chart-area">
				<canvas 
					canvas-id="radarCanvas" 
					id="radarCanvas" 
					class="radar-canvas"
				></canvas>
				<view class="overall-score">
					<text class="score-num">{{ dashboardData.overall_score || 0 }}</text>
					<text class="score-label">综合指数</text>
				</view>
			</view>

			<!-- 右侧：核心意图 -->
			<view class="intent-area">
				<view class="section-header">
					<text class="section-title">核心意图识别</text>
				</view>
				<view class="intent-list">
					<view v-for="(intent, i) in dashboardData.intents" :key="i" class="intent-item" :style="{animationDelay: i*0.1+'s'}">
						<view class="intent-dot" :class="'dot-'+(i%3)"></view>
						<text class="intent-text">{{ intent }}</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 底部：智能建议 -->
		<view class="recommend-area">
			<view class="section-header">
				<text class="section-title">个性化动态建议</text>
				<text class="section-more">基于近期对话</text>
			</view>
			<view class="recommend-grid">
				<view v-for="(rec, i) in dashboardData.recommendations" :key="i" class="recommend-card">
					<view class="rec-icon-box">
						<text class="rec-icon">💡</text>
					</view>
					<text class="rec-text">{{ rec }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted, watch, getCurrentInstance } from 'vue'

const props = defineProps({
	dashboardData: {
		type: Object,
		default: () => ({
			radar_data: { categories: [], series: [] },
			intents: [],
			recommendations: [],
			overall_score: 0
		})
	}
})

const instance = getCurrentInstance()

// 绘制雷达图的核心逻辑
const drawRadar = () => {
	// [修复] 在组件内必须传入 instance 才能找到 canvas
	const ctx = uni.createCanvasContext('radarCanvas', instance)
	
	const width = uni.upx2px(340) 
	const height = uni.upx2px(340)
	const centerX = width / 2
	const centerY = height / 2
	const radius = width * 0.3
	
	const categories = props.dashboardData.radar_data.categories || []
	const seriesData = props.dashboardData.radar_data.series && props.dashboardData.radar_data.series[0] ? props.dashboardData.radar_data.series[0].data : []
	
	if (!categories.length) return

	const step = categories.length
	const angle = (Math.PI * 2) / step

	// 1. 绘制背景网格
	ctx.setLineWidth(1)
	for (let j = 1; j <= 4; j++) {
		const curR = (radius / 4) * j
		ctx.setStrokeStyle(j === 4 ? '#E0E0E0' : '#F5F5F5')
		ctx.beginPath()
		for (let i = 0; i < step; i++) {
			const x = centerX + curR * Math.cos(angle * i - Math.PI / 2)
			const y = centerY + curR * Math.sin(angle * i - Math.PI / 2)
			if (i === 0) ctx.moveTo(x, y)
			else ctx.lineTo(x, y)
		}
		ctx.closePath()
		ctx.stroke()
	}

	// 2. 绘制轴线和更美观的文字
	ctx.setFontSize(uni.upx2px(22))
	for (let i = 0; i < step; i++) {
		const x = centerX + radius * Math.cos(angle * i - Math.PI / 2)
		const y = centerY + radius * Math.sin(angle * i - Math.PI / 2)
		
		// 轴线
		ctx.setStrokeStyle('#F0F0F0')
		ctx.beginPath()
		ctx.moveTo(centerX, centerY)
		ctx.lineTo(x, y)
		ctx.stroke()
		
		// 文字标签
		const textR = radius + uni.upx2px(35)
		const tx = centerX + textR * Math.cos(angle * i - Math.PI / 2)
		const ty = centerY + textR * Math.sin(angle * i - Math.PI / 2)
		
		ctx.setFillStyle('#666666')
		ctx.setTextAlign('center')
		ctx.setTextBaseline('middle')
		ctx.fillText(categories[i], tx, ty)
	}

	// 3. 绘制覆盖区域
	if (seriesData.length) {
		ctx.beginPath()
		ctx.setLineWidth(2)
		ctx.setStrokeStyle('#589675') // 使用项目主题色
		ctx.setFillStyle('rgba(88, 150, 117, 0.2)')
		
		for (let i = 0; i < seriesData.length; i++) {
			const valR = (seriesData[i] / 100) * radius
			const x = centerX + valR * Math.cos(angle * i - Math.PI / 2)
			const y = centerY + valR * Math.sin(angle * i - Math.PI / 2)
			if (i === 0) ctx.moveTo(x, y)
			else ctx.lineTo(x, y)
		}
		ctx.closePath()
		ctx.fill()
		ctx.stroke()
		
		// 绘制数据点
		for (let i = 0; i < seriesData.length; i++) {
			const valR = (seriesData[i] / 100) * radius
			const x = centerX + valR * Math.cos(angle * i - Math.PI / 2)
			const y = centerY + valR * Math.sin(angle * i - Math.PI / 2)
			ctx.beginPath()
			ctx.arc(x, y, 3, 0, Math.PI * 2)
			ctx.setFillStyle('#589675')
			ctx.fill()
			// 白色内圆点增加精致感
			ctx.beginPath()
			ctx.arc(x, y, 1.5, 0, Math.PI * 2)
			ctx.setFillStyle('#FFFFFF')
			ctx.fill()
		}
	}

	ctx.draw()
}

onMounted(() => {
	setTimeout(() => drawRadar(), 600)
})

watch(() => props.dashboardData, () => {
	drawRadar()
}, { deep: true })

</script>

<style lang="scss" scoped>
.dashboard-card {
	background: #ffffff;
	border-radius: 32rpx;
	padding: 40rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.03);
	border: 1rpx solid rgba(0,0,0,0.02);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 30rpx;
	.title-wrap {
		display: flex;
		flex-direction: column;
		.title { font-size: 32rpx; font-weight: bold; color: #1A1A1A; letter-spacing: 1rpx; }
		.subtitle { font-size: 18rpx; color: #BCBCBC; text-transform: uppercase; margin-top: 4rpx; }
	}
	.status-tag {
		display: flex;
		align-items: center;
		gap: 10rpx;
		font-size: 20rpx;
		background: #F0F7F4;
		color: #589675;
		padding: 8rpx 16rpx;
		border-radius: 100rpx;
		font-weight: 500;
		.pulse-dot {
			width: 10rpx; height: 10rpx; background: #589675; border-radius: 50%;
			animation: pulse 2s infinite;
		}
	}
}

@keyframes pulse {
	0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(88, 150, 117, 0.7); }
	70% { transform: scale(1); box-shadow: 0 0 0 10rpx rgba(88, 150, 117, 0); }
	100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(88, 150, 117, 0); }
}

.content-row {
	display: flex;
	align-items: center;
	margin-bottom: 40rpx;
}

.chart-area {
	position: relative;
	width: 340rpx;
	height: 340rpx;
	flex-shrink: 0;
	.radar-canvas { width: 340rpx; height: 340rpx; }
	.overall-score {
		position: absolute;
		top: 50%; left: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		pointer-events: none;
		.score-num { font-size: 44rpx; font-weight: 800; color: #589675; line-height: 1; }
		.score-label { font-size: 18rpx; color: #999; margin-top: 6rpx; }
	}
}

.intent-area {
	flex: 1;
	padding-left: 20rpx;
	.section-header { margin-bottom: 20rpx; }
	.section-title { font-size: 24rpx; color: #999; font-weight: 600; }
	.intent-list {
		display: flex;
		flex-direction: column;
		gap: 16rpx;
	}
	.intent-item {
		display: flex;
		align-items: flex-start;
		gap: 12rpx;
		animation: fadeInUp 0.5s ease-out both;
		.intent-dot { 
			width: 12rpx; height: 12rpx; border-radius: 4rpx; margin-top: 10rpx; flex-shrink: 0;
			&.dot-0 { background: #589675; }
			&.dot-1 { background: #8AB8A1; }
			&.dot-2 { background: #B4D1C2; }
		}
		.intent-text { font-size: 24rpx; color: #333; line-height: 1.5; font-weight: 500; }
	}
}

.recommend-area {
	border-top: 1rpx solid #F8F8F8;
	padding-top: 30rpx;
	.section-header {
		display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 24rpx;
		.section-title { font-size: 24rpx; color: #999; font-weight: 600; }
		.section-more { font-size: 20rpx; color: #CCC; }
	}
	.recommend-grid {
		display: flex;
		flex-direction: column;
		gap: 20rpx;
	}
	.recommend-card {
		display: flex;
		align-items: center;
		gap: 20rpx;
		background: #FAFAFA;
		padding: 24rpx 28rpx;
		border-radius: 20rpx;
		transition: all 0.2s;
		&:active { background: #F0F0F0; transform: scale(0.98); }
		.rec-icon-box {
			width: 48rpx; height: 48rpx; background: #FFF; border-radius: 12rpx;
			display: flex; align-items: center; justify-content: center; font-size: 24rpx;
			box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.02);
		}
		.rec-text { font-size: 26rpx; color: #4A4A4A; flex: 1; font-weight: 500; }
	}
}

.animate-fade-in { animation: fadeIn 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(10rpx); } to { opacity: 1; transform: translateY(0); } }
</style>
