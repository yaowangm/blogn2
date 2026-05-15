/**
 * 搜索页面逻辑
 * 实现智能搜索功能
 */

class SearchPage {
    constructor() {
        this.currentQuery = '';
        this.currentPage = 1;
        this.pageSize = 10;
        this.currentType = 'all';
        this.currentSort = 'relevance';
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSearchParams();
    }

    bindEvents() {
        // 搜索表单提交
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performSearch();
            });
        }

        // 搜索输入框回车
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performSearch();
                }
            });
        }

        // 过滤器变化
        const searchType = document.getElementById('searchType');
        const sortBy = document.getElementById('sortBy');
        
        if (searchType) {
            searchType.addEventListener('change', (e) => {
                this.currentType = e.target.value;
                this.currentPage = 1; // 切换搜索类型时重置到第一页
                if (this.currentQuery) {
                    this.performSearch();
                }
            });
        }

        if (sortBy) {
            sortBy.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.currentPage = 1; // 切换排序方式时重置到第一页
                if (this.currentQuery) {
                    this.performSearch();
                }
            });
        }

        // 结果排序变化
        const resultsSort = document.getElementById('resultsSort');
        if (resultsSort) {
            resultsSort.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.currentPage = 1; // 切换结果排序时重置到第一页
                if (this.currentQuery) {
                    this.performSearch();
                }
            });
        }
    }

    loadSearchParams() {
        // 从URL参数加载搜索条件
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        const type = urlParams.get('type') || 'all';
        const sort = urlParams.get('sort') || 'relevance';
        const page = parseInt(urlParams.get('page')) || 1;

        if (query) {
            this.currentQuery = query;
            this.currentType = type;
            this.currentSort = sort;
            this.currentPage = page;

            // 设置表单值
            const searchInput = document.getElementById('searchInput');
            const searchType = document.getElementById('searchType');
            const sortBy = document.getElementById('sortBy');
            const resultsSort = document.getElementById('resultsSort');

            if (searchInput) searchInput.value = query;
            if (searchType) searchType.value = type;
            if (sortBy) sortBy.value = sort;
            if (resultsSort) resultsSort.value = sort;

            // 执行搜索
            this.performSearch();
        }
    }

    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput ? searchInput.value.trim() : '';

        if (!query) {
            this.showError('请输入搜索关键词');
            return;
        }

        // 检查是否是新的搜索关键词，如果是则重置到第一页
        if (this.currentQuery !== query) {
            this.currentPage = 1;
        }

        this.currentQuery = query;
        this.showLoading();
        this.hideError();

        try {
            const results = await this.searchAPI(query);
            this.displayResults(results);
            this.updateURL();
        } catch (error) {
            console.error('搜索失败:', error);
            this.showError('搜索失败，请稍后重试');
        } finally {
            this.hideLoading();
        }
    }

    async searchAPI(query) {
        const params = new URLSearchParams({
            q: query,
            type: this.currentType,
            sort: this.currentSort,
            page: this.currentPage,
            limit: this.pageSize
        });

        const response = await fetch(`/api/search?${params}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`搜索请求失败: ${response.status}`);
        }

        return await response.json();
    }

    displayResults(data) {
        const searchResults = document.getElementById('searchResults');
        const resultsList = document.getElementById('resultsList');
        const resultsCount = document.getElementById('resultsCount');
        const noResultsState = document.getElementById('noResultsState');

        if (!searchResults || !resultsList || !resultsCount) return;

        // 显示搜索结果区域
        searchResults.style.display = 'block';
        noResultsState.style.display = 'none';

        // 更新结果数量和搜索信息
        const total = data.total || 0;
        const searchMethod = data.search_method || 'unknown';
        const searchTime = data.search_time || 0;
        const query = data.query || this.currentQuery || '';
        const dynamicThreshold = data.dynamic_threshold || 0.6;
        const thresholdPercent = Math.round(dynamicThreshold * 100);
        resultsCount.textContent = `找到 ${total} 个结果 (${searchMethod}, ${searchTime}ms) | 关键词：${query} | 阈值：${thresholdPercent}%`;

        if (total === 0) {
            this.showNoResults();
            return;
        }

        // 渲染结果列表
        resultsList.innerHTML = '';
        if (data.results && data.results.length > 0) {
            data.results.forEach((result, index) => {
                const resultElement = this.createResultElement(result, index);
                resultsList.appendChild(resultElement);
            });
        }

        // 渲染分页
        this.renderPagination(data);
    }

    createResultElement(result, index) {
        const title = this.escapeHtml(result.title || result.subject || '无标题');
        const content = this.escapeHtml(this.truncateText(result.content || result.comment || '', 200));
        const author = this.escapeHtml(result.author || '未知作者');
        const date = this.formatDate(result.created_at || result.posttime);
        const type = result.type || 'article';
        const typeText = type === 'comment' ? '评论' : '文章';
        const relevanceScore = result.relevance_score || 0;
        const similarityPercent = Math.round(relevanceScore * 100);

        const href = this.getResultHref(result);

        const div = document.createElement('div');
        div.className = 'result-item';
        div.innerHTML = `
            <a href="${href}" target="_blank" class="result-link">
                <div class="result-title">${title}</div>
                <div class="result-meta">
                    <div class="result-author">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        ${author}
                    </div>
                    <div class="result-date">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12,6 12,12 16,14"></polyline>
                        </svg>
                        ${date}
                    </div>
                    <div class="result-similarity">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 12l2 2 4-4"></path>
                            <circle cx="12" cy="12" r="10"></circle>
                        </svg>
                        相似度: ${similarityPercent}%
                    </div>
                    <div class="result-tag">${typeText}</div>
                </div>
                <div class="result-content">${content}</div>
                ${result.tags && result.tags.length > 0 ? `
                    <div class="result-tags">
                        ${result.tags.map(tag => `<span class="result-tag">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </a>
        `;

        return div;
    }

    renderPagination(data) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        const total = data.total || 0;
        const totalPages = Math.ceil(total / this.pageSize);

        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        pagination.innerHTML = '';

        // 上一页按钮
        const prevButton = document.createElement('button');
        prevButton.className = 'pagination-button';
        prevButton.textContent = '上一页';
        prevButton.disabled = this.currentPage <= 1;
        prevButton.onclick = () => this.goToPage(this.currentPage - 1);
        pagination.appendChild(prevButton);

        // 页码按钮
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const pageButton = document.createElement('button');
            pageButton.className = `pagination-button ${i === this.currentPage ? 'active' : ''}`;
            pageButton.textContent = i;
            pageButton.onclick = () => this.goToPage(i);
            pagination.appendChild(pageButton);
        }

        // 下一页按钮
        const nextButton = document.createElement('button');
        nextButton.className = 'pagination-button';
        nextButton.textContent = '下一页';
        nextButton.disabled = this.currentPage >= totalPages;
        nextButton.onclick = () => this.goToPage(this.currentPage + 1);
        pagination.appendChild(nextButton);
    }

    goToPage(page) {
        if (page < 1) return;
        this.currentPage = page;
        this.performSearch();
    }

    /**
     * 搜索结果详情页 URL。博文评论使用 /article/{博文id}#post{评论id}，与文章页评论锚点一致。
     */
    getResultHref(result) {
        const positiveInt = (v) => {
            if (v === undefined || v === null || v === '') return NaN;
            const n = Number(v);
            return Number.isFinite(n) && n > 0 ? n : NaN;
        };
        const type = result.type || 'article';
        if (type === 'comment') {
            const nPid = positiveInt(result.projectitem_id ?? result.article_id);
            const nCid = positiveInt(result.id);
            if (Number.isFinite(nPid) && Number.isFinite(nCid)) {
                return `/article/${nPid}#post${nCid}`;
            }
            if (Number.isFinite(nCid)) {
                return `/thread/${nCid}`;
            }
            return '#';
        }
        const articleId = result.id ?? result.projectitem_id;
        if (articleId !== undefined && articleId !== null && articleId !== '') {
            return `/article/${articleId}`;
        }
        return '#';
    }

    openResult(result) {
        const href = this.getResultHref(result);
        if (href !== '#') {
            window.open(href, '_blank');
        }
    }

    showLoading() {
        this.isLoading = true;
        const loadingState = document.getElementById('loadingState');
        const searchButton = document.getElementById('searchButton');
        
        if (loadingState) loadingState.style.display = 'block';
        if (searchButton) {
            searchButton.disabled = true;
            searchButton.textContent = '搜索中...';
        }
    }

    hideLoading() {
        this.isLoading = false;
        const loadingState = document.getElementById('loadingState');
        const searchButton = document.getElementById('searchButton');
        
        if (loadingState) loadingState.style.display = 'none';
        if (searchButton) {
            searchButton.disabled = false;
            searchButton.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                </svg>
                搜索
            `;
        }
    }

    showNoResults() {
        const noResultsState = document.getElementById('noResultsState');
        const searchResults = document.getElementById('searchResults');
        
        if (noResultsState) noResultsState.style.display = 'block';
        if (searchResults) searchResults.style.display = 'none';
    }

    showError(message) {
        // 创建或更新错误消息
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.className = 'error-message';
            
            const searchForm = document.getElementById('searchForm');
            if (searchForm) {
                searchForm.parentNode.insertBefore(errorDiv, searchForm.nextSibling);
            }
        }
        
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    hideError() {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }

    updateURL() {
        // 更新URL参数，但不刷新页面
        const url = new URL(window.location);
        url.searchParams.set('q', this.currentQuery);
        url.searchParams.set('type', this.currentType);
        url.searchParams.set('sort', this.currentSort);
        url.searchParams.set('page', this.currentPage);
        
        window.history.pushState({}, '', url);
    }

    // 工具方法
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    formatDate(dateString) {
        if (!dateString) return '未知时间';
        
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;
        
        return date.toLocaleDateString('zh-CN');
    }
}

// 页面加载完成后初始化搜索功能
document.addEventListener('DOMContentLoaded', () => {
    new SearchPage();
});
