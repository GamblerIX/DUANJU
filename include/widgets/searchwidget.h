#ifndef SEARCHWIDGET_H
#define SEARCHWIDGET_H

#include <QWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QListWidget>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include "models/datamodels.h"

class SearchWidget : public QWidget {
    Q_OBJECT

public:
    explicit SearchWidget(QWidget* parent = nullptr);
    
    QString searchText() const;
    void setResults(const SearchResult& result);
    void setLoading(bool loading);
    void showError(const QString& message);
    void showNoResults();
    void clearResults();
    
    // Input validation
    static bool isValidSearchInput(const QString& input);

signals:
    void searchRequested(const QString& keyword);
    void dramaSelected(const QString& bookId);
    void pageChanged(int page);

private slots:
    void onSearchClicked();
    void onItemClicked(QListWidgetItem* item);
    void onPrevPageClicked();
    void onNextPageClicked();

private:
    void setupUI();
    void updatePagination();
    
    QLineEdit* m_searchInput;
    QPushButton* m_searchButton;
    QListWidget* m_resultList;
    QLabel* m_loadingLabel;
    QLabel* m_messageLabel;
    QWidget* m_paginationWidget;
    QPushButton* m_prevButton;
    QPushButton* m_nextButton;
    QLabel* m_pageLabel;
    
    int m_currentPage;
    int m_totalPages;
};

#endif // SEARCHWIDGET_H
