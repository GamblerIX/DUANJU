#include "widgets/episodelistdialog.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>

EpisodeListDialog::EpisodeListDialog(QWidget* parent)
    : QDialog(parent)
{
    setupUI();
    setWindowTitle("剧集列表");
    resize(400, 500);
}

void EpisodeListDialog::setupUI() {
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(16, 16, 16, 16);
    mainLayout->setSpacing(12);
    
    // Title
    m_titleLabel = new QLabel(this);
    m_titleLabel->setStyleSheet("font-size: 16px; font-weight: bold;");
    mainLayout->addWidget(m_titleLabel);
    
    // Quality selection
    QHBoxLayout* qualityLayout = new QHBoxLayout();
    qualityLayout->addWidget(new QLabel("清晰度:", this));
    
    m_qualityCombo = new QComboBox(this);
    m_qualityCombo->addItems({"360p", "480p", "720p", "1080p", "2160p"});
    m_qualityCombo->setCurrentText("1080p");
    qualityLayout->addWidget(m_qualityCombo);
    qualityLayout->addStretch();
    mainLayout->addLayout(qualityLayout);
    
    // Loading indicator
    m_loadingLabel = new QLabel("正在加载...", this);
    m_loadingLabel->setAlignment(Qt::AlignCenter);
    m_loadingLabel->hide();
    mainLayout->addWidget(m_loadingLabel);
    
    // Episode list
    m_episodeList = new QListWidget(this);
    m_episodeList->setSpacing(2);
    connect(m_episodeList, &QListWidget::itemDoubleClicked,
            this, &EpisodeListDialog::onItemDoubleClicked);
    mainLayout->addWidget(m_episodeList, 1);
    
    // Hint
    QLabel* hintLabel = new QLabel("双击剧集开始播放", this);
    hintLabel->setStyleSheet("color: gray;");
    hintLabel->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(hintLabel);
    
    // Close button
    QPushButton* closeBtn = new QPushButton("关闭", this);
    connect(closeBtn, &QPushButton::clicked, this, &QDialog::close);
    mainLayout->addWidget(closeBtn);
}

void EpisodeListDialog::setEpisodeList(const EpisodeList& list) {
    m_titleLabel->setText(list.dramaName);
    m_episodeList->clear();
    
    for (const EpisodeInfo& episode : list.episodes) {
        QListWidgetItem* item = new QListWidgetItem(m_episodeList);
        QString text = QString("第 %1 集").arg(episode.episodeNumber);
        if (!episode.title.isEmpty()) {
            text += QString(" - %1").arg(episode.title);
        }
        if (!episode.duration.isEmpty()) {
            text += QString(" (%1)").arg(episode.duration);
        }
        item->setText(text);
        item->setData(Qt::UserRole, episode.videoId);
    }
}

void EpisodeListDialog::setLoading(bool loading) {
    m_loadingLabel->setVisible(loading);
    m_episodeList->setEnabled(!loading);
}

QString EpisodeListDialog::selectedQuality() const {
    return m_qualityCombo->currentText();
}

void EpisodeListDialog::onItemDoubleClicked(QListWidgetItem* item) {
    QString videoId = item->data(Qt::UserRole).toString();
    if (!videoId.isEmpty()) {
        emit episodeSelected(videoId, selectedQuality());
    }
}
