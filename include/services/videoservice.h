#ifndef VIDEOSERVICE_H
#define VIDEOSERVICE_H

#include <QObject>
#include "api/apiclient.h"
#include "models/datamodels.h"

class VideoService : public QObject {
    Q_OBJECT

public:
    explicit VideoService(ApiClient* apiClient, QObject* parent = nullptr);
    
    void fetchEpisodes(const QString& bookId);
    void fetchVideoUrl(const QString& videoId, const QString& quality = "1080p");

signals:
    void fetchStarted();
    void episodesFetched(const EpisodeList& episodes);
    void videoUrlFetched(const VideoInfo& video);
    void fetchFailed(const ApiError& error);

private:
    ApiClient* m_apiClient;
};

#endif // VIDEOSERVICE_H
