<template>
	<view class="register-container">
		<view class="background-decor">
			<view class="circle c1"></view>
			<view class="circle c2"></view>
		</view>
		
		<view class="register-box">
			<view class="logo-area">
				<text class="logo-emoji">🌿</text>
				<text class="app-name">完善你的心理档案</text>
				<text class="app-slogan">以下信息仅用于校园心理健康服务</text>
			</view>
			
			<view class="form-area">
				<!-- 头像 (选填，微信官方 chooseAvatar) -->
				<view class="avatar-section">
					<button class="avatar-btn" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
						<image 
							class="avatar-img" 
							:src="avatarUrl || '/static/default-avatar.png'" 
							mode="aspectFill"
						/>
						<text class="avatar-tip">点击选择头像</text>
					</button>
				</view>
				
				<!-- 昵称 (选填，微信官方 nickname 键盘) -->
				<view class="input-group">
					<text class="label">昵称 <text class="optional">（选填）</text></text>
					<input 
						class="input" 
						type="nickname"
						v-model="nickname" 
						placeholder="点击使用微信昵称"
						placeholder-class="placeholder"
						@blur="onNicknameBlur"
					/>
				</view>
				
				<!-- 学号 (必填) -->
				<view class="input-group">
					<text class="label">学号 <text class="required">*</text></text>
					<input 
						class="input" 
						v-model="campusId" 
						placeholder="请输入您的学号"
						placeholder-class="placeholder"
					/>
				</view>
				
				<!-- 真实姓名 (必填) -->
				<view class="input-group">
					<text class="label">真实姓名 <text class="required">*</text></text>
					<input 
						class="input" 
						v-model="realName" 
						placeholder="请输入您的姓名"
						placeholder-class="placeholder"
					/>
				</view>
				
				<!-- 手机号 (选填) -->
				<view class="input-group">
					<text class="label">手机号 <text class="optional">（选填）</text></text>
					<input 
						class="input" 
						type="number"
						v-model="phone" 
						placeholder="用于紧急联络（选填）"
						placeholder-class="placeholder"
						maxlength="11"
					/>
				</view>
				
				<view class="submit-btn" :class="{ active: canSubmit }" @click="handleSubmit">
					<text v-if="!isLoading">确认并进入</text>
					<text v-else>正在保存档案...</text>
				</view>
				
				<view class="privacy-tip">
					<text>🔒 您的信息受到严格加密保护</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import request from '@/utils/request.js'

const avatarUrl = ref('')
const nickname = ref('')
const campusId = ref('')
const realName = ref('')
const phone = ref('')
const isLoading = ref(false)

// 必填字段校验：学号 + 真实姓名
const canSubmit = computed(() => {
	return campusId.value.trim().length > 0 && realName.value.trim().length > 0
})

// 微信官方头像选择回调
const onChooseAvatar = (e) => {
	avatarUrl.value = e.detail.avatarUrl
}

// 微信昵称自动填充回调
const onNicknameBlur = (e) => {
	if (e.detail.value) {
		nickname.value = e.detail.value
	}
}

const handleSubmit = async () => {
	if (!canSubmit.value || isLoading.value) return
	
	isLoading.value = true
	try {
		const data = {
			campus_id: campusId.value.trim(),
			real_name: realName.value.trim()
		}
		
		// 选填字段：有值才传
		if (nickname.value.trim()) data.nickname = nickname.value.trim()
		if (avatarUrl.value) data.avatar_url = avatarUrl.value
		if (phone.value.trim()) data.phone = phone.value.trim()
		
		const res = await request({
			url: '/auth/complete-profile/',
			method: 'POST',
			data
		})
		
		if (res && res.user) {
			// 更新本地缓存的用户信息
			uni.setStorageSync('student_user', JSON.stringify(res.user))
			uni.setStorageSync('profile_completed', 'true')
			
			uni.showToast({ title: '欢迎进入心邻空间 🌿', icon: 'none' })
			
			setTimeout(() => {
				uni.reLaunch({ url: '/pages/home/index' })
			}, 1000)
		} else {
			uni.showToast({ title: res?.error || '保存失败', icon: 'none' })
		}
	} catch (err) {
		console.error('Complete profile error:', err)
		uni.showToast({ title: '网络异常，请稍后再试', icon: 'none' })
	} finally {
		isLoading.value = false
	}
}
</script>

<style lang="scss">
.register-container {
	min-height: 100vh;
	background-color: $sh-bg;
	display: flex;
	flex-direction: column;
	position: relative;
	overflow: hidden;
}

.background-decor {
	position: absolute;
	top: -100rpx;
	left: -50rpx;
	width: 100%;
	z-index: 0;
	.circle {
		position: absolute;
		border-radius: 50%;
		filter: blur(60px);
	}
	.c1 {
		width: 400rpx;
		height: 400rpx;
		background: rgba($sh-primary, 0.2);
		left: -50rpx;
		top: 0;
	}
	.c2 {
		width: 300rpx;
		height: 300rpx;
		background: rgba($sh-secondary, 0.2);
		right: 100rpx;
		top: 100rpx;
	}
}

.register-box {
	flex: 1;
	z-index: 1;
	display: flex;
	flex-direction: column;
	padding: 0 50rpx;
	padding-top: calc(var(--status-bar-height) + 40rpx);
}

.logo-area {
	text-align: center;
	margin-bottom: 50rpx;
	.logo-emoji {
		font-size: 80rpx;
		margin-bottom: 16rpx;
		display: block;
	}
	.app-name {
		font-size: 40rpx;
		font-weight: 600;
		color: $sh-text-main;
		display: block;
		letter-spacing: 2rpx;
	}
	.app-slogan {
		font-size: 24rpx;
		color: $sh-text-sub;
		margin-top: 12rpx;
		display: block;
	}
}

.form-area {
	@include sh-card;
	padding: 50rpx 40rpx;
}

.avatar-section {
	display: flex;
	justify-content: center;
	margin-bottom: 40rpx;
}
.avatar-btn {
	background: none;
	border: none;
	padding: 0;
	display: flex;
	flex-direction: column;
	align-items: center;
	&::after { border: none; }
}
.avatar-img {
	width: 140rpx;
	height: 140rpx;
	border-radius: 50%;
	background: $sh-border;
}
.avatar-tip {
	font-size: 22rpx;
	color: $sh-text-sub;
	margin-top: 12rpx;
}

.input-group {
	margin-bottom: 32rpx;
	.label {
		font-size: 24rpx;
		color: $sh-text-sub;
		margin-bottom: 14rpx;
		display: block;
	}
	.required {
		color: #E57373;
		font-weight: 600;
	}
	.optional {
		color: #BBC5C0;
		font-size: 22rpx;
	}
	.input {
		height: 88rpx;
		background: $sh-bg;
		border-radius: $sh-radius-sm;
		padding: 0 30rpx;
		font-size: 30rpx;
		color: $sh-text-main;
	}
	.placeholder {
		color: #BBC5C0;
	}
}

.submit-btn {
	height: 100rpx;
	background: $sh-border;
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: $sh-text-sub;
	font-size: 32rpx;
	font-weight: 600;
	margin-top: 40rpx;
	transition: all 0.3s $sh-bezier;
	
	&.active {
		background: $sh-primary;
		color: #fff;
		box-shadow: 0 16rpx 32rpx rgba($sh-primary, 0.2);
	}
}

.privacy-tip {
	margin-top: 24rpx;
	text-align: center;
	font-size: 22rpx;
	color: $sh-text-sub;
}
</style>
