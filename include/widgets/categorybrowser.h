#ifndef CATEGORYBROWSER_H
#define CATEGORYBROWSER_H

#include <QWidget>
#include <QComboBox>
#include <QPushButton>
#include <QListWidget>
#include <QLabel>
#include "models/datamodels.h"

class CategoryBrowser : public QWidget {
    Q_OBJECT

public:
    explicit CategoryBrowser(QWidget* parent = nullptr);
    
    void setCategories(const QStringList& categories);
    void setResults(const CategoryResult& result);
    void setLoading(bool loading);

signals:
    void categorySelected(const QString& category);
    void recommendRequested();
    void dramaSelected(const QString& bookId);
    void pageChanged(int offset);

private slots:
    void onCategoryChanged(int index);
    void onRecommendClicked();
    void onItemClicked(QListWidgetItem* item);
    void onPrevPageClicked();
    void onNextPageClicked();

private:
    void setupUI();
    void updatePagination();
    
    QComboBox* m_categoryCombo;
    QPushButton* m_recommendBtn;
    QListWidget* m_resultList;
    QLabel* m_loadingLabel;
    QWidget* m_paginationWidget;
    QPushButton* m_prevButton;
    QPushButton* m_nextButton;
    QLabel* m_pageLabel;
    
    int m_currentOffset;
};

#endif // CATEGORYBROWSER_H
