#ifndef SEARCHSERVICE_H
#define SEARCHSERVICE_H

#include <QObject>
#include "api/apiclient.h"
#include "models/datamodels.h"

class SearchService : public QObject {
    Q_OBJECT

public:
    explicit SearchService(ApiClient* apiClient, QObject* parent = nullptr);
    
    void search(const QString& keyword, int page = 1);
    QString currentKeyword() const;

signals:
    void searchStarted();
    void searchCompleted(const SearchResult& result);
    void searchFailed(const ApiError& error);

private:
    ApiClient* m_apiClient;
    QString m_currentKeyword;
};

#endif // SEARCHSERVICE_H
