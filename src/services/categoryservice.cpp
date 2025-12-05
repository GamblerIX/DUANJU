#include "services/categoryservice.h"

CategoryService::CategoryService(ApiClient* apiClient, QObject* parent)
    : QObject(parent)
    , m_apiClient(apiClient)
{
    connect(m_apiClient, &ApiClient::categoryListReceived,
            this, &CategoryService::categoryFetched);
    connect(m_apiClient, &ApiClient::recommendationsReceived,
            this, &CategoryService::recommendationsFetched);
    connect(m_apiClient, &ApiClient::errorOccurred,
            this, &CategoryService::fetchFailed);
    connect(m_apiClient, &ApiClient::requestStarted,
            this, &CategoryService::fetchStarted);
}

void CategoryService::fetchCategory(const QString& category, int offset) {
    m_currentCategory = category;
    m_apiClient->getCategoryList(category, offset);
}

void CategoryService::fetchRecommendations() {
    m_apiClient->getRecommendations();
}

QString CategoryService::currentCategory() const {
    return m_currentCategory;
}
