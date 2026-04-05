<template>
	<view class="knowledge-page">
		<!-- === Discovery Home Mode === -->
		<view class="home-header">
			<view class="search-bar">
				<view class="search-input-wrap">
					<text class="icon">🔍</text>
					<input 
						class="input" 
						type="text" 
						placeholder="搜索心理知识、政策、应对技巧..." 
						v-model="searchQuery"
						@input="onSearchInput"
					/>
					<text class="clear" v-if="searchQuery" @click="clearSearch">x</text>
				</view>
			</view>
			
			<!-- Hot Search Tags -->
			<view class="hot-tags" v-if="hotTags.length">
				<text class="label">大家都在搜：</text>
				<scroll-view scroll-x class="tag-scroll" :show-scrollbar="false">
					<view 
						class="tag-item" 
						v-for="(tag, idx) in hotTags" 
						:key="idx"
						@click="quickSearch(tag)"
					>
						{{ tag }}
					</view>
				</scroll-view>
			</view>
		</view>

		<!-- Category Tabs -->
		<view class="category-tabs">
			<scroll-view scroll-x class="tab-scroll" :show-scrollbar="false">
				<view 
					v-for="cat in categories" 
					:key="cat.id"
					class="tab-item"
					:class="{ active: activeCategory === cat.id }"
					@click="switchCategory(cat.id)"
				>
					{{ cat.name }}
				</view>
			</scroll-view>
		</view>

		<!-- Entity List -->
		<scroll-view 
			scroll-y 
			class="entity-list-scroll"
			@scrolltolower="onLoadMore"
		>
			<view class="list-container">
				<view 
					v-for="item in entities" 
					:key="item.uuid" 
					class="entity-item animate-fade-in"
					@click="handleItemClick(item)"
				>
					<view class="custom-card" :class="getLabelClass(item.label)">
						<view class="card-left" v-if="item.cover">
							<image :src="item.cover" mode="aspectFill" class="cover" />
						</view>
						<view class="card-right">
							<view class="title-row">
								<text class="label-badge">{{ item.label }}</text>
								<text class="title">{{ item.name }}</text>
							</view>
							<text class="summary">{{ item.content }}</text>
						</view>
					</view>
				</view>

				<!-- Load More Status -->
				<view class="load-more-status" v-if="entities.length > 0">
					<view class="loading-more" v-if="isLoadingMore">
						<view class="mini-spinner"></view>
						<text>努力加载中...</text>
					</view>
					<text class="no-more" v-else-if="noMoreData">—— 已展示全部内容 ——</text>
					<text class="load-tip" v-else>向上滑动加载更多</text>
				</view>

				<!-- Empty State -->
				<view class="empty-state" v-if="!entities.length && !isLoading && !isLoadingMore">
					<image src="/static/images/empty_kg.png" mode="aspectFit" class="empty-img" />
					<text>没有找到相关内容</text>
				</view>
			</view>
		</scroll-view>

		<!-- Initial Loading State -->
		<view class="loading-overlay" v-if="isLoading && !isLoadingMore">
			<view class="spinner"></view>
			<text>正在探索图谱...</text>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/utils/request.js'

// --- State ---
const isLoading = ref(true)
const isLoadingMore = ref(false)
const noMoreData = ref(false)
const searchQuery = ref('')
const activeCategory = ref('全部')
const categories = ref([])
const hotTags = ref([])
const entities = ref([])

const page = ref(1)
const pageSize = ref(30)

// --- Lifecycle ---
onLoad(() => {
	fetchHomeData()
})

// --- Logic ---
const fetchHomeData = async (isLoadMore = false) => {
	if (isLoadMore) {
		isLoadingMore.value = true
	} else {
		isLoading.value = true
		page.value = 1
		noMoreData.value = false
		// 如果不是加载更多，清空列表防止闪烁（或者可以用 Skeleton）
		// entities.value = [] 
	}

	try {
		const res = await request({
			url: '/graph/knowledge-base/home/',
			method: 'GET',
			data: {
				q: searchQuery.value,
				label: activeCategory.value,
				page: page.value,
				page_size: pageSize.value
			}
		})
		
		// 初始加载时更新分类和热门标签
		if (!isLoadMore) {
			categories.value = res.categories
			hotTags.value = res.hot_tags
			entities.value = res.entities
		} else {
			// 加载更多时追加数据
			entities.value = [...entities.value, ...res.entities]
		}
		
		// 根据返回的数据量或 has_more 标志判断是否还有更多
		if (res.pagination) {
			noMoreData.value = !res.pagination.has_more
		} else {
			// 降级判断：如果返回数量少于 pageSize，说明没数据了
			noMoreData.value = res.entities.length < pageSize.value
		}
		
	} catch (e) {
		uni.showToast({ title: '数据加载失败', icon: 'none' })
	} finally {
		isLoading.value = false
		isLoadingMore.value = false
	}
}

const onLoadMore = () => {
	if (isLoadingMore.value || noMoreData.value || isLoading.value) return
	page.value++
	fetchHomeData(true)
}

let searchTimer = null
const onSearchInput = () => {
	if (searchTimer) clearTimeout(searchTimer)
	searchTimer = setTimeout(() => {
		fetchHomeData()
	}, 500)
}

const clearSearch = () => {
	searchQuery.value = ''
	fetchHomeData()
}

const quickSearch = (tag) => {
	searchQuery.value = tag
	fetchHomeData()
}

const switchCategory = (cid) => {
	activeCategory.value = cid
	fetchHomeData()
}

const getLabelClass = (label) => {
	const map = {
		'心理问题': 'crisis',
		'应对技巧': 'treatment',
		'校园政策': 'policy',
		'症状': 'symptom',
		'文章': 'article',
		'科普文章': 'article'
	}
	return map[label] || ''
}

const handleItemClick = (item) => {
	if (item.label === '心理问题') {
		uni.navigateTo({
			url: `/pages/knowledge/detail?uuid=${item.uuid}`
		})
	} else if (item.label === '文章' || item.label === '科普文章') {
		uni.navigateTo({
			url: `/pages/discovery/article-detail?uuid=${item.uuid}`
		})
	} else {
		uni.navigateTo({
			url: `/pages/knowledge/entity?uuid=${item.uuid}`
		})
	}
}
</script>

<style lang="scss" scoped>
.knowledge-page {
	height: 100vh; background-color: #F8FBF9; display: flex; flex-direction: column;
}

.home-header {
	background: linear-gradient(135deg, $sh-primary, #6AA285);
	padding: 40rpx 30rpx 40rpx;
	.search-bar {
		.search-input-wrap {
			background: rgba(255, 255, 255, 0.95);
			height: 88rpx; border-radius: 44rpx;
			display: flex; align-items: center; padding: 0 30rpx;
			box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
			.icon { color: $sh-text-sub; margin-right: 16rpx; font-size: 32rpx; }
			.input { flex: 1; font-size: 28rpx; color: $sh-text-main; }
			.clear { color: $sh-text-sub; padding: 10rpx; font-size: 24rpx; }
		}
	}
	.hot-tags {
		margin-top: 30rpx; display: flex; align-items: center;
		.label { font-size: 22rpx; color: rgba(255, 255, 255, 0.8); flex-shrink: 0; }
		.tag-scroll { white-space: nowrap; flex: 1; margin-left: 10rpx; overflow: hidden;
			.tag-item { 
				display: inline-block; padding: 6rpx 20rpx; background: rgba(255, 255, 255, 0.15);
				border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 30rpx;
				color: #fff; font-size: 22rpx; margin-right: 16rpx;
				&:active { background: rgba(255, 255, 255, 0.3); }
			}
		}
	}
}

.category-tabs {
	background: #fff; border-bottom: 1px solid #f0f0f0;
	.tab-scroll { white-space: nowrap; height: 90rpx; 
		.tab-item {
			display: inline-block; height: 90rpx; line-height: 90rpx;
			padding: 0 40rpx; font-size: 28rpx; color: $sh-text-sub;
			position: relative; transition: all 0.3s;
			&.active {
				color: $sh-primary; font-weight: bold;
				&::after {
					content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%);
					width: 40%; height: 6rpx; background: $sh-primary; border-radius: 10rpx;
				}
			}
		}
	}
}

.entity-list-scroll { flex: 1; overflow: hidden; }
.list-container { padding: 30rpx; padding-bottom: 60rpx; }

.custom-card {
	background: #fff; border-radius: 20rpx; padding: 24rpx; margin-bottom: 24rpx;
	display: flex; gap: 20rpx; box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.02);
	border: 1px solid rgba(0, 0, 0, 0.01);
	
	.card-left { .cover { width: 140rpx; height: 140rpx; border-radius: 12rpx; } }
	.card-right { flex: 1; display: flex; flex-direction: column; justify-content: center;
		.title-row { 
			display: flex; align-items: flex-start; gap: 12rpx; margin-bottom: 12rpx;
			.label-badge { 
				font-size: 20rpx; padding: 2rpx 12rpx; border-radius: 6rpx; 
				background: #F0F5F2; color: $sh-primary; white-space: nowrap;
			}
			.title { font-size: 30rpx; font-weight: bold; color: $sh-text-main; line-height: 1.3; }
		}
		.summary { font-size: 24rpx; color: $sh-text-sub; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
	}
	
	&.crisis { border-left: 8rpx solid #FF4D4F; .label-badge { background: #FFF1F0; color: #FF4D4F; } }
	&.treatment { border-left: 8rpx solid $sh-primary; .label-badge { background: #F6FFED; color: $sh-primary; } }
	&.policy { border-left: 8rpx solid #1890FF; .label-badge { background: #E6F7FF; color: #1890FF; } }
	&.symptom { border-left: 8rpx solid #722ED1; .label-badge { background: #F9F0FF; color: #722ED1; } }
	&.article { border-left: 8rpx solid #FAAD14; .label-badge { background: #FFF7E6; color: #FAAD14; } }
}

.load-more-status {
	padding: 40rpx 0; text-align: center;
	.loading-more { 
		display: flex; align-items: center; justify-content: center; gap: 12rpx;
		color: $sh-text-sub; font-size: 24rpx;
		.mini-spinner { 
			width: 24rpx; height: 24rpx; border: 2rpx solid #eee; border-top-color: $sh-primary; 
			border-radius: 50%; animation: spin 0.8s linear infinite;
		}
	}
	.no-more { color: #ccc; font-size: 22rpx; letter-spacing: 2rpx; }
	.load-tip { color: $sh-text-sub; font-size: 22rpx; opacity: 0.6; }
}

.empty-state {
	padding: 100rpx 0; display: flex; flex-direction: column; align-items: center; color: $sh-text-sub; font-size: 26rpx;
	.empty-img { width: 240rpx; height: 240rpx; margin-bottom: 30rpx; opacity: 0.5; }
}

.loading-overlay { 
	position: fixed; inset: 0; background: rgba(255, 255, 255, 0.8); z-index: 100; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20rpx;
	.spinner { width: 60rpx; height: 60rpx; border: 4rpx solid #f3f3f3; border-top: 4rpx solid $sh-primary; border-radius: 50%; animation: spin 1s linear infinite; }
	text { font-size: 26rpx; color: $sh-text-sub; }
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.animate-fade-in { animation: fadeIn 0.6s ease-out both; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10rpx); } to { opacity: 1; transform: translateY(0); } }
</style>
