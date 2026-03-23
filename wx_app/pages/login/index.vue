<template>
	<view class="login-container">
		<view class="background-decor">
			<view class="circle c1"></view>
			<view class="circle c2"></view>
		</view>
		
		<view class="login-box">
			<view class="logo-area">
				<text class="logo-emoji">🌿</text>
				<text class="app-name">心邻空间</text>
				<text class="app-slogan">温润心理咨询 · 24小时陪护</text>
			</view>
			
			<view class="form-area">
				<view class="input-group">
					<text class="label">学号 / Campus ID</text>
					<input 
						class="input" 
						v-model="campusId" 
						placeholder="请输入您的学号"
						placeholder-class="placeholder"
					/>
				</view>
				
				<view class="input-group">
					<text class="label">称呼 / Nickname</text>
					<input 
						class="input" 
						v-model="nickname" 
						placeholder="想让我们怎么称呼您？"
						placeholder-class="placeholder"
					/>
				</view>
				
				<view class="login-btn" :class="{ active: canLogin }" @click="handleLogin">
					<text v-if="!isLoading">进入空间</text>
					<text v-else>正在同步账号...</text>
				</view>
				
				<view class="tip-area">
					<text class="tip">初次登录将自动为您创建心理档案</text>
				</view>
			</view>
		</view>
		
		<view class="footer">
			<text>© SH MindStation 校园心理健康安全工程</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'

const BASE_URL = 'http://127.0.0.1:8000/api'

const campusId = ref('')
const nickname = ref('')
const isLoading = ref(false)

const canLogin = computed(() => {
	// 强制要求学号和昵称都必须填写
	return campusId.value.trim().length > 0 && nickname.value.trim().length > 0
})

const handleLogin = async () => {
	if (!canLogin.value || isLoading.value) return
	
	isLoading.value = true
	try {
		// 1. 获取微信临时登录凭证 code
		console.log('正在获取微信 code...')
		const loginRes = await uni.login({
			provider: 'weixin'
		})
		
		if (!loginRes || !loginRes.code) {
			uni.showToast({ title: '微信授权失败', icon: 'none' })
			return
		}

		console.log('获取 code 成功:', loginRes.code)

		// 2. 调用后端真实微信登录接口
		const res = await uni.request({
			url: `${BASE_URL}/auth/login/`,
			method: 'POST',
			data: {
				code: loginRes.code,
				campus_id: campusId.value,
				nickname: nickname.value
			}
		})
		
		console.log('登录响应:', res)
		
		if (res && res.statusCode === 200 && res.data.token) {
			// 存储登录态
			uni.setStorageSync('student_token', res.data.token)
			uni.setStorageSync('student_user', JSON.stringify(res.data.user))
			
			uni.showToast({ title: '欢迎进入心邻空间', icon: 'success' })
			
			// 跳转回首页
			setTimeout(() => {
				uni.reLaunch({ url: '/pages/home/index' })
			}, 1000)
		} else {
			const errorMsg = (res && res.data && res.data.error) || '登录失败'
			uni.showToast({ title: errorMsg, icon: 'none' })
		}
	} catch (err) {
		console.error('Login error:', err)
		uni.showToast({ title: '联机失败，请检查网络', icon: 'none' })
	} finally {
		isLoading.value = false
	}
}
</script>

<style lang="scss">
.login-container {
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

.login-box {
	flex: 1;
	z-index: 1;
	display: flex;
	flex-direction: column;
	justify-content: center;
	padding: 0 60rpx;
	margin-top: -100rpx;
}

.logo-area {
	text-align: center;
	margin-bottom: 80rpx;
	.logo-emoji {
		font-size: 100rpx;
		margin-bottom: 20rpx;
		display: block;
	}
	.app-name {
		font-size: 48rpx;
		font-weight: 600;
		color: $sh-text-main;
		display: block;
		letter-spacing: 2rpx;
	}
	.app-slogan {
		font-size: 24rpx;
		color: $sh-text-sub;
		margin-top: 16rpx;
		display: block;
	}
}

.form-area {
	@include sh-card;
	padding: 60rpx 40rpx;
}

.input-group {
	margin-bottom: 40rpx;
	.label {
		font-size: 24rpx;
		color: $sh-text-sub;
		margin-bottom: 16rpx;
		display: block;
	}
	.input {
		height: 90rpx;
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

.login-btn {
	height: 100rpx;
	background: $sh-border;
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: $sh-text-sub;
	font-size: 32rpx;
	font-weight: 600;
	margin-top: 60rpx;
	transition: all 0.3s $sh-bezier;
	
	&.active {
		background: $sh-primary;
		color: #fff;
		box-shadow: 0 16rpx 32rpx rgba($sh-primary, 0.2);
	}
}

.tip-area {
	margin-top: 30rpx;
	text-align: center;
	.tip {
		font-size: 22rpx;
		color: $sh-text-sub;
	}
}

.footer {
	padding-bottom: 40rpx;
	text-align: center;
	.copyright {
		font-size: 20rpx;
		color: #BBC5C0;
	}
}
</style>
