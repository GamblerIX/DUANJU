#include "api/apiclient.h"
#include "utils/logmanager.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>

ApiClient::ApiClient(QObject* parent)
    : QObject(parent)
    , m_networkManager(new QNetworkAccessManager(this))
    , m_baseUrl("https://api.cenguigui.cn/api/duanju/api.php")
    , m_timeout(10000)
{
}

ApiClient::~ApiClient() = default;

void ApiClient::setTimeout(int ms) {
    m_timeout = ms;
}

int ApiClient::timeout() const {
    return m_timeout;
}

QUrl ApiClient::buildSearchUrl(const QString& name, int page) const {
    QUrl url(m_baseUrl);
    QUrlQuery query;
    query.addQueryItem("name", name);
    if (page > 1) {
        query.addQueryItem("page", QString::number(page));
    }
    query.addQueryItem("showRawParams", "false");
    url.setQuery(query);
    return url;
}

QUrl ApiClient::buildVideoUrl(const QString& videoId, const QString& quality) const {
    QUrl url(m_baseUrl);
    QUrlQuery query;
    query.addQueryItem("video_id", videoId);
    query.addQueryItem("level", quality);
    query.addQueryItem("type", "json");
    query.addQueryItem("showRawParams", "false");
    url.setQuery(query);
    return url;
}

QUrl ApiClient::buildCategoryUrl(const QString& className, int offset) const {
    QUrl url(m_baseUrl);
    QUrlQuery query;
    query.addQueryItem("classname", className);
    if (offset > 1) {
        query.addQueryItem("offset", QString::number(offset));
    }
    url.setQuery(query);
    return url;
}

void ApiClient::searchDrama(const QString& name, int page) {
    emit requestStarted();
    
    QUrl url = buildSearchUrl(name, page);
    
    // Log the request
    LogManager::instance()->log(
        QString("API Request: Search - URL: %1").arg(url.toString()),
        LogLevel::Info
    );
    
    QNetworkRequest request(url);
    request.setTransferTimeout(m_timeout);
    
    QNetworkReply* reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &ApiClient::onSearchReplyFinished);
    connect(reply, &QNetworkReply::errorOccurred, this, &ApiClient::onNetworkError);
}

void ApiClient::getEpisodeList(const QString& bookId) {
    emit requestStarted();
    
    QUrl url(m_baseUrl);
    QUrlQuery query;
    query.addQueryItem("book_id", bookId);
    query.addQueryItem("showRawParams", "false");
    url.setQuery(query);
    
    LogManager::instance()->log(
        QString("API Request: Episode List - URL: %1").arg(url.toString()),
        LogLevel::Info
    );
    
    QNetworkRequest request(url);
    request.setTransferTimeout(m_timeout);
    
    QNetworkReply* reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &ApiClient::onEpisodeListReplyFinished);
    connect(reply, &QNetworkReply::errorOccurred, this, &ApiClient::onNetworkError);
}

void ApiClient::getVideoUrl(const QString& videoId, const QString& quality) {
    emit requestStarted();
    
    QUrl url = buildVideoUrl(videoId, quality);
    
    LogManager::instance()->log(
        QString("API Request: Video URL - URL: %1").arg(url.toString()),
        LogLevel::Info
    );
    
    QNetworkRequest request(url);
    request.setTransferTimeout(m_timeout);
    
    QNetworkReply* reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &ApiClient::onVideoUrlReplyFinished);
    connect(reply, &QNetworkReply::errorOccurred, this, &ApiClient::onNetworkError);
}

void ApiClient::getCategoryList(const QString& className, int offset) {
    emit requestStarted();
    
    QUrl url = buildCategoryUrl(className, offset);
    
    LogManager::instance()->log(
        QString("API Request: Category - URL: %1").arg(url.toString()),
        LogLevel::Info
    );
    
    QNetworkRequest request(url);
    request.setTransferTimeout(m_timeout);
    
    QNetworkReply* reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &ApiClient::onCategoryListReplyFinished);
    connect(reply, &QNetworkReply::errorOccurred, this, &ApiClient::onNetworkError);
}

void ApiClient::getRecommendations() {
    emit requestStarted();
    
    QUrl url(m_baseUrl);
    QUrlQuery query;
    query.addQueryItem("type", "recommend");
    url.setQuery(query);
    
    LogManager::instance()->log(
        QString("API Request: Recommendations - URL: %1").arg(url.toString()),
        LogLevel::Info
    );
    
    QNetworkRequest request(url);
    request.setTransferTimeout(m_timeout);
    
    QNetworkReply* reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &ApiClient::onRecommendationsReplyFinished);
    connect(reply, &QNetworkReply::errorOccurred, this, &ApiClient::onNetworkError);
}

void ApiClient::onSearchReplyFinished() {
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) return;
    
    reply->deleteLater();
    emit requestFinished();
    
    if (reply->error() != QNetworkReply::NoError) {
        handleNetworkError(reply);
        return;
    }
    
    QByteArray data = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    
    if (doc.isNull() || !doc.isObject()) {
        ApiError error;
        error.code = -1;
        error.message = "数据解析失败";
        error.details = "Invalid JSON response";
        emit errorOccurred(error);
        return;
    }
    
    QJsonObject json = doc.object();
    int code = json["code"].toInt();
    
    LogManager::instance()->log(
        QString("API Response: Search - Code: %1").arg(code),
        LogLevel::Info
    );
    
    if (code != 200 && code != 0) {
        ApiError error;
        error.code = code;
        error.message = json["title"].toString();
        emit errorOccurred(error);
        return;
    }
    
    SearchResult result = parseSearchResult(json);
    emit searchCompleted(result);
}

void ApiClient::onEpisodeListReplyFinished() {
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) return;
    
    reply->deleteLater();
    emit requestFinished();
    
    if (reply->error() != QNetworkReply::NoError) {
        handleNetworkError(reply);
        return;
    }
    
    QByteArray data = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    
    if (doc.isNull() || !doc.isObject()) {
        ApiError error;
        error.code = -1;
        error.message = "数据解析失败";
        emit errorOccurred(error);
        return;
    }
    
    QJsonObject json = doc.object();
    int code = json["code"].toInt();
    
    LogManager::instance()->log(
        QString("API Response: Episode List - Code: %1").arg(code),
        LogLevel::Info
    );
    
    if (code != 200 && code != 0) {
        ApiError error;
        error.code = code;
        error.message = json["title"].toString();
        emit errorOccurred(error);
        return;
    }
    
    EpisodeList list = parseEpisodeList(json);
    emit episodeListReceived(list);
}

void ApiClient::onVideoUrlReplyFinished() {
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) return;
    
    reply->deleteLater();
    emit requestFinished();
    
    if (reply->error() != QNetworkReply::NoError) {
        handleNetworkError(reply);
        return;
    }
    
    QByteArray data = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    
    if (doc.isNull() || !doc.isObject()) {
        ApiError error;
        error.code = -1;
        error.message = "数据解析失败";
        emit errorOccurred(error);
        return;
    }
    
    QJsonObject json = doc.object();
    int code = json["code"].toInt();
    
    LogManager::instance()->log(
        QString("API Response: Video URL - Code: %1").arg(code),
        LogLevel::Info
    );
    
    if (code != 200 && code != 0) {
        ApiError error;
        error.code = code;
        error.message = json["title"].toString();
        emit errorOccurred(error);
        return;
    }
    
    VideoInfo info = parseVideoInfo(json);
    emit videoUrlReceived(info);
}

void ApiClient::onCategoryListReplyFinished() {
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) return;
    
    reply->deleteLater();
    emit requestFinished();
    
    if (reply->error() != QNetworkReply::NoError) {
        handleNetworkError(reply);
        return;
    }
    
    QByteArray data = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    
    if (doc.isNull() || !doc.isObject()) {
        ApiError error;
        error.code = -1;
        error.message = "数据解析失败";
        emit errorOccurred(error);
        return;
    }
    
    QJsonObject json = doc.object();
    int code = json["code"].toInt();
    
    LogManager::instance()->log(
        QString("API Response: Category - Code: %1").arg(code),
        LogLevel::Info
    );
    
    if (code != 200 && code != 0) {
        ApiError error;
        error.code = code;
        error.message = json["title"].toString();
        emit errorOccurred(error);
        return;
    }
    
    CategoryResult result = parseCategoryResult(json);
    emit categoryListReceived(result);
}

void ApiClient::onRecommendationsReplyFinished() {
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) return;
    
    reply->deleteLater();
    emit requestFinished();
    
    if (reply->error() != QNetworkReply::NoError) {
        handleNetworkError(reply);
        return;
    }
    
    QByteArray data = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(data);
    
    if (doc.isNull() || !doc.isObject()) {
        ApiError error;
        error.code = -1;
        error.message = "数据解析失败";
        emit errorOccurred(error);
        return;
    }
    
    QJsonObject json = doc.object();
    int code = json["code"].toInt();
    
    LogManager::instance()->log(
        QString("API Response: Recommendations - Code: %1").arg(code),
        LogLevel::Info
    );
    
    if (code != 200 && code != 0) {
        ApiError error;
        error.code = code;
        error.message = json["title"].toString();
        emit errorOccurred(error);
        return;
    }
    
    CategoryResult result = parseCategoryResult(json);
    emit recommendationsReceived(result);
}

void ApiClient::onNetworkError(QNetworkReply::NetworkError error) {
    QNetworkReply* reply = qobject_cast<QNetworkReply*>(sender());
    if (reply) {
        handleNetworkError(reply);
    }
}

void ApiClient::handleNetworkError(QNetworkReply* reply) {
    ApiError error = createNetworkError(reply->error(), reply->errorString());
    
    LogManager::instance()->log(
        QString("API Error: %1 - %2").arg(error.code).arg(error.message),
        LogLevel::Error
    );
    
    emit errorOccurred(error);
}

ApiError ApiClient::createNetworkError(QNetworkReply::NetworkError error, const QString& errorString) {
    ApiError apiError;
    apiError.code = static_cast<int>(error);
    apiError.details = errorString;
    
    switch (error) {
        case QNetworkReply::ConnectionRefusedError:
        case QNetworkReply::RemoteHostClosedError:
        case QNetworkReply::HostNotFoundError:
            apiError.message = "无法连接到服务器，请检查网络连接";
            break;
        case QNetworkReply::TimeoutError:
        case QNetworkReply::OperationCanceledError:
            apiError.message = "网络连接超时，请检查网络设置";
            break;
        case QNetworkReply::SslHandshakeFailedError:
            apiError.message = "安全连接失败，请稍后重试";
            break;
        default:
            apiError.message = "网络请求失败，请稍后重试";
            break;
    }
    
    return apiError;
}
