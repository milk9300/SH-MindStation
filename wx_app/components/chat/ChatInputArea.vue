<template>
	<view class="input-area" :class="{ 'input-focus': isFocused }">
		<view class="input-card">
			<!-- 模式切换: 文本/语音 -->
			<view class="mode-switch" @click="$emit('toggle-mode')">
				<text class="switch-icon">{{ inputMode === 'text' ? '🎙️' : '⌨️' }}</text>
			</view>
			
			<view class="content-box">
				<block v-if="inputMode === 'text'">
					<input 
						class="message-input"
						v-model="modelValue"
						placeholder="聊聊你的近况..."
						confirm-type="send"
						@confirm="$emit('send')"
						@focus="isFocused = true"
						@blur="isFocused = false"
					/>
				</block>
				
				<block v-else>
					<view 
						class="voice-btn" 
						:class="{ recording: isRecording }"
						@touchstart="$emit('start-voice')" 
						@touchend="$emit('stop-voice')"
					>
						<text>{{ isRecording ? '聆听中...' : '按住 说话' }}</text>
					</view>
				</block>
			</view>
			
			<!-- 发送按钮: 简约向上箭头 -->
			<view 
				class="send-btn" 
				:class="{ active: modelValue.trim() }" 
				@click="$emit('send')"
			>
				<view class="arrow-circle">
					<text class="arrow-icon">↑</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed } from 'vue'

const props = defineProps({
	inputMode: String,
	isRecording: Boolean,
	modelValue: String
})

const emit = defineEmits(['update:modelValue', 'toggle-mode', 'send', 'start-voice', 'stop-voice'])

const isFocused = ref(false)

const modelValue = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val)
})
</script>

<style lang="scss" scoped>
.input-area {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	z-index: 100;
	background: #F7FAF9;
	padding: 20rpx 30rpx calc(20rpx + env(safe-area-inset-bottom));
	box-sizing: border-box;
}

.input-card {
	background: #ffffff;
	border-radius: 60rpx;
	padding: 10rpx 10rpx 10rpx 20rpx;
	display: flex;
	align-items: center;
	gap: 16rpx;
	box-shadow: 0 8rpx 32rpx rgba(138, 187, 161, 0.15);
	border: 1rpx solid rgba(138, 187, 161, 0.1);
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	height: 100rpx;
	box-sizing: border-box;

	&:active {
		transform: scale(0.99);
	}
}

.input-focus .input-card {
	box-shadow: 0 12rpx 40rpx rgba(138, 187, 161, 0.2);
	border-color: $sh-primary;
}

.mode-switch {
	width: 70rpx;
	height: 70rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 38rpx;
	border-radius: 50%;
	transition: background 0.2s;
	&:active { background: #f0f0f0; }
}

.content-box {
	flex: 1;
	height: 100%;
	display: flex;
	align-items: center;
}

.message-input {
	width: 100%;
	height: 80rpx;
	font-size: 30rpx;
	color: $sh-text-main;
	padding: 0 10rpx;
}

.voice-btn {
	flex: 1;
	height: 80rpx;
	background: #f7f9f8;
	border-radius: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
	color: $sh-text-main;
	transition: all 0.2s;
	font-weight: 500;
	
	&.recording {
		background: $sh-primary;
		color: #ffffff;
		transform: scale(1.02);
	}
}

.send-btn {
	width: 80rpx;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	opacity: 0.3;
	transition: all 0.3s;
	transform: scale(0.8);

	&.active {
		opacity: 1;
		transform: scale(1);
	}

	.arrow-circle {
		width: 70rpx;
		height: 70rpx;
		background: $sh-primary;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4rpx 12rpx rgba($sh-primary, 0.3);
		
		.arrow-icon {
			color: #ffffff;
			font-size: 40rpx;
			font-weight: bold;
			margin-bottom: 4rpx;
		}
	}
}
</style>
