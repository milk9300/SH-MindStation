<template>
	<view class="sidebar-drawer" :class="{ 'show': show }">
		<view class="drawer-mask" @click="$emit('close')"></view>
		<view class="drawer-content">
			<!-- 用户资料区 -->
			<view class="user-profile-section" :style="{ paddingTop: (statusBarHeight + 20) + 'px' }" @click="goToProfile">
				<image class="avatar" :src="userInfo.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
				<view class="user-meta">
					<text class="nickname">{{ userInfo.nickname || '同学' }}</text>
					<text class="view-profile">查看个人中心 ›</text>
				</view>
			</view>

			<!-- 核心功能矩阵 (Kimi 风格) -->
			<view class="function-matrix">
				<view class="matrix-item" @click="navigateTo('/pages/home/index')">
					<view class="icon-wrap article"><text>📄</text></view>
					<text class="label">文章</text>
				</view>
				<view class="matrix-item" @click="navigateTo('/pages/discovery/index')">
					<view class="icon-wrap assessment"><text>📊</text></view>
					<text class="label">测评</text>
				</view>
				<view class="matrix-item" @click="navigateTo('/pages/knowledge/index')">
					<view class="icon-wrap knowledge"><text>📚</text></view>
					<text class="label">知识库</text>
				</view>
			</view>

			<!-- 新咨询及历史列表 -->
			<view class="action-list-area">
				<view class="new-chat-btn" @click="$emit('new-chat')">
					<view class="plus-icon-box">+</view>
					<text>开启新咨询</text>
				</view>

				<scroll-view 
					scroll-y 
					class="history-scroll"
				>
					<view v-for="group in groupedHistory" :key="group.label" class="history-group">
						<view class="history-label">{{ group.label }}</view>
						<view 
							v-for="sess in group.items" 
							:key="sess.id"
							class="history-item"
							:class="{ active: currentSessionId === sess.id }"
							@click="$emit('load-session', sess.id)"
						>
							<text class="item-title">{{ sess.title || '无标题会话' }}</text>
						</view>
					</view>
					<view v-if="historySessions.length === 0 && !loadingMore" class="empty-history">暂无历史记录</view>
					
					<!-- 加载更多逻辑改为点击触发 -->
					<view class="pagination-area" v-if="historySessions.length > 0">
						<view v-if="loadingMore" class="load-more-status">
							<text class="loading-icon">⏳</text>
							<text>正在加载...</text>
						</view>
						<view 
							v-else-if="hasMore" 
							class="load-more-btn" 
							@click="$emit('load-more')"
						>
							<text>点击查看更多历史</text>
						</view>
						<view v-else class="no-more-status">
							<text>没有更多历史记录了</text>
						</view>
					</view>
				</scroll-view>
			</view>

			<!-- 底部设置/退出等 (可选) -->
			<view class="sidebar-footer">
				<text class="version">SH MindStation v1.1</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'

const props = defineProps({
	show: Boolean,
	userInfo: {
		type: Object,
		default: () => ({})
	},
	historySessions: {
		type: Array,
		default: () => []
	},
	currentSessionId: String,
	statusBarHeight: {
		type: Number,
		default: 20
	},
	loadingMore: Boolean,
	hasMore: {
		type: Boolean,
		default: true
	}
})

const emit = defineEmits(['close', 'new-chat', 'load-session', 'load-more'])

// 历史记录按日期分组逻辑
const groupedHistory = computed(() => {
	const groups = [
		{ label: '今天', items: [] },
		{ label: '昨天', items: [] },
		{ label: '最近7天', items: [] },
		{ label: '更早之前', items: [] }
	]

	const now = new Date()
	const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
	const yesterdayStart = todayStart - 24 * 60 * 60 * 1000
	const last7DaysStart = todayStart - 7 * 24 * 60 * 60 * 1000

	props.historySessions.forEach(sess => {
		// 优先取 updated_at，其次 created_at
		const timeStr = sess.updated_at || sess.created_at
		const time = timeStr ? new Date(timeStr).getTime() : Date.now()
		
		if (time >= todayStart) groups[0].items.push(sess)
		else if (time >= yesterdayStart) groups[1].items.push(sess)
		else if (time >= last7DaysStart) groups[2].items.push(sess)
		else groups[3].items.push(sess)
	})

	// 只返回有内容的组
	return groups.filter(g => g.items.length > 0)
})

const goToProfile = () => {
	uni.navigateTo({ url: '/pages/profile/index' })
	emit('close')
}

const navigateTo = (url) => {
	uni.navigateTo({ url })
	emit('close')
}
</script>

<style lang="scss" scoped>
.sidebar-drawer {
	position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1000; pointer-events: none;
	&.show {
		pointer-events: auto;
		.drawer-mask { opacity: 1; }
		.drawer-content { transform: translateX(0); }
	}
	.drawer-mask { position: absolute; width: 100%; height: 100%; background: rgba(0,0,0,0.5); opacity: 0; transition: opacity 0.3s; backdrop-filter: blur(2px); }
	
	.drawer-content {
		position: absolute; width: 80%; height: 100%; background: #fff; transform: translateX(-100%); transition: transform 0.3s $sh-bezier; display: flex; flex-direction: column; box-shadow: 20rpx 0 60rpx rgba(0,0,0,0.1);
		
		.user-profile-section {
			padding: 40rpx 40rpx 30rpx; display: flex; align-items: center; gap: 24rpx; background: linear-gradient(to bottom, #F7FAF9, #fff);
			.avatar { width: 110rpx; height: 110rpx; border-radius: 50%; border: 4rpx solid #fff; box-shadow: 0 4rpx 15rpx rgba(0,0,0,0.05); }
			.user-meta { display: flex; flex-direction: column; gap: 4rpx; .nickname { font-size: 36rpx; font-weight: 700; color: $sh-text-main; } .view-profile { font-size: 24rpx; color: $sh-text-sub; } }
		}

		.function-matrix {
			display: flex; justify-content: space-around; padding: 30rpx 20rpx; border-bottom: 1rpx solid #f5f5f5;
			.matrix-item {
				display: flex; flex-direction: column; align-items: center; gap: 12rpx;
				.icon-wrap {
					width: 100rpx; height: 100rpx; border-radius: 30rpx; display: flex; align-items: center; justify-content: center; font-size: 40rpx; transition: all 0.2s;
					&:active { transform: scale(0.9); }
					&.article { background-color: #E8F0FE; color: #4285F4; }
					&.assessment { background-color: #E6F4EA; color: #34A853; }
					&.knowledge { background-color: #FEF7E0; color: #FABB05; }
				}
				.label { font-size: 26rpx; color: $sh-text-main; font-weight: 500; }
			}
		}

		.action-list-area {
			flex: 1; display: flex; flex-direction: column; padding: 40rpx 30rpx; overflow: hidden;
			.new-chat-btn {
				display: flex; align-items: center; gap: 20rpx; padding: 28rpx; background: rgba($sh-primary, 0.08); border-radius: 20rpx; color: $sh-primary; font-weight: 600; font-size: 30rpx; margin-bottom: 40rpx;
				.plus-icon-box { width: 44rpx; height: 44rpx; background: $sh-primary; color: #fff; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; font-size: 32rpx; }
				&:active { opacity: 0.7; }
			}
			.history-scroll {
				flex: 1; 
				min-height: 0; /* 关键：解决 flex 布局下 scroll-view 高度撑开导致无法滚动的问题 */
				.history-group { margin-bottom: 40rpx; }
				.history-label { font-size: 24rpx; color: $sh-text-sub; font-weight: bold; margin-bottom: 20rpx; padding-left: 10rpx; text-transform: uppercase; letter-spacing: 1rpx; }
				.history-item {
					padding: 24rpx 20rpx; display: flex; align-items: center; gap: 20rpx; border-radius: 16rpx; margin-bottom: 10rpx; transition: background 0.2s;
					&.active { background: #f0f7f4; .item-title { font-weight: 600; color: $sh-primary; } .item-icon { color: $sh-primary; } }
					.item-icon { font-size: 32rpx; color: #999; }
					.item-title { font-size: 28rpx; color: $sh-text-main; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
					&:active { background: #f9f9f9; }
				}
				.empty-history { text-align: center; color: #ccc; font-size: 24rpx; padding: 40rpx 0; }
				
				.load-more-status, .no-more-status, .load-more-btn {
					text-align: center;
					padding: 30rpx 0;
					font-size: 24rpx;
					color: $sh-text-sub;
					.loading-icon {
						margin-right: 10rpx;
						display: inline-block;
						animation: rotating 2s linear infinite;
					}
				}
				
				.load-more-btn {
					color: $sh-primary;
					background: rgba($sh-primary, 0.05);
					border-radius: 12rpx;
					margin: 10rpx 0;
					font-weight: 500;
					&:active {
						opacity: 0.6;
						background: rgba($sh-primary, 0.1);
					}
				}
			}
		}

		@keyframes rotating {
			from { transform: rotate(0deg); }
			to { transform: rotate(360deg); }
		}

		.sidebar-footer { padding: 30rpx; text-align: center; .version { font-size: 20rpx; color: #ddd; } }
	}
}
</style>
