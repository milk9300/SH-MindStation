<template>
	<view class="chat-page-container">
		<!-- 1. Header: 左侧对齐，带快速新建按钮 -->
		<ChatHeader 
			:statusBarHeight="statusBarHeight" 
			@toggle-sidebar="toggleSidebar"
			@new-chat="startNewChat"
		/>

		<!-- 2. Sidebar Drawer -->
		<ChatSidebar 
			:show="showSidebar"
			:userInfo="userInfo"
			:historySessions="historySessions"
			:currentSessionId="sessionId"
			:statusBarHeight="statusBarHeight"
			:loadingMore="historyLoadingMore"
			:hasMore="historyHasMore"
			@close="showSidebar = false"
			@new-chat="startNewChat"
			@load-session="loadSession"
			@load-more="handleLoadMore"
		/>

		<!-- 3. Message List: 全屏滚动，顶部和底部留出 fixed 区域 -->
		<ChatMessageList 
			:messages="messages"
			:loading="isLoading"
			:scrollTop="scrollTop"
			:headerHeight="headerHeight"
			@select-option="handleOptionClick"
		>
			<template #welcome>
				<WelcomeSection 
					:show="messages.length === 0"
					:nickname="userInfo.nickname"
					:guidanceQuestions="guidanceQuestions"
					@select-guidance="selectGuidance"
				/>
			</template>
		</ChatMessageList>

		<!-- 4. Progress Bar (仅在非空且非纯展示态显示) -->
		<view class="session-progress" v-if="messages.length > 0">
			<view class="progress-inner">
				<view class="progress-item" :class="{ completed: currentSlots.event }">
					<view class="dot"><text v-if="currentSlots.event">✓</text></view>
					<text class="label">核心事件</text>
				</view>
				<view class="progress-line"></view>
				<view class="progress-item" :class="{ completed: currentSlots.duration }">
					<view class="dot"><text v-if="currentSlots.duration">✓</text></view>
					<text class="label">持续时间</text>
				</view>
				<view class="progress-line"></view>
				<view class="progress-item" :class="{ completed: currentSlots.impact }">
					<view class="dot"><text v-if="currentSlots.impact">✓</text></view>
					<text class="label">身心影响</text>
				</view>
			</view>
		</view>

		<!-- 5. Input Area: 始终显示，支持在任何历史记录中追问 -->
		<ChatInputArea 
			v-model="inputText"
			:inputMode="inputMode"
			:isRecording="isRecording"
			@toggle-mode="toggleMode"
			@send="sendMessage"
			@start-voice="startVoice"
			@stop-voice="stopVoice"
		/>
	</view>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import request from '@/utils/request.js'

// 导入组件化子模块
import ChatHeader from '@/components/chat/ChatHeader.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMessageList from '@/components/chat/ChatMessageList.vue'
import ChatInputArea from '@/components/chat/ChatInputArea.vue'
import WelcomeSection from '@/components/chat/WelcomeSection.vue'

// 1. UI 基础状态
const statusBarHeight = ref(uni.getSystemInfoSync().statusBarHeight || 20)
// Header 总高度 = 状态栏 + 导航内容区(88rpx ≈ 44px)
const headerHeight = ref(statusBarHeight.value + 44)
const showSidebar = ref(false)
const historySessions = ref([])
const historyPage = ref(1)
const historyHasMore = ref(true)
const historyLoadingMore = ref(false)
const userInfo = ref({ nickname: '同学', avatar_url: '' })

// 2. 对话核心状态
const inputText = ref('')
const messages = ref([])
const isLoading = ref(false)
const scrollTop = ref(0)
const sessionId = ref('')
const guidanceQuestions = ref([])
const currentSlots = ref({ event: null, duration: null, impact: null })

// 3. 录音功能逻辑
const recorderManager = uni.getRecorderManager()
const inputMode = ref('text')
const isRecording = ref(false)

const initVoice = () => {
	recorderManager.onStop((res) => {
		if (res.duration < 800) {
			uni.showToast({ title: '录制时间太短', icon: 'none' })
			return
		}
		uploadVoice(res.tempFilePath)
	})
}

const toggleMode = () => inputMode.value = inputMode.value === 'text' ? 'voice' : 'text'

const startVoice = () => {
	uni.authorize({
		scope: 'scope.record',
		success: () => {
			isRecording.value = true
			uni.vibrateShort()
			recorderManager.start({ format: 'aac' })
		},
		fail: () => uni.showToast({ title: '需要麦克风权限', icon: 'none' })
	})
}

const stopVoice = () => {
	isRecording.value = false
	recorderManager.stop()
}

const uploadVoice = (filePath) => {
	uni.showLoading({ title: '识别中...' })
	const token = uni.getStorageSync('student_token')
	uni.uploadFile({
		url: 'http://127.0.0.1:8000/api/chat/stt/',
		filePath: filePath,
		name: 'audio',
		header: { 'Authorization': token },
		success: (res) => {
			if (res.statusCode === 200) {
				const data = JSON.parse(res.data)
				if (data.text) {
					inputText.value = data.text
					inputMode.value = 'text'
				}
			}
		},
		complete: () => uni.hideLoading()
	})
}

// 4. 会话管理逻辑
const toggleSidebar = () => {
	showSidebar.value = !showSidebar.value
	if (showSidebar.value) {
		// 每次打开侧边栏，重置并刷新第一页记录
		historyPage.value = 1
		historyHasMore.value = true
		fetchHistoryList(true)
	}
}

const fetchHistoryList = async (isReset = false) => {
	if (historyLoadingMore.value || (!historyHasMore.value && !isReset)) return
	
	historyLoadingMore.value = true
	try {
		const res = await request({ 
			url: '/chat-sessions/', 
			method: 'GET',
			data: { page: historyPage.value }
		})
		const newList = res.results || res || []
		
		if (isReset) {
			historySessions.value = newList
		} else {
			// 追加新数据并进行去重处理 (防止后端分页抖动产生的重复记录)
			const existingIds = new Set(historySessions.value.map(s => s.id))
			const filteredNew = newList.filter(s => !existingIds.has(s.id))
			historySessions.value = [...historySessions.value, ...filteredNew]
		}
		
		// 判断是否还有下一页
		historyHasMore.value = !!res.next
		if (historyHasMore.value) {
			historyPage.value++
		}
	} catch (e) {
		console.error('Fetch history failed', e)
	} finally {
		historyLoadingMore.value = false
	}
}

const handleLoadMore = () => {
	fetchHistoryList(false)
}

const loadSession = async (sid) => {
	showSidebar.value = false
	sessionId.value = sid
	uni.showLoading({ title: '加载中...' })
	try {
		const data = await request({ url: `/chat-sessions/${sid}/`, method: 'GET' })
		if (data) {
			messages.value = data.messages || []
			currentSlots.value = data.current_slots || { event: null, duration: null, impact: null }
			uni.setStorageSync('active_session_id', sid)
			scrollToBottom()
		}
	} catch (e) {
		if (e.statusCode === 404) startNewChat()
		else uni.showToast({ title: '加载失败', icon: 'none' })
	} finally {
		uni.hideLoading()
	}
}

const startNewChat = () => {
	// 如果当前已经是新会话且没有聊天内容，提示用户
	if (!sessionId.value && messages.value.length === 0) {
		uni.showToast({
			title: '目前已经是新对话',
			icon: 'none'
		})
		return
	}

	showSidebar.value = false
	sessionId.value = ''
	messages.value = []
	currentSlots.value = { event: null, duration: null, impact: null }
	uni.removeStorageSync('active_session_id')
	fetchGuidance()
}

const fetchGuidance = async () => {
	try {
		const data = await request({ url: '/guidance-questions/?count=5', method: 'GET' })
		guidanceQuestions.value = data
	} catch (e) {}
}

const selectGuidance = (text) => {
	inputText.value = text
	sendMessage()
}

const generateSessionId = () => {
	const sid = 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8)
	sessionId.value = sid
	uni.setStorageSync('active_session_id', sid)
	return sid
}

// 5. 对话核心流程
const sendMessage = async () => {
	const text = inputText.value.trim()
	if (!text || isLoading.value) return
	if (!sessionId.value) generateSessionId()
	
	messages.value.push({ role: 'user', content: text, isNew: true })
	inputText.value = ''
	scrollToBottom()
	isLoading.value = true
	
	try {
		const data = await request({
			url: '/chat/interact/',
			method: 'POST',
			data: { session_id: sessionId.value, content: text }
		})
		if (data && data.reply) {
			messages.value.push({
				role: 'ai',
				content: data.reply,
				options: data.options || [],
				cards: data.structured_cards || [],
				suggested_assessment: data.suggested_assessment || null,
				knowledge_base_uuid: data.knowledge_base_uuid,
				isNew: true
			})
			if (data.debug_slots) currentSlots.value = data.debug_slots
			// 如果是新会话，刷新一下历史列表以反映最新状态
			fetchHistoryList()
		}
	} catch (err) {
		console.error('Chat error:', err)
	} finally {
		isLoading.value = false
		scrollToBottom()
	}
}

const handleOptionClick = async (option) => {
	if (isLoading.value) return
	messages.value.push({ role: 'user', content: `我想了解：${option.name}`, isNew: true })
	scrollToBottom()
	isLoading.value = true
	try {
		const data = await request({
			url: '/chat/interact/',
			method: 'POST',
			data: { session_id: sessionId.value, selected_node_uuid: option.uuid, content: '' }
		})
		if (data && data.reply) {
			messages.value.push({
				role: 'ai',
				content: data.reply,
				options: data.options || [],
				cards: data.structured_cards || [],
				suggested_assessment: data.suggested_assessment || null,
				knowledge_base_uuid: data.knowledge_base_uuid,
				isNew: true
			})
		}
	} catch (err) {} finally {
		isLoading.value = false
		scrollToBottom()
	}
}

const scrollToBottom = () => {
	nextTick(() => {
		setTimeout(() => { scrollTop.value = scrollTop.value >= 99999 ? scrollTop.value + 1 : 100000 }, 100)
	})
}

// 6. 生命周期
onLoad(() => {
	const userStr = uni.getStorageSync('student_user')
	if (userStr) {
		const u = JSON.parse(userStr)
		userInfo.value = {
			nickname: u.nickname || '同学',
			avatar_url: u.avatar_url || ''
		}
	}
	
	initVoice()
	fetchGuidance()
	
	const sid = uni.getStorageSync('active_session_id')
	if (sid) {
		loadSession(sid)
	}
})

onShow(() => {
	// [修复] 处理由测评结束带来的状态更新需求
	const shouldRefresh = uni.getStorageSync('refresh_chat_session')
	if (shouldRefresh && sessionId.value) {
		loadSession(sessionId.value)
		uni.removeStorageSync('refresh_chat_session')
	}

	const pendingMsg = uni.getStorageSync('pending_chat_msg')
	if (pendingMsg) {
		inputText.value = pendingMsg
		uni.removeStorageSync('pending_chat_msg')
		setTimeout(() => sendMessage(), 500)
	}
})
</script>

<style lang="scss">
page {
	height: 100%;
}

.chat-page-container {
	display: flex; 
	flex-direction: column; 
	height: 100vh; 
	background-color: $sh-bg;
}

.session-progress {
	background: #fff; 
	padding: 20rpx 30rpx; 
	border-bottom: 1rpx solid $sh-border; 
	box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.02);
	flex-shrink: 0; // 强制不收缩
	.progress-inner { display: flex; align-items: center; justify-content: space-around; }
	.progress-item {
		display: flex; flex-direction: column; align-items: center; gap: 8rpx; opacity: 0.3; transition: all 0.3s;
		&.completed { opacity: 1; .dot { background: $sh-primary; color: #fff; } .label { color: $sh-text-main; font-weight: 600; } }
		.dot { width: 32rpx; height: 32rpx; border-radius: 50%; background: #E5EDE9; display: flex; align-items: center; justify-content: center; font-size: 18rpx; }
		.label { font-size: 18rpx; color: $sh-text-sub; }
	}
	.progress-line { flex: 1; height: 2rpx; background: $sh-border; margin: 0 10rpx; margin-top: -24rpx; }
}
</style>
