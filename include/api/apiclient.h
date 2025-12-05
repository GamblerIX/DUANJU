#ifndef APICLIENT_H
#define APICLIENT_H

#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QUrl>
#include <QUrlQuery>
#include "models/datamodels.h"

class ApiClient : public QObject {
    Q_OBJECT

public:
    explicit ApiClient(QObject* parent = nullptr);
    ~ApiClient();

    // Search for dramas by name
    void searchDrama(const QString& name, int page = 1);
    
    // Get episode list for a drama
    void getEpisodeList(const QString& bookId);
    
    // Get video URL for playback
    void getVideoUrl(const QString& videoId, const QString& quality = "1080p");
    
    // Get dramas by category
    void getCategoryList(const QString& className, int offset = 1);
    
    // Get recommended dramas
    void getRecommendations();

    // Build URL for search request (exposed for testing)
    QUrl buildSearchUrl(const QString& name, int page = 1) const;
    
    // Build URL for video request (exposed for testing)
    QUrl buildVideoUrl(const QString& videoId, const QString& quality) const;
    
    // Build URL for category request (exposed for testing)
    QUrl buildCategoryUrl(const QString& className, int offset) const;

    // Set API timeout
    void setTimeout(int ms);
    int timeout() const;

signals:
    void searchCompleted(const SearchResult& result);
    void episodeListReceived(const EpisodeList& episodes);
    void videoUrlReceived(const VideoInfo& video);
    void categoryListReceived(const CategoryResult& result);
    void recommendationsReceived(const CategoryResult& list);
    void requestStarted();
    void requestFinished();
    void errorOccurred(const ApiError& error);

private slots:
    void onSearchReplyFinished();
    void onEpisodeListReplyFinished();
    void onVideoUrlReplyFinished();
    void onCategoryListReplyFinished();
    void onRecommendationsReplyFinished();
    void onNetworkError(QNetworkReply::NetworkError error);

private:
    QNetworkAccessManager* m_networkManager;
    QString m_baseUrl;
    int m_timeout;
    
    void handleNetworkError(QNetworkReply* reply);
    ApiError createNetworkError(QNetworkReply::NetworkError error, const QString& errorString);
};

#endif // APICLIENT_H
