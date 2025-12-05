#include "mainwindow.h"
#include "widgets/settingsdialog.h"
#include "utils/configmanager.h"
#include "utils/thememanager.h"
#include "utils/logmanager.h"
#include <QToolBar>
#include <QAction>
#include <QSplitter>
#include <QVBoxLayout>

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
{
    // Initialize core components
    m_apiClient = new ApiClient(this);
    m_searchService = new SearchService(m_apiClient, this);
    m_categoryService = new CategoryService(m_apiClient, this);
    m_videoService = new VideoService(m_apiClient, this);
    
    setupUI();
    setupConnections();
    applyFluentDesign();
    
    // Load config
    ConfigManager::instance()->load();
    m_apiClient->setTimeout(ConfigManager::instance()->apiTimeout());
    
    // Apply theme
    ThemeManager::instance()->setThemeMode(ConfigManager::instance()->themeMode());
    
    LogManager::instance()->log("应用程序启动", LogLevel::Info);
}

MainWindow::~MainWindow() {
    ConfigManager::instance()->save();
}

void MainWindow::setupUI() {
    setWindowTitle("短剧搜索");
    resize(1200, 800);
    setMinimumSize(800, 600);
    
    // Toolbar
    QToolBar* toolbar = addToolBar("工具栏");
    toolbar->setMovable(false);
    
    QAction* settingsAction = toolbar->addAction("⚙ 设置");
    connect(settingsAction, &QAction::triggered, this, &MainWindow::onSettingsClicked);
    
    // Main splitter
    QSplitter* mainSplitter = new QSplitter(Qt::Horizontal, this);
    setCentralWidget(mainSplitter);
    
    // Left panel - tabs
    QWidget* leftPanel = new QWidget(this);
    QVBoxLayout* leftLayout = new QVBoxLayout(leftPanel);
    leftLayout->setContentsMargins(0, 0, 0, 0);
    
    m_tabWidget = new QTabWidget(this);
    
    // Search tab
    m_searchWidget = new SearchWidget(this);
    m_tabWidget->addTab(m_searchWidget, "搜索");
    
    // Category tab
    m_categoryBrowser = new CategoryBrowser(this);
    m_tabWidget->addTab(m_categoryBrowser, "分类");
    
    // Player tab
    m_videoPlayer = new VideoPlayer(this);
    m_tabWidget->addTab(m_videoPlayer, "播放");
    
    leftLayout->addWidget(m_tabWidget);
    
    // Error handler (overlay)
    m_errorHandler = new ErrorHandler(leftPanel);
    m_errorHandler->setGeometry(16, 16, 400, 48);
    
    mainSplitter->addWidget(leftPanel);
    
    // Right panel - log viewer
    m_logViewer = new LogViewer(this);
    m_logViewer->setMinimumWidth(250);
    m_logViewer->setMaximumWidth(400);
    mainSplitter->addWidget(m_logViewer);
    
    mainSplitter->setStretchFactor(0, 3);
    mainSplitter->setStretchFactor(1, 1);
    
    // Episode dialog
    m_episodeDialog = new EpisodeListDialog(this);
}

void MainWindow::setupConnections() {
    // Search connections
    connect(m_searchWidget, &SearchWidget::searchRequested,
            this, &MainWindow::onSearchRequested);
    connect(m_searchWidget, &SearchWidget::dramaSelected,
            this, &MainWindow::onDramaSelected);
    connect(m_searchWidget, &SearchWidget::pageChanged, this, [this](int page) {
        m_searchService->search(m_currentKeyword, page);
    });
    
    connect(m_searchService, &SearchService::searchStarted, this, [this]() {
        m_searchWidget->setLoading(true);
    });
    connect(m_searchService, &SearchService::searchCompleted,
            this, &MainWindow::onSearchCompleted);
    connect(m_searchService, &SearchService::searchFailed,
            this, &MainWindow::onError);
    
    // Category connections
    connect(m_categoryBrowser, &CategoryBrowser::categorySelected,
            this, &MainWindow::onCategorySelected);
    connect(m_categoryBrowser, &CategoryBrowser::recommendRequested,
            this, &MainWindow::onRecommendRequested);
    connect(m_categoryBrowser, &CategoryBrowser::dramaSelected,
            this, &MainWindow::onDramaSelected);
    connect(m_categoryBrowser, &CategoryBrowser::pageChanged, this, [this](int offset) {
        m_categoryService->fetchCategory(m_categoryService->currentCategory(), offset);
    });
    
    connect(m_categoryService, &CategoryService::fetchStarted, this, [this]() {
        m_categoryBrowser->setLoading(true);
    });
    connect(m_categoryService, &CategoryService::categoryFetched,
            this, &MainWindow::onCategoryFetched);
    connect(m_categoryService, &CategoryService::recommendationsFetched,
            this, &MainWindow::onCategoryFetched);
    connect(m_categoryService, &CategoryService::fetchFailed,
            this, &MainWindow::onError);
    
    // Video connections
    connect(m_videoService, &VideoService::episodesFetched,
            this, &MainWindow::onEpisodesFetched);
    connect(m_videoService, &VideoService::videoUrlFetched,
            this, &MainWindow::onVideoUrlFetched);
    connect(m_videoService, &VideoService::fetchFailed,
            this, &MainWindow::onError);
    
    connect(m_episodeDialog, &EpisodeListDialog::episodeSelected,
            this, &MainWindow::onEpisodeSelected);
    
    connect(m_videoPlayer, &VideoPlayer::qualityChangeRequested, this, [this](const QString& quality) {
        // Re-fetch video with new quality if needed
    });
    connect(m_videoPlayer, &VideoPlayer::errorOccurred, this, [this](const QString& error) {
        m_errorHandler->showError(error);
    });
}

void MainWindow::applyFluentDesign() {
    // Apply Windows 11 Fluent Design styling
    setStyleSheet(R"(
        QMainWindow {
            background-color: #f3f3f3;
        }
        QToolBar {
            background-color: transparent;
            border: none;
            padding: 8px;
            spacing: 8px;
        }
        QToolBar QToolButton {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QToolBar QToolButton:hover {
            background-color: rgba(0, 0, 0, 0.05);
        }
        QTabWidget::pane {
            border: none;
            background-color: transparent;
        }
        QTabBar::tab {
            background-color: transparent;
            padding: 10px 20px;
            margin-right: 4px;
            border-radius: 4px 4px 0 0;
        }
        QTabBar::tab:selected {
            background-color: white;
        }
        QTabBar::tab:hover:!selected {
            background-color: rgba(0, 0, 0, 0.05);
        }
    )");
}

void MainWindow::onSearchRequested(const QString& keyword) {
    m_currentKeyword = keyword;
    m_searchService->search(keyword);
    ConfigManager::instance()->addToSearchHistory(keyword);
}

void MainWindow::onSearchCompleted(const SearchResult& result) {
    m_searchWidget->setLoading(false);
    m_searchWidget->setResults(result);
}

void MainWindow::onDramaSelected(const QString& bookId) {
    m_episodeDialog->setLoading(true);
    m_episodeDialog->show();
    m_videoService->fetchEpisodes(bookId);
}

void MainWindow::onEpisodesFetched(const EpisodeList& episodes) {
    m_episodeDialog->setLoading(false);
    m_episodeDialog->setEpisodeList(episodes);
}

void MainWindow::onEpisodeSelected(const QString& videoId, const QString& quality) {
    m_videoService->fetchVideoUrl(videoId, quality);
}

void MainWindow::onVideoUrlFetched(const VideoInfo& video) {
    m_episodeDialog->hide();
    m_tabWidget->setCurrentWidget(m_videoPlayer);
    m_videoPlayer->play(video.videoUrl);
    LogManager::instance()->log(QString("开始播放: %1").arg(video.title), LogLevel::Info);
}

void MainWindow::onCategorySelected(const QString& category) {
    m_categoryService->fetchCategory(category);
}

void MainWindow::onCategoryFetched(const CategoryResult& result) {
    m_categoryBrowser->setLoading(false);
    m_categoryBrowser->setResults(result);
}

void MainWindow::onRecommendRequested() {
    m_categoryService->fetchRecommendations();
}

void MainWindow::onError(const ApiError& error) {
    m_searchWidget->setLoading(false);
    m_categoryBrowser->setLoading(false);
    m_episodeDialog->setLoading(false);
    m_errorHandler->showError(error);
}

void MainWindow::onSettingsClicked() {
    SettingsDialog dialog(this);
    dialog.exec();
    
    // Apply updated settings
    m_apiClient->setTimeout(ConfigManager::instance()->apiTimeout());
}
