#ifndef CATEGORYSERVICE_H
#define CATEGORYSERVICE_H

#include <QObject>
#include "api/apiclient.h"
#include "models/datamodels.h"

class CategoryService : public QObject {
    Q_OBJECT

public:
    explicit CategoryService(ApiClient* apiClient, QObject* parent = nullptr);
    
    void fetchCategory(const QString& category, int offset = 1);
    void fetchRecommendations();
    QString currentCategory() const;

signals:
    void fetchStarted();
    void categoryFetched(const CategoryResult& result);
    void recommendationsFetched(const CategoryResult& result);
    void fetchFailed(const ApiError& error);

private:
    ApiClient* m_apiClient;
    QString m_currentCategory;
};

#endif // CATEGORYSERVICE_H
