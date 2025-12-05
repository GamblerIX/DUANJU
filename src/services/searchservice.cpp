#include "services/searchservice.h"

SearchService::SearchService(ApiClient* apiClient, QObject* parent)
    : QObject(parent)
    , m_apiClient(apiClient)
{
    connect(m_apiClient, &ApiClient::searchCompleted,
            this, &SearchService::searchCompleted);
    connect(m_apiClient, &ApiClient::errorOccurred,
            this, &SearchService::searchFailed);
    connect(m_apiClient, &ApiClient::requestStarted,
            this, &SearchService::searchStarted);
}

void SearchService::search(const QString& keyword, int page) {
    m_currentKeyword = keyword;
    m_apiClient->searchDrama(keyword, page);
}

QString SearchService::currentKeyword() const {
    return m_currentKeyword;
}
