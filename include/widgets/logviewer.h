#ifndef LOGVIEWER_H
#define LOGVIEWER_H

#include <QWidget>
#include <QTextEdit>
#include <QPushButton>
#include "models/datamodels.h"
#include "utils/logmanager.h"

class LogViewer : public QWidget {
    Q_OBJECT

public:
    explicit LogViewer(QWidget* parent = nullptr);
    
    void appendLog(const LogEntry& entry);
    void clear();

signals:
    void exportRequested();

private slots:
    void onClearClicked();
    void onExportClicked();
    void onLogAdded(const LogEntry& entry);

private:
    void setupUI();
    QString formatLogEntry(const LogEntry& entry) const;
    QString getColorForLevel(LogLevel level) const;
    
    QTextEdit* m_logText;
    QPushButton* m_clearBtn;
    QPushButton* m_exportBtn;
    bool m_autoScroll;
};

#endif // LOGVIEWER_H
