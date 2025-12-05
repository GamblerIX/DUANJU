#include "services/videoservice.h"

VideoService::VideoService(ApiClient* apiClient, QObject* parent)
    : QObject(parent)
    , m_apiClient(apiClient)
{
    connect(m_apiClient, &ApiClient::episodeListReceived,
            this, &VideoService::episodesFetched);
    connect(m_apiClient, &ApiClient::videoUrlReceived,
            this, &VideoService::videoUrlFetched);
    connect(m_apiClient, &ApiClient::errorOccurred,
            this, &VideoService::fetchFailed);
    connect(m_apiClient, &ApiClient::requestStarted,
            this, &VideoService::fetchStarted);
}

void VideoService::fetchEpisodes(const QString& bookId) {
    m_apiClient->getEpisodeList(bookId);
}

void VideoService::fetchVideoUrl(const QString& videoId, const QString& quality) {
    m_apiClient->getVideoUrl(videoId, quality);
}
