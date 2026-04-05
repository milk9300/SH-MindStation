const BASE_URL = 'http://127.0.0.1:8000/api'

const request = (options) => {
	const token = uni.getStorageSync('student_token')
	
	// 组装请求头
	const header = {
		'Content-Type': 'application/json',
		...options.header
	}
	if (token) {
		header['Authorization'] = token
	}

	return new Promise((resolve, reject) => {
		uni.request({
			url: BASE_URL + options.url,
			method: options.method || 'GET',
			data: options.data,
			header: header,
			success: (res) => {
				if (res.statusCode === 401) {
					// 身份过期，清空并跳登录
					uni.removeStorageSync('student_token')
					uni.removeStorageSync('student_user')
					uni.showToast({ title: '请重新登录', icon: 'none' })
					setTimeout(() => {
						uni.reLaunch({ url: '/pages/register/index' })
					}, 1000)
					reject(res)
				} else if (res.statusCode === 403) {
                    // 特殊情况：如果是危机预警拦截，不跳转，直接把数据传给页面渲染
                    if (res.data && res.data.is_crisis) {
                        resolve(res.data)
                        return
                    }
					// 否则是档案未完善，踢回注册页
					uni.removeStorageSync('profile_completed')
					uni.showToast({ title: '请补充必要信息', icon: 'none' })
					setTimeout(() => {
						uni.reLaunch({ url: '/pages/register/index' })
					}, 1000)
					reject(res)
				} else {
					resolve(res.data)
				}
			},
			fail: (err) => {
				uni.showToast({ title: '网络连接失败', icon: 'error' })
				reject(err)
			}
		})
	})
}

export default request
