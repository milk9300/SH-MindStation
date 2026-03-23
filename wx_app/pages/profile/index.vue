<template>
	<view class="container">
		<view class="user-card">
			<view class="avatar-area">
				<image class="avatar-img" :src="userInfo.avatar_url ? userInfo.avatar_url : '/static/default-avatar.png'" mode="aspectFill" />
				<view class="user-info">
					<view class="name-row">
						<text class="username">{{ userInfo.nickname || '同学' }}</text>
						<text class="real-name" v-if="userInfo.real_name">({{ userInfo.real_name }})</text>
					</view>
					<text class="campus-id">学号：{{ userInfo.campus_id || '未绑定' }}</text>
					<text class="phone" v-if="userInfo.phone">手机：{{ userInfo.phone }}</text>
				</view>
			</view>
		</view>
		
		<view class="menu-group">
			<view class="menu-item" @click="goToMood">
				<text class="menu-icon">📝</text>
				<text class="menu-label">心情手记</text>
				<text class="menu-arrow">›</text>
			</view>
			<view class="menu-item" @click="goToFavorites">
				<text class="menu-icon">⭐</text>
				<text class="menu-label">我的收藏</text>
				<text class="menu-arrow">›</text>
			</view>
			<view class="menu-item" @click="goToRecords">
				<text class="menu-icon">📊</text>
				<text class="menu-label">测评记录</text>
				<text class="menu-arrow">›</text>
			</view>
		</view>
		
		<view class="menu-group">
			<view class="menu-item" @click="goToAbout">
				<text class="menu-icon">ℹ️</text>
				<text class="menu-label">关于我们</text>
				<text class="menu-arrow">›</text>
			</view>
			<view class="menu-item" @click="goToHotline">
				<text class="menu-icon">📞</text>
				<text class="menu-label">紧急求助热线</text>
				<text class="menu-arrow">›</text>
			</view>
		</view>
		
		<view class="logout-area">
			<view class="logout-btn" @click="doLogout">退出登录</view>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const userInfo = ref({
	nickname: '匿名同学',
	real_name: '',
	campus_id: '未绑定',
	phone: '',
	avatar_url: ''
})

onMounted(() => {
	const userStr = uni.getStorageSync('student_user')
	if (userStr) {
		try {
			const user = JSON.parse(userStr)
			userInfo.value = {
				nickname: user.nickname || '同学',
				real_name: user.real_name || '',
				campus_id: user.campus_id || '未绑定',
				phone: user.phone || '',
				avatar_url: user.avatar_url || ''
			}
		} catch (e) {}
	}
})

const goToMood = () => {
	uni.navigateTo({ url: '/pages/mood/index' })
}

const goToFavorites = () => {
	uni.navigateTo({ url: '/pages/profile/favorites' })
}

const goToRecords = () => {
	uni.navigateTo({ url: '/pages/profile/records' })
}

const goToAbout = () => {
	uni.showToast({ title: 'SH MindStation v1.0', icon: 'none' })
}

const goToHotline = () => {
	uni.makePhoneCall({
		phoneNumber: '021-12345678' // 示例热线
	})
}
const doLogout = () => {
	uni.showModal({
		title: '确认退出',
		content: '退出后需要重新登录',
		success: (res) => {
			if (res.confirm) {
				uni.removeStorageSync('student_token')
				uni.removeStorageSync('student_user')
				uni.reLaunch({ url: '/pages/login/index' })
			}
		}
	})
}
</script>

<style lang="scss">
.container {
	padding: 30rpx;
	background: $sh-bg;
	min-height: 100vh;
}
.user-card {
	@include sh-card;
	margin-bottom: 30rpx;
	padding: 40rpx;
}
.avatar-area {
	display: flex;
	align-items: center;
}
.avatar-img {
	width: 100rpx;
	height: 100rpx;
	border-radius: 50%;
	margin-right: 24rpx;
	background: $sh-border;
}
.avatar {
	width: 100rpx;
	height: 100rpx;
	border-radius: 50%;
	background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 48rpx;
	margin-right: 24rpx;
}
.user-info {
	display: flex;
	flex-direction: column;
	.name-row {
		display: flex;
		align-items: center;
		margin-bottom: 8rpx;
		.username {
			font-size: 34rpx;
			font-weight: 600;
			color: $sh-text-main;
		}
		.real-name {
			font-size: 24rpx;
			color: $sh-text-sub;
			margin-left: 12rpx;
		}
	}
	.campus-id {
		font-size: 24rpx;
		color: $sh-text-sub;
	}
	.phone {
		font-size: 22rpx;
		color: $sh-text-sub;
		margin-top: 4rpx;
	}
}
.menu-group {
	@include sh-card;
	margin-bottom: 30rpx;
	padding: 0;
	overflow: hidden;
}
.menu-item {
	display: flex;
	align-items: center;
	padding: 30rpx;
	border-bottom: 1rpx solid $sh-border;
	&:last-child {
		border-bottom: none;
	}
	.menu-icon {
		font-size: 36rpx;
		margin-right: 20rpx;
	}
	.menu-label {
		flex: 1;
		font-size: 28rpx;
		color: $sh-text-main;
	}
	.menu-arrow {
		font-size: 36rpx;
		color: $sh-text-sub;
	}
}
.logout-area {
	margin-top: 60rpx;
	text-align: center;
}
.logout-btn {
	display: inline-block;
	padding: 20rpx 80rpx;
	border-radius: $sh-radius-lg;
	border: 2rpx solid $sh-error;
	color: $sh-error;
	font-size: 28rpx;
}
</style>
