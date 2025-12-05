#include "widgets/searchwidget.h"
#include <QMessageBox>

SearchWidget::SearchWidget(QWidget* parent)
    : QWidget(parent)
    , m_currentPage(1)
    , m_totalPages(1)
{
    setupUI();
}

void SearchWidget::setupUI() {
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(16, 16, 16, 16);
    mainLayout->setSpacing(12);
    
    // Search bar
    QHBoxLayout* searchLayout = new QHBoxLayout();
    searchLayout->setSpacing(8);
    
    m_searchInput = new QLineEdit(this);
    m_searchInput->setPlaceholderText("输入短剧名称搜索...");
    m_searchInput->setMinimumHeight(36);
    connect(m_searchInput, &QLineEdit::returnPressed, this, &SearchWidget::onSearchClicked);
    
    m_searchButton = new QPushButton("搜索", this);
    m_searchButton->setMinimumHeight(36);
    m_searchButton->setMinimumWidth(80);
    connect(m_searchButton, &QPushButton::clicked, this, &SearchWidget::onSearchClicked);
    
    searchLayout->addWidget(m_searchInput);
    searchLayout->addWidget(m_searchButton);
    mainLayout->addLayout(searchLayout);
    
    // Loading indicator
    m_loadingLabel = new QLabel("正在搜索...", this);
    m_loadingLabel->setAlignment(Qt::AlignCenter);
    m_loadingLabel->hide();
    mainLayout->addWidget(m_loadingLabel);
    
    // Message label (for errors and no results)
    m_messageLabel = new QLabel(this);
    m_messageLabel->setAlignment(Qt::AlignCenter);
    m_messageLabel->setWordWrap(true);
    m_messageLabel->hide();
    mainLayout->addWidget(m_messageLabel);
    
    // Result list
    m_resultList = new QListWidget(this);
    m_resultList->setSpacing(4);
    connect(m_resultList, &QListWidget::itemClicked, this, &SearchWidget::onItemClicked);
    mainLayout->addWidget(m_resultList, 1);
    
    // Pagination
    m_paginationWidget = new QWidget(this);
    QHBoxLayout* pageLayout = new QHBoxLayout(m_paginationWidget);
    pageLayout->setContentsMargins(0, 0, 0, 0);
    
    m_prevButton = new QPushButton("上一页", this);
    m_prevButton->setEnabled(false);
    connect(m_prevButton, &QPushButton::clicked, this, &SearchWidget::onPrevPageClicked);
    
    m_pageLabel = new QLabel("第 1 页 / 共 1 页", this);
    m_pageLabel->setAlignment(Qt::AlignCenter);
    
    m_nextButton = new QPushButton("下一页", this);
    m_nextButton->setEnabled(false);
    connect(m_nextButton, &QPushButton::clicked, this, &SearchWidget::onNextPageClicked);
    
    pageLayout->addStretch();
    pageLayout->addWidget(m_prevButton);
    pageLayout->addWidget(m_pageLabel);
    pageLayout->addWidget(m_nextButton);
    pageLayout->addStretch();
    
    m_paginationWidget->hide();
    mainLayout->addWidget(m_paginationWidget);
}

QString SearchWidget::searchText() const {
    return m_searchInput->text();
}

bool SearchWidget::isValidSearchInput(const QString& input) {
    // Check if input is empty or contains only whitespace
    return !input.trimmed().isEmpty();
}

void SearchWidget::onSearchClicked() {
    QString keyword = m_searchInput->text();
    
    if (!isValidSearchInput(keyword)) {
        m_messageLabel->setText("请输入搜索关键词");
        m_messageLabel->show();
        return;
    }
    
    m_messageLabel->hide();
    m_currentPage = 1;
    emit searchRequested(keyword.trimmed());
}

void SearchWidget::setResults(const SearchResult& result) {
    m_resultList->clear();
    m_messageLabel->hide();
    
    if (result.data.isEmpty()) {
        showNoResults();
        return;
    }
    
    for (const DramaInfo& drama : result.data) {
        QListWidgetItem* item = new QListWidgetItem(m_resultList);
        QString text = QString("%1\n集数: %2").arg(drama.name).arg(drama.episodeCount);
        if (!drama.category.isEmpty()) {
            text += QString(" | 分类: %1").arg(drama.category);
        }
        item->setText(text);
        item->setData(Qt::UserRole, drama.bookId);
        item->setSizeHint(QSize(0, 60));
    }
    
    m_currentPage = result.currentPage;
    m_totalPages = result.totalPages;
    updatePagination();
}

void SearchWidget::setLoading(bool loading) {
    m_loadingLabel->setVisible(loading);
    m_searchButton->setEnabled(!loading);
    m_searchInput->setEnabled(!loading);
    
    if (loading) {
        m_messageLabel->hide();
    }
}

void SearchWidget::showError(const QString& message) {
    m_messageLabel->setText(message);
    m_messageLabel->setStyleSheet("color: #d32f2f;");
    m_messageLabel->show();
}

void SearchWidget::showNoResults() {
    m_messageLabel->setText("未找到相关短剧，请尝试其他关键词");
    m_messageLabel->setStyleSheet("");
    m_messageLabel->show();
    m_paginationWidget->hide();
}

void SearchWidget::clearResults() {
    m_resultList->clear();
    m_messageLabel->hide();
    m_paginationWidget->hide();
    m_currentPage = 1;
    m_totalPages = 1;
}

void SearchWidget::onItemClicked(QListWidgetItem* item) {
    QString bookId = item->data(Qt::UserRole).toString();
    if (!bookId.isEmpty()) {
        emit dramaSelected(bookId);
    }
}

void SearchWidget::onPrevPageClicked() {
    if (m_currentPage > 1) {
        m_currentPage--;
        emit pageChanged(m_currentPage);
    }
}

void SearchWidget::onNextPageClicked() {
    if (m_currentPage < m_totalPages) {
        m_currentPage++;
        emit pageChanged(m_currentPage);
    }
}

void SearchWidget::updatePagination() {
    if (m_totalPages > 1) {
        m_paginationWidget->show();
        m_pageLabel->setText(QString("第 %1 页 / 共 %2 页").arg(m_currentPage).arg(m_totalPages));
        m_prevButton->setEnabled(m_currentPage > 1);
        m_nextButton->setEnabled(m_currentPage < m_totalPages);
    } else {
        m_paginationWidget->hide();
    }
}
