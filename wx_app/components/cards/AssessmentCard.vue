<template>
	<view class="assessment-card animate-fade-in" @click="handleCardClick">
		<view class="card-glow"></view>
		<view class="card-content">
			<view class="header">
				<view class="icon-wrapper">
					<text class="icon">📋</text>
				</view>
				<view class="title-group">
					<text class="title">{{ data.title || '专业心理评估' }}</text>
					<text class="subtitle">基于当前对话生成的深度建议</text>
				</view>
			</view>
			
			<view class="reason-box">
				<text class="label">建议理由：</text>
				<text class="text">{{ data.reason }}</text>
			</view>
			
			<view v-if="!data.is_completed" class="action-btn" @click="startAssessment">
				<text>立即开始测评</text>
				<text class="btn-arrow">➔</text>
			</view>

			<view v-else class="completed-box">
				<view class="score-info">
					<text class="label">测评得分</text>
					<text class="val">{{ data.result?.score || 0 }}</text>
				</view>
				<view class="level-tag">{{ data.result?.level || '已完成' }}</view>
			</view>
			
			<view class="footer-tip">
				<text>{{ data.is_completed ? '测评已完成，点击可查看报告' : '完成测评后，我能为你提供更具针对性的支持' }}</text>
			</view>
		</view>
	</view>
</template>

<script setup>
const props = defineProps({
	data: {
		type: Object,
		required: true
	},
	msgId: {
		type: [String, Number],
		default: ''
	}
})

const handleCardClick = () => {
	if (props.data.is_completed && props.data.result?.record_id) {
		uni.navigateTo({
			url: `/pages/discovery/assessment?record_id=${props.data.result.record_id}`
		})
	}
}

const startAssessment = () => {
	if (props.data.is_completed) {
		handleCardClick()
		return
	}
	uni.navigateTo({
		url: `/pages/discovery/assessment?id=${props.data.scale_id}&trigger_msg_id=${props.msgId}`
	})
}
</script>

<style lang="scss" scoped>
.assessment-card {
	position: relative;
	background: #fff;
	border-radius: $sh-radius-md;
	overflow: hidden;
	box-shadow: 0 8rpx 30rpx rgba($sh-primary, 0.12);
	border: 1px solid rgba($sh-primary, 0.1);
	margin-bottom: 24rpx;
}

.card-glow {
	position: absolute;
	top: -50%;
	left: -50%;
	width: 200%;
	height: 200%;
	background: radial-gradient(circle, rgba($sh-primary, 0.05) 0%, transparent 70%);
	pointer-events: none;
}

.card-content {
	padding: 32rpx;
	position: relative;
	z-index: 1;
}

.header {
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin-bottom: 24rpx;
	
	.icon-wrapper {
		width: 72rpx;
		height: 72rpx;
		background: rgba($sh-primary, 0.1);
		border-radius: 16rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		.icon { font-size: 40rpx; }
	}
	
	.title-group {
		display: flex;
		flex-direction: column;
		.title { font-size: 32rpx; font-weight: 600; color: $sh-primary; }
		.subtitle { font-size: 20rpx; color: $sh-text-sub; margin-top: 4rpx; }
	}
}

.reason-box {
	background: #F8FAF9;
	border-radius: 12rpx;
	padding: 20rpx;
	margin-bottom: 32rpx;
	.label { font-size: 24rpx; font-weight: 600; color: $sh-text-main; display: block; margin-bottom: 8rpx; }
	.text { font-size: 26rpx; color: $sh-text-sub; line-height: 1.5; }
}

.action-btn {
	background: linear-gradient(135deg, $sh-primary, #6AA285);
	color: #fff;
	padding: 24rpx;
	border-radius: $sh-radius-sm;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	font-size: 28rpx;
	font-weight: 600;
	box-shadow: 0 4rpx 15rpx rgba($sh-primary, 0.3);
	transition: all 0.2s;
	
	&:active { transform: scale(0.98); opacity: 0.9; }
	.btn-arrow { font-size: 24rpx; }
}

.footer-tip {
	margin-top: 20rpx;
	text-align: center;
	text { font-size: 22rpx; color: $sh-text-sub; }
}

.completed-box {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 24rpx 32rpx;
	background: rgba($sh-primary, 0.03);
	border: 1px solid rgba($sh-primary, 0.1);
	border-radius: $sh-radius-sm;
	
	.score-info {
		display: flex;
		align-items: baseline;
		.label { font-size: 24rpx; color: $sh-text-sub; }
		.val { font-size: 40rpx; font-weight: 700; color: $sh-primary; margin-left: 12rpx; }
	}
	.level-tag {
		font-size: 24rpx;
		color: #fff;
		background: $sh-primary;
		padding: 6rpx 20rpx;
		border-radius: 40rpx;
		font-weight: 600;
	}
}

.animate-fade-in { animation: fadeIn 0.6s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10rpx); } to { opacity: 1; transform: translateY(0); } }
</style>
