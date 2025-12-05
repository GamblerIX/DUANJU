#include "widgets/logviewer.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFileDialog>
#include <QScrollBar>

LogViewer::LogViewer(QWidget* parent)
    : QWidget(parent)
    , m_autoScroll(true)
{
    setupUI();
    
    // Connect to LogManager
    connect(LogManager::instance(), &LogManager::logAdded,
            this, &LogViewer::onLogAdded);
    connect(LogManager::instance(), &LogManager::logsCleared,
            this, &LogViewer::clear);
}

void LogViewer::setupUI() {
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(8, 8, 8, 8);
    mainLayout->setSpacing(8);
    
    // Title
    QLabel* titleLabel = new QLabel("日志", this);
    titleLabel->setStyleSheet("font-weight: bold;");
    mainLayout->addWidget(titleLabel);
    
    // Log text area
    m_logText = new QTextEdit(this);
    m_logText->setReadOnly(true);
    m_logText->setFont(QFont("Consolas", 9));
    mainLayout->addWidget(m_logText, 1);
    
    // Buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    buttonLayout->setSpacing(8);
    
    m_clearBtn = new QPushButton("清空", this);
    connect(m_clearBtn, &QPushButton::clicked, this, &LogViewer::onClearClicked);
    
    m_exportBtn = new QPushButton("导出", this);
    connect(m_exportBtn, &QPushButton::clicked, this, &LogViewer::onExportClicked);
    
    buttonLayout->addStretch();
    buttonLayout->addWidget(m_clearBtn);
    buttonLayout->addWidget(m_exportBtn);
    mainLayout->addLayout(buttonLayout);
}

void LogViewer::appendLog(const LogEntry& entry) {
    QString html = formatLogEntry(entry);
    m_logText->append(html);
    
    if (m_autoScroll) {
        QScrollBar* scrollBar = m_logText->verticalScrollBar();
        scrollBar->setValue(scrollBar->maximum());
    }
}

void LogViewer::clear() {
    m_logText->clear();
}

void LogViewer::onClearClicked() {
    LogManager::instance()->clear();
}

void LogViewer::onExportClicked() {
    QString filePath = QFileDialog::getSaveFileName(
        this, "导出日志", "duanju_log.txt", "文本文件 (*.txt)");
    
    if (!filePath.isEmpty()) {
        LogManager::instance()->exportToFile(filePath);
    }
    
    emit exportRequested();
}

void LogViewer::onLogAdded(const LogEntry& entry) {
    appendLog(entry);
}

QString LogViewer::formatLogEntry(const LogEntry& entry) const {
    QString color = getColorForLevel(entry.level);
    QString timestamp = entry.timestamp.toString(Qt::ISODate);
    QString level = logLevelToString(entry.level);
    
    return QString("<span style='color: gray;'>%1</span> "
                   "<span style='color: %2; font-weight: bold;'>[%3]</span> "
                   "<span>%4</span>")
            .arg(timestamp)
            .arg(color)
            .arg(level)
            .arg(entry.message.toHtmlEscaped());
}

QString LogViewer::getColorForLevel(LogLevel level) const {
    switch (level) {
        case LogLevel::Debug: return "#888888";
        case LogLevel::Info: return "#0078d4";
        case LogLevel::Warning: return "#ff8c00";
        case LogLevel::Error: return "#d32f2f";
        default: return "#000000";
    }
}
