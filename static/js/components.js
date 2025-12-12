/**
 * UI 组件模块
 */
const Components = {
    /**
     * 创建短剧卡片
     * @param {Object} drama - 短剧数据
     * @returns {string} HTML 字符串
     */
    DramaCard(drama) {
        // 处理不同 API 返回的数据结构
        const bookData = drama.book_data || {};
        const bookId = drama.book_id || bookData.book_id || '';
        const title = drama.title || bookData.book_name || '未知';
        const cover = drama.cover || bookData.thumb_url || drama.book_pic || '';
        const episodeCnt = drama.episode_cnt || bookData.serial_count || '';
        const playCnt = drama.play_cnt || parseInt(bookData.read_count) || 0;
        
        // 如果没有 book_id，跳过这个卡片
        if (!bookId) {
            console.warn('短剧缺少 book_id:', drama);
            return '';
        }
        
        const playText = playCnt > 10000 
            ? (playCnt / 10000).toFixed(1) + '万' 
            : playCnt;

        return `
            <div class="drama-card" onclick="showDetail('${bookId}')">
                <div class="cover">
                    <img src="${cover}" alt="${title}" loading="lazy" 
                         onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 133%22><rect fill=%22%2316213e%22 width=%22100%22 height=%22133%22/><text x=%2250%22 y=%2270%22 text-anchor=%22middle%22 fill=%22%23888%22>暂无封面</text></svg>'">
                    ${episodeCnt ? `<span class="episode-badge">全${episodeCnt}集</span>` : ''}
                </div>
                <div class="info">
                    <div class="title">${title}</div>
                    <div class="meta">${playText}次播放</div>
                </div>
            </div>
        `;
    },

    /**
     * 创建短剧网格
     * @param {Array} dramas - 短剧列表
     * @returns {string} HTML 字符串
     */
    DramaGrid(dramas) {
        if (!dramas || dramas.length === 0) {
            return '<div class="empty-message">暂无数据</div>';
        }
        return `
            <div class="drama-grid">
                ${dramas.map(d => this.DramaCard(d)).join('')}
            </div>
        `;
    },

    /**
     * 创建剧集列表
     * @param {Array} episodes - 剧集列表
     * @param {number} currentPage - 当前页码
     * @param {number} pageSize - 每页数量
     * @returns {string} HTML 字符串
     */
    EpisodeList(episodes, currentPage = 1, pageSize = 50) {
        if (!episodes || episodes.length === 0) {
            return '<div class="empty-message">暂无剧集</div>';
        }

        const totalPages = Math.ceil(episodes.length / pageSize);
        const start = (currentPage - 1) * pageSize;
        const end = Math.min(start + pageSize, episodes.length);
        const pageEpisodes = episodes.slice(start, end);

        let html = `<div class="episode-grid">`;
        pageEpisodes.forEach((ep, idx) => {
            const num = start + idx + 1;
            html += `
                <button class="episode-btn" onclick="playEpisode('${ep.video_id}', ${start + idx})">
                    ${num}
                </button>
            `;
        });
        html += `</div>`;

        // 分页控件（超过50集时显示）
        if (totalPages > 1) {
            html += `<div class="episode-pagination">`;
            for (let i = 1; i <= totalPages; i++) {
                html += `
                    <button class="page-btn ${i === currentPage ? 'active' : ''}" 
                            onclick="changeEpisodePage(${i})">
                        ${(i-1)*pageSize + 1}-${Math.min(i*pageSize, episodes.length)}
                    </button>
                `;
            }
            html += `</div>`;
        }

        return html;
    },


    /**
     * 创建详情页
     * @param {Object} data - 详情数据
     * @returns {string} HTML 字符串
     */
    DetailPage(data) {
        const title = data.book_name || '未知';
        const cover = data.book_pic || '';
        const author = data.author || '';
        const category = data.category || '';
        const desc = data.desc || '';
        const duration = data.duration || '';
        const total = data.total || data.episodes?.length || 0;

        return `
            <div class="detail-page">
                <button class="back-btn" onclick="Router.navigate('home')">← 返回</button>
                <div class="detail-header">
                    <div class="detail-cover">
                        <img src="${cover}" alt="${title}" loading="lazy">
                    </div>
                    <div class="detail-info">
                        <h2>${title}</h2>
                        <div class="meta">${category} · 共${total}集</div>
                        ${author ? `<div class="meta">主演: ${author}</div>` : ''}
                        ${duration ? `<div class="meta">时长: ${duration}</div>` : ''}
                        <div class="desc">${desc}</div>
                    </div>
                </div>
                <div class="episode-section">
                    <h3>选集</h3>
                    <div id="episode-list"></div>
                </div>
            </div>
        `;
    },

    /**
     * 加载中组件
     * @returns {string} HTML 字符串
     */
    Loading() {
        return `
            <div class="loading active">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;
    },

    /**
     * 错误消息组件
     * @param {string} message - 错误信息
     * @param {Function} retryFn - 重试函数名
     * @returns {string} HTML 字符串
     */
    ErrorMessage(message, retryFn = 'location.reload()') {
        return `
            <div class="error-message">
                <p>${message}</p>
                <button onclick="${retryFn}">重试</button>
            </div>
        `;
    },

    /**
     * 空状态组件
     * @param {string} message - 提示信息
     * @returns {string} HTML 字符串
     */
    EmptyMessage(message = '暂无数据') {
        return `<div class="empty-message">${message}</div>`;
    }
};

/**
 * 显示 Toast 提示
 * @param {string} message - 提示信息
 * @param {number} duration - 显示时长(ms)
 */
function showToast(message, duration = 2000) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('active');
    setTimeout(() => toast.classList.remove('active'), duration);
}
