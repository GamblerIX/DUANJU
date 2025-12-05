#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTabWidget>
#include <QDockWidget>
#include "api/apiclient.h"
#include "services/searchservice.h"
#include "services/categoryservice.h"
#include "services/videoservice.h"
#include "widgets/searchwidget.h"
#include "widgets/categorybrowser.h"
#include "widgets/videoplayer.h"
#include "widgets/logviewer.h"
#include "widgets/episodelistdialog.h"
#include "widgets/errorhandler.h"

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget* parent = nullptr);
    ~MainWindow();

private slots:
    void onSearchRequested(const QString& keyword);
    void onSearchCompleted(const SearchResult& result);
    void onDramaSelected(const QString& bookId);
    void onEpisodesFetched(const EpisodeList& episodes);
    void onEpisodeSelected(const QString& videoId, const QString& quality);
    void onVideoUrlFetched(const VideoInfo& video);
    void onCategorySelected(const QString& category);
    void onCategoryFetched(const CategoryResult& result);
    void onRecommendRequested();
    void onError(const ApiError& error);
    void onSettingsClicked();

private:
    void setupUI();
    void setupConnections();
    void applyFluentDesign();
    
    // Core components
    ApiClient* m_apiClient;
    SearchService* m_searchService;
    CategoryService* m_categoryService;
    VideoService* m_videoService;
    
    // UI components
    QTabWidget* m_tabWidget;
    SearchWidget* m_searchWidget;
    CategoryBrowser* m_categoryBrowser;
    VideoPlayer* m_videoPlayer;
    LogViewer* m_logViewer;
    ErrorHandler* m_errorHandler;
    EpisodeListDialog* m_episodeDialog;
    
    // State
    QString m_currentKeyword;
};

#endif // MAINWINDOW_H
