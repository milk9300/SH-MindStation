<template>
	<view class="article-container">
		<view class="article-header" v-if="article">
			<text class="title">{{ article.title }}</text>
			<view class="meta">
				<text class="author">{{ article.author }}</text>
				<text class="dot">·</text>
				<text class="date">{{ formatDate(article.created_at) }}</text>
			</view>
		</view>

		<view class="content-scroll">
			<view class="article-content" v-if="article">
				<text v-if="article.content" class="text-p">{{ article.content }}</text>
			</view>

			<!-- 评论区 -->
			<view class="comment-section" v-if="article">
				<view class="section-title">
					<text>评论 ({{ comments.length }})</text>
				</view>
				
				<view v-if="comments.length === 0" class="empty-comment">
					<text>暂无评论，快来抢沙发吧~</text>
				</view>

				<view class="comment-list">
					<view class="comment-item" v-for="item in comments" :key="item?.id">
						<template v-if="item">
							<image class="avatar" :src="item.user_avatar || '/static/default-avatar.png'" mode="aspectFill" />
							<view class="comment-main">
								<view class="comment-header">
									<text class="nickname">{{ item.user_nickname }}</text>
									<text class="time">{{ formatDate(item.created_at) }}</text>
								</view>
								<text class="comment-content">{{ item.content }}</text>
								<view class="comment-footer">
									<text class="reply-btn" @click="handleReply(item)">回复</text>
								</view>

								<!-- 回复列表 -->
								<view class="reply-list" v-if="item.replies && item.replies.length > 0">
									<view class="reply-item" v-for="reply in item.replies" :key="reply?.id">
										<template v-if="reply">
											<text class="reply-user">{{ reply.user_nickname }}</text>
											<text class="reply-content">: {{ reply.content }}</text>
										</template>
									</view>
								</view>
							</view>
						</template>
					</view>
				</view>
			</view>
		</view>

		<!-- 底部操作栏 & 评论输入框 -->
		<view class="footer-action-wrap" v-if="article">
			<view class="comment-input-bar">
				<input 
					class="input" 
					v-model="commentContent" 
					:placeholder="replyTo ? `回复 @${replyTo.user_nickname}` : '写下你的评论...'" 
					@confirm="submitComment"
					confirm-type="send"
				/>
				<text v-if="replyTo" class="cancel-reply" @click="cancelReply">取消</text>
				<view class="send-btn" @click="submitComment">
					<text :class="{ active: commentContent.trim() }">发送</text>
				</view>
			</view>
			
			<view class="action-icons">
				<view class="action-btn" :class="{ active: isFavorite }" @click="toggleFavorite">
					<text class="icon">{{ isFavorite ? '❤️' : '🤍' }}</text>
				</view>
				<view class="action-btn share" @click="doShare">
					<text class="icon">↗️</text>
				</view>
			</view>
		</view>

		<view v-if="loading" class="loading-state">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request.js'

const id = ref('')
const article = ref(null)
const loading = ref(false)
const isFavorite = ref(false)

// 评论相关
const comments = ref([])
const commentContent = ref('')
const replyTo = ref(null)
const submitting = ref(false)

const formatDate = (dateStr) => {
	if (!dateStr) return ''
	return dateStr.substring(0, 10)
}

const fetchData = async () => {
	loading.value = true
	try {
		const res = await request({
			url: `/articles/${id.value}/`,
			method: 'GET'
		})
		article.value = res
		// 检查是否已收藏
		checkFavorite()
		// 获取评论
		fetchComments()
	} catch (err) {
		console.error('Fetch article error:', err)
	} finally {
		loading.value = false
	}
}

const fetchComments = async () => {
	try {
		const res = await request({
			url: '/article-comments/',
			method: 'GET',
			data: { article: id.value }
		})
		// 兼容分页数据结构 res.results
		const list = res.results || res || []
		comments.value = Array.isArray(list) ? list.filter(c => c !== null) : []
	} catch (err) {
		console.error('Fetch comments error:', err)
	}
}

const submitComment = async () => {
	if (!commentContent.value.trim() || submitting.value) return
	
	submitting.value = true
	try {
		const res = await request({
			url: '/article-comments/',
			method: 'POST',
			data: {
				article: id.value,
				content: commentContent.value,
				parent: replyTo.value ? replyTo.value.id : null
			}
		})
		
		if (res.is_audit_passed === false) {
			uni.showToast({ title: '评论包含敏感词，将进入审核流程', icon: 'none' })
		} else {
			uni.showToast({ title: '评论成功' })
		}
		
		commentContent.value = ''
		replyTo.value = null
		fetchComments()
	} catch (err) {
		console.error('Submit comment error:', err)
		uni.showToast({ title: '提交失败，请重试', icon: 'none' })
	} finally {
		submitting.value = false
	}
}

const handleReply = (comment) => {
	replyTo.value = comment
}

const cancelReply = () => {
	replyTo.value = null
}

const checkFavorite = async () => {
	try {
		const res = await request({
			url: '/favorites/',
			method: 'GET',
			data: { target_type: 'article', target_id: id.value }
		})
		// 适配分页数据结构
		const list = res.results || res || []
		isFavorite.value = list.some(f => f.target_id === id.value && f.target_type === 'article')
	} catch (e) {
		console.error('Check favorite error:', e)
	}
}

const favSubmitting = ref(false)
const toggleFavorite = async () => {
	if (favSubmitting.value || submitting.value) return
	favSubmitting.value = true
	try {
		if (isFavorite.value) {
			// 取消收藏 (通常 DELETE 需要 ID，或者自定义 Action)
			// 这里我们为了简单，假设后端支持 POST 同一个数据切换状态，或者我们先查到收藏记录 ID
			const favorites = await request({ url: '/favorites/', method: 'GET' })
			const fav = favorites.find(f => f.target_id === id.value && f.target_type === 'article')
			if (fav) {
				await request({ url: `/favorites/${fav.id}/`, method: 'DELETE' })
				isFavorite.value = false
				uni.showToast({ title: '已取消', icon: 'none' })
			}
		} else {
			// 添加收藏
			await request({
				url: '/favorites/',
				method: 'POST',
				data: {
					target_type: 'article',
					target_id: id.value,
					target_title: article.value.title
				}
			})
			isFavorite.value = true
			uni.showToast({ title: '已收藏' })
		}
	} catch (err) {
		console.error('Toggle favorite error:', err)
	} finally {
		favSubmitting.value = false
	}
}

const doShare = () => {
	uni.showToast({ title: '点击右上角转发给好友吧', icon: 'none' })
}

onMounted(() => {
	// 获取 URL 参数 id 或 uuid (知识图谱传的是 uuid)
	const pages = getCurrentPages()
	const curPage = pages[pages.length - 1]
	if (curPage && curPage.options) {
		const targetId = curPage.options.id || curPage.options.uuid
		if (targetId) {
			id.value = targetId
			fetchData()
		}
	}
})
</script>

<style lang="scss">
.article-container {
	background: #fff;
	min-height: 100vh;
	display: flex;
	flex-direction: column;
	padding-bottom: 120rpx;
}
.article-header {
	padding: 40rpx 40rpx 20rpx;
	.title {
		font-size: 44rpx;
		font-weight: 600;
		color: $sh-text-main;
		line-height: 1.4;
		margin-bottom: 24rpx;
		display: block;
	}
	.meta {
		display: flex;
		align-items: center;
		font-size: 26rpx;
		color: $sh-text-sub;
		.author {
			color: $sh-primary;
			font-weight: 500;
		}
		.dot {
			margin: 0 12rpx;
		}
	}
}
.content-scroll {
	flex: 1;
	padding: 20rpx 40rpx;
}
.article-content {
	line-height: 1.8;
	font-size: 30rpx;
	color: $sh-text-main;
	margin-bottom: 60rpx;
	.text-p {
		white-space: pre-wrap;
		word-break: break-all;
	}
}

// 评论区样式
.comment-section {
	margin-top: 40rpx;
	border-top: 1rpx solid $sh-border;
	padding-top: 40rpx;
	.section-title {
		font-size: 32rpx;
		font-weight: 600;
		color: $sh-text-main;
		margin-bottom: 30rpx;
	}
	.empty-comment {
		padding: 60rpx 0;
		text-align: center;
		font-size: 26rpx;
		color: $sh-text-sub;
	}
	.comment-item {
		display: flex;
		margin-bottom: 40rpx;
		.avatar {
			width: 72rpx;
			height: 72rpx;
			border-radius: 50%;
			margin-right: 20rpx;
			flex-shrink: 0;
		}
		.comment-main {
			flex: 1;
			.comment-header {
				display: flex;
				justify-content: space-between;
				align-items: center;
				margin-bottom: 8rpx;
				.nickname {
					font-size: 26rpx;
					font-weight: 500;
					color: $sh-text-main;
				}
				.time {
					font-size: 22rpx;
					color: $sh-text-sub;
				}
			}
			.comment-content {
				font-size: 28rpx;
				color: $sh-text-main;
				line-height: 1.5;
				display: block;
			}
			.comment-footer {
				margin-top: 12rpx;
				.reply-btn {
					font-size: 24rpx;
					color: $sh-primary;
					font-weight: 500;
				}
			}
		}
	}
	.reply-list {
		margin-top: 16rpx;
		background: #f8f9fa;
		padding: 12rpx 20rpx;
		border-radius: 8rpx;
		.reply-item {
			font-size: 24rpx;
			line-height: 1.6;
			margin-bottom: 4rpx;
			&:last-child { margin-bottom: 0; }
			.reply-user {
				color: $sh-primary;
				font-weight: 500;
			}
			.reply-content {
				color: $sh-text-main;
			}
		}
	}
}

// 底部评论栏
.footer-action-wrap {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background: #fff;
	border-top: 1rpx solid $sh-border;
	display: flex;
	align-items: center;
	padding: 20rpx 30rpx;
	padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
	z-index: 100;
	
	.comment-input-bar {
		flex: 1;
		display: flex;
		align-items: center;
		background: #f5f5f5;
		border-radius: 40rpx;
		height: 80rpx;
		padding: 0 30rpx;
		margin-right: 20rpx;
		.input {
			flex: 1;
			font-size: 28rpx;
		}
		.cancel-reply {
			font-size: 24rpx;
			color: $sh-text-sub;
			margin-left: 20rpx;
		}
		.send-btn {
			margin-left: 20rpx;
			text {
				font-size: 28rpx;
				color: $sh-text-sub;
				font-weight: 600;
				&.active {
					color: $sh-primary;
				}
			}
		}
	}
	
	.action-icons {
		display: flex;
		align-items: center;
		.action-btn {
			margin-left: 20rpx;
			.icon {
				font-size: 44rpx;
			}
		}
	}
}
.loading-state {
	padding: 100rpx;
	text-align: center;
	color: $sh-text-sub;
}
</style>
