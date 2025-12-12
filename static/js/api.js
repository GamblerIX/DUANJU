/**
 * 短剧 API 调用模块
 */
const API = {
    /**
     * 搜索短剧
     * @param {string} query - 搜索关键词
     * @param {number} page - 页码
     * @returns {Promise<Object>}
     */
    async search(query, page = 1) {
        const params = new URLSearchParams({ name: query, page: page });
        const response = await fetch(`/api/search?${params}`);
        if (!response.ok) throw new Error('搜索请求失败');
        return response.json();
    },

    /**
     * 获取分类短剧
     * @param {string} category - 分类名称
     * @param {number} offset - 偏移量
     * @returns {Promise<Object>}
     */
    async getCategoryDramas(category, offset = 1) {
        const params = new URLSearchParams({ classname: category, offset: offset });
        const response = await fetch(`/api/categories?${params}`);
        if (!response.ok) throw new Error('获取分类失败');
        return response.json();
    },

    /**
     * 获取短剧详情和剧集列表
     * @param {string} bookId - 短剧ID
     * @returns {Promise<Object>}
     */
    async getDramaDetail(bookId) {
        const response = await fetch(`/api/drama/${bookId}`);
        if (!response.ok) throw new Error('获取详情失败');
        return response.json();
    },

    /**
     * 获取视频播放地址
     * @param {string} videoId - 视频ID
     * @param {string} quality - 清晰度
     * @returns {Promise<Object>}
     */
    async getVideoUrl(videoId, quality = '1080p') {
        const params = new URLSearchParams({ level: quality });
        const response = await fetch(`/api/video/${videoId}?${params}`);
        if (!response.ok) throw new Error('获取视频地址失败');
        return response.json();
    },

    /**
     * 获取推荐短剧
     * @returns {Promise<Object>}
     */
    async getRecommendations() {
        const response = await fetch('/api/recommend');
        if (!response.ok) throw new Error('获取推荐失败');
        return response.json();
    }
};

// 分类列表
const CATEGORIES = [
    '推荐榜', '新剧', '霸总', '现代言情', '逆袭', '重生', '穿越',
    '甜宠', '虐恋', '豪门', '战神', '赘婿', '萌宝', '古装'
];
