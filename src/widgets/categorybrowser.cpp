#include "widgets/categorybrowser.h"
#include <QVBoxLayout>
#include <QHBoxLayout>

CategoryBrowser::CategoryBrowser(QWidget* parent)
    : QWidget(parent)
    , m_currentOffset(1)
{
    setupUI();
    
    // Set default categories
    QStringList defaultCategories = {
        "穿越", "虐恋", "甜宠", "霸总", "现代言情", "古装虐恋",
        "都市", "逆袭", "复仇", "重生", "战神", "神医"
    };
    setCategories(defaultCategories);
}

void CategoryBrowser::setupUI() {
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(16, 16, 16, 16);
    mainLayout->setSpacing(12);
    
    // Category selection bar
    QHBoxLayout* topLayout = new QHBoxLayout();
    topLayout->setSpacing(8);
    
    m_categoryCombo = new QComboBox(this);
    m_categoryCombo->setMinimumHeight(36);
    m_categoryCombo->setMinimumWidth(150);
    connect(m_categoryCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &CategoryBrowser::onCategoryChanged);
    
    m_recommendBtn = new QPushButton("推荐", this);
    m_recommendBtn->setMinimumHeight(36);
    connect(m_recommendBtn, &QPushButton::clicked, this, &CategoryBrowser::onRecommendClicked);
    
    topLayout->addWidget(new QLabel("分类:", this));
    topLayout->addWidget(m_categoryCombo);
    topLayout->addWidget(m_recommendBtn);
    topLayout->addStretch();
    mainLayout->addLayout(topLayout);
    
    // Loading indicator
    m_loadingLabel = new QLabel("正在加载...", this);
    m_loadingLabel->setAlignment(Qt::AlignCenter);
    m_loadingLabel->hide();
    mainLayout->addWidget(m_loadingLabel);
    
    // Result list
    m_resultList = new QListWidget(this);
    m_resultList->setSpacing(4);
    connect(m_resultList, &QListWidget::itemClicked, this, &CategoryBrowser::onItemClicked);
    mainLayout->addWidget(m_resultList, 1);
    
    // Pagination
    m_paginationWidget = new QWidget(this);
    QHBoxLayout* pageLayout = new QHBoxLayout(m_paginationWidget);
    pageLayout->setContentsMargins(0, 0, 0, 0);
    
    m_prevButton = new QPushButton("上一页", this);
    m_prevButton->setEnabled(false);
    connect(m_prevButton, &QPushButton::clicked, this, &CategoryBrowser::onPrevPageClicked);
    
    m_pageLabel = new QLabel("第 1 页", this);
    m_pageLabel->setAlignment(Qt::AlignCenter);
    
    m_nextButton = new QPushButton("下一页", this);
    connect(m_nextButton, &QPushButton::clicked, this, &CategoryBrowser::onNextPageClicked);
    
    pageLayout->addStretch();
    pageLayout->addWidget(m_prevButton);
    pageLayout->addWidget(m_pageLabel);
    pageLayout->addWidget(m_nextButton);
    pageLayout->addStretch();
    
    m_paginationWidget->hide();
    mainLayout->addWidget(m_paginationWidget);
}

void CategoryBrowser::setCategories(const QStringList& categories) {
    m_categoryCombo->clear();
    m_categoryCombo->addItem("请选择分类");
    m_categoryCombo->addItems(categories);
}

void CategoryBrowser::setResults(const CategoryResult& result) {
    m_resultList->clear();
    
    for (const DramaInfo& drama : result.data) {
        QListWidgetItem* item = new QListWidgetItem(m_resultList);
        QString text = QString("%1\n集数: %2").arg(drama.name).arg(drama.episodeCount);
        item->setText(text);
        item->setData(Qt::UserRole, drama.bookId);
        item->setSizeHint(QSize(0, 60));
    }
    
    m_currentOffset = result.offset;
    updatePagination();
}

void CategoryBrowser::setLoading(bool loading) {
    m_loadingLabel->setVisible(loading);
    m_categoryCombo->setEnabled(!loading);
    m_recommendBtn->setEnabled(!loading);
}

void CategoryBrowser::onCategoryChanged(int index) {
    if (index > 0) {
        QString category = m_categoryCombo->currentText();
        m_currentOffset = 1;
        emit categorySelected(category);
    }
}

void CategoryBrowser::onRecommendClicked() {
    emit recommendRequested();
}

void CategoryBrowser::onItemClicked(QListWidgetItem* item) {
    QString bookId = item->data(Qt::UserRole).toString();
    if (!bookId.isEmpty()) {
        emit dramaSelected(bookId);
    }
}

void CategoryBrowser::onPrevPageClicked() {
    if (m_currentOffset > 1) {
        m_currentOffset--;
        emit pageChanged(m_currentOffset);
    }
}

void CategoryBrowser::onNextPageClicked() {
    m_currentOffset++;
    emit pageChanged(m_currentOffset);
}

void CategoryBrowser::updatePagination() {
    m_paginationWidget->show();
    m_pageLabel->setText(QString("第 %1 页").arg(m_currentOffset));
    m_prevButton->setEnabled(m_currentOffset > 1);
}
