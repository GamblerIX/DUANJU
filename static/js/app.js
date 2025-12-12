/**
 * 短剧应用主模块
 */

// 应用状态
const AppState = {
    currentPage: 'home',
    currentCategory: '推荐榜',
    currentDrama: null,
    episodes: [],
    episodePage: 1,
    currentEpisodeIndex: 0,
    searchQuery: '',
    isLoading: false
};

// 路由器
const Router = {
    navigate(page, params = {}) {
        AppState.currentPage = page;
        Object.assign(AppState, params);
        this.render();
    },

    render() {
        const main = document.getElementById('main-content');
        switch (AppState.currentPage) {
            case 'home':
                loadHome();
                break;
            case 'search':
                loadSearchResults();
                break;
            case 'detail':
                loadDetail();
                break;
            default:
                loadHome();
        }
    }
};

// 显示加载状态
function showLoading() {
    AppState.isLoading = true;
    document.getElementById('main-content').innerHTML = Components.Loading();
}

// 隐藏加载状态
function hideLoading() {
    AppState.isLoading = false;
}

// 初始化分类导航
function initCategories() {
    const nav = document.getElementById('categories-nav');
    nav.innerHTML = CATEGORIES.map(cat => `
        <button class="category-btn ${cat === AppState.currentCategory ? 'active' : ''}" 
                onclick="selectCategory('${cat}')">${cat}</button>
    `).join('');
}

// 选择分类
async function selectCategory(category) {
    AppState.currentCategory = category;
    initCategories();
    showLoading();
    
    try {
        const data = await API.getCategoryDramas(category);
        const main = document.getElementById('main-content');
        
        if (data.code === 200 && data.data) {
            main.innerHTML = `
                <h2 class="section-title">${category}</h2>
                ${Components.DramaGrid(data.data)}
            `;
        } else {
            main.innerHTML = Components.EmptyMessage('暂无该分类短剧');
        }
    } catch (e) {
        document.getElementById('main-content').innerHTML = 
            Components.ErrorMessage('加载失败: ' + e.message, `selectCategory('${category}')`);
    }
    hideLoading();
}

// 加载首页
async function loadHome() {
    showLoading();
    try {
        const data = await API.getRecommendations();
        const main = document.getElementById('main-content');
        
        if (data.code === 200 && data.data) {
            main.innerHTML = `
                <h2 class="section-title">热门推荐</h2>
                ${Components.DramaGrid(data.data)}
            `;
        } else {
            main.innerHTML = Components.EmptyMessage('暂无推荐');
        }
    } catch (e) {
        document.getElementById('main-content').innerHTML = 
            Components.ErrorMessage('加载失败: ' + e.message, 'loadHome()');
    }
    hideLoading();
}


// 搜索处理
function handleSearch() {
    const input = document.getElementById('search-input');
    const query = input.value.trim();
    if (!query) {
        showToast('请输入搜索关键词');
        return;
    }
    AppState.searchQuery = query;
    Router.navigate('search');
}

// 加载搜索结果
async function loadSearchResults() {
    showLoading();
    try {
        const data = await API.search(AppState.searchQuery);
        const main = document.getElementById('main-content');
        
        if (data.code === 200 && data.data && data.data.length > 0) {
            main.innerHTML = `
                <h2 class="section-title">搜索: ${AppState.searchQuery}</h2>
                ${Components.DramaGrid(data.data)}
            `;
        } else {
            main.innerHTML = `
                <h2 class="section-title">搜索: ${AppState.searchQuery}</h2>
                ${Components.EmptyMessage('未找到相关短剧')}
            `;
        }
    } catch (e) {
        document.getElementById('main-content').innerHTML = 
            Components.ErrorMessage('搜索失败: ' + e.message, 'loadSearchResults()');
    }
    hideLoading();
}

// 显示详情页
async function showDetail(bookId) {
    AppState.currentDrama = { book_id: bookId };
    AppState.episodePage = 1;
    Router.navigate('detail');
}

// 加载详情
async function loadDetail() {
    showLoading();
    try {
        console.log('加载详情, book_id:', AppState.currentDrama.book_id);
        const data = await API.getDramaDetail(AppState.currentDrama.book_id);
        console.log('详情API响应:', data);
        const main = document.getElementById('main-content');
        
        if (data.code === 200) {
            AppState.currentDrama = data;
            AppState.episodes = data.data || [];
            console.log('剧集数量:', AppState.episodes.length);
            
            main.innerHTML = Components.DetailPage(data);
            renderEpisodeList();
        } else {
            main.innerHTML = Components.ErrorMessage('获取详情失败: ' + (data.msg || ''), 'loadDetail()');
        }
    } catch (e) {
        console.error('加载详情失败:', e);
        document.getElementById('main-content').innerHTML = 
            Components.ErrorMessage('加载失败: ' + e.message, 'loadDetail()');
    }
    hideLoading();
}

// 渲染剧集列表
function renderEpisodeList() {
    const container = document.getElementById('episode-list');
    if (container) {
        container.innerHTML = Components.EpisodeList(
            AppState.episodes, 
            AppState.episodePage
        );
    }
}

// 切换剧集分页
function changeEpisodePage(page) {
    AppState.episodePage = page;
    renderEpisodeList();
}

// 播放剧集
async function playEpisode(videoId, index) {
    AppState.currentEpisodeIndex = index;
    showToast('正在获取视频...');
    
    try {
        const data = await API.getVideoUrl(videoId);
        console.log('视频API响应:', data);
        
        if (data.code === 200 && data.data) {
            const videoUrl = data.data.url;
            if (videoUrl) {
                openPlayer({
                    title: data.data.title || data.msg || '播放中',
                    url: videoUrl,
                    pic: data.data.pic
                });
            } else {
                showToast('视频地址为空');
                console.error('视频数据:', data.data);
            }
        } else {
            showToast('获取视频失败: ' + (data.msg || '未知错误'));
            console.error('API错误:', data);
        }
    } catch (e) {
        showToast('播放失败: ' + e.message);
        console.error('播放异常:', e);
    }
}

// 当前视频数据
let currentVideoData = null;

// 打开播放器
function openPlayer(videoData) {
    const modal = document.getElementById('player-modal');
    const video = document.getElementById('video-player');
    const title = document.getElementById('player-title');
    const error = document.getElementById('player-error');
    
    console.log('打开播放器, URL:', videoData.url);
    currentVideoData = videoData;
    
    title.textContent = videoData.title || '播放中';
    error.classList.remove('active');
    modal.classList.add('active');
    
    // 更新上下集按钮状态
    document.getElementById('prev-episode').disabled = AppState.currentEpisodeIndex <= 0;
    document.getElementById('next-episode').disabled = 
        AppState.currentEpisodeIndex >= AppState.episodes.length - 1;
    
    // 设置视频源并播放
    video.src = videoData.url;
    video.load();
    
    video.play().catch(err => {
        console.error('播放失败:', err);
    });
}

// 使用外部播放器
function openExternal() {
    if (currentVideoData && currentVideoData.url) {
        // 尝试使用 intent 打开外部播放器 (Android)
        const url = currentVideoData.url;
        
        // 创建一个隐藏的 a 标签来触发外部应用
        const a = document.createElement('a');
        a.href = url;
        a.target = '_blank';
        a.click();
        
        showToast('正在打开外部播放器...');
    } else {
        showToast('没有可播放的视频');
    }
}

// 复制视频链接
function copyVideoUrl() {
    if (currentVideoData && currentVideoData.url) {
        navigator.clipboard.writeText(currentVideoData.url).then(() => {
            showToast('链接已复制');
        }).catch(() => {
            // 降级方案
            const input = document.createElement('input');
            input.value = currentVideoData.url;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            showToast('链接已复制');
        });
    }
}

// 关闭播放器
function closePlayer() {
    const modal = document.getElementById('player-modal');
    const video = document.getElementById('video-player');
    video.pause();
    video.src = '';
    modal.classList.remove('active');
}


// 播放上一集
function playPrevEpisode() {
    if (AppState.currentEpisodeIndex > 0) {
        const prevIndex = AppState.currentEpisodeIndex - 1;
        const episode = AppState.episodes[prevIndex];
        if (episode) {
            playEpisode(episode.video_id, prevIndex);
        }
    }
}

// 播放下一集
function playNextEpisode() {
    if (AppState.currentEpisodeIndex < AppState.episodes.length - 1) {
        const nextIndex = AppState.currentEpisodeIndex + 1;
        const episode = AppState.episodes[nextIndex];
        if (episode) {
            playEpisode(episode.video_id, nextIndex);
        }
    }
}

// 重试视频
function retryVideo() {
    const episode = AppState.episodes[AppState.currentEpisodeIndex];
    if (episode) {
        playEpisode(episode.video_id, AppState.currentEpisodeIndex);
    }
}

// 视频错误处理
function setupVideoEvents() {
    const video = document.getElementById('video-player');
    const error = document.getElementById('player-error');
    const errorMsg = document.getElementById('error-msg');
    const externalActions = document.getElementById('external-actions');
    
    video.addEventListener('error', (e) => {
        console.error('视频加载错误:', video.error);
        let msg = '视频加载失败';
        let isFormatError = false;
        
        if (video.error) {
            switch (video.error.code) {
                case 1: msg = '视频加载被中止'; break;
                case 2: msg = '网络错误'; break;
                case 3: 
                    msg = '视频解码失败，正在跳转外部播放...'; 
                    isFormatError = true;
                    break;
                case 4: 
                    msg = '视频格式不支持，正在跳转外部播放...'; 
                    isFormatError = true;
                    break;
            }
        }
        
        errorMsg.textContent = msg;
        externalActions.style.display = isFormatError ? 'flex' : 'none';
        error.classList.add('active');
        
        // 格式不支持时自动跳转外部播放
        if (isFormatError) {
            setTimeout(() => {
                openExternal();
            }, 500);
        }
    });
    
    video.addEventListener('loadstart', () => {
        console.log('视频开始加载');
        externalActions.style.display = 'none';
    });
    
    video.addEventListener('canplay', () => {
        console.log('视频可以播放');
        error.classList.remove('active');
    });
    
    video.addEventListener('ended', () => {
        if (AppState.currentEpisodeIndex < AppState.episodes.length - 1) {
            showToast('点击"下一集"继续观看');
        }
    });
}

// 搜索框回车事件
function setupSearchEvents() {
    const input = document.getElementById('search-input');
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
}

// 初始化应用
function initApp() {
    initCategories();
    setupSearchEvents();
    setupVideoEvents();
    loadHome();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initApp);
