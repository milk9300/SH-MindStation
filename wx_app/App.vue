<script>
	export default {
		onLaunch: async function() {
			console.log('[SH MindStation] 小程序启动')
			
			try {
				const loginRes = await uni.login({ provider: 'weixin' })
				if (loginRes.code) {
					uni.request({
						url: 'http://127.0.0.1:8000/api/auth/login/',
						method: 'POST',
						data: { code: loginRes.code },
						success: (res) => {
							if (res.statusCode === 200 && res.data.token) {
								uni.setStorageSync('student_token', res.data.token)
								uni.setStorageSync('student_user', JSON.stringify(res.data.user))
								
								if (!res.data.is_profile_completed) {
									console.log('档案未完善，跳转注册页')
									uni.reLaunch({ url: '/pages/register/index' })
								}
							}
						}
					})
				}
			} catch (err) {
				console.error('静默登录过程中止:', err)
			}
		},
		onShow: function() {},
		onHide: function() {}
	}
</script>

<style lang="scss">
/* 全局基础样式重置 */
page {
	background-color: $sh-bg;
	color: $sh-text-main;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
	font-size: 28rpx;
	line-height: 1.5;
}

/* 全局安全区域适配 */
.safe-bottom {
	padding-bottom: env(safe-area-inset-bottom);
}
</style>
