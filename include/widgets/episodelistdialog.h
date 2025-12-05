#ifndef EPISODELISTDIALOG_H
#define EPISODELISTDIALOG_H

#include <QDialog>
#include <QListWidget>
#include <QLabel>
#include <QComboBox>
#include "models/datamodels.h"

class EpisodeListDialog : public QDialog {
    Q_OBJECT

public:
    explicit EpisodeListDialog(QWidget* parent = nullptr);
    
    void setEpisodeList(const EpisodeList& list);
    void setLoading(bool loading);
    QString selectedQuality() const;

signals:
    void episodeSelected(const QString& videoId, const QString& quality);

private slots:
    void onItemDoubleClicked(QListWidgetItem* item);

private:
    void setupUI();
    
    QLabel* m_titleLabel;
    QListWidget* m_episodeList;
    QComboBox* m_qualityCombo;
    QLabel* m_loadingLabel;
};

#endif // EPISODELISTDIALOG_H
