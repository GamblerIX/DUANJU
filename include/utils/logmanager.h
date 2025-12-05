#ifndef LOGMANAGER_H
#define LOGMANAGER_H

#include <QObject>
#include <QString>
#include <QList>
#include <QDateTime>
#include <QMutex>
#include "models/datamodels.h"

struct LogEntry {
    QDateTime timestamp;
    LogLevel level;
    QString message;
};

class LogManager : public QObject {
    Q_OBJECT

public:
    static LogManager* instance();
    
    void log(const QString& message, LogLevel level = LogLevel::Info);
    void clear();
    QList<LogEntry> entries() const;
    QString exportToString() const;
    bool exportToFile(const QString& filePath);
    
    void setMaxEntries(int max);
    int maxEntries() const;

signals:
    void logAdded(const LogEntry& entry);
    void logsCleared();

private:
    explicit LogManager(QObject* parent = nullptr);
    ~LogManager();
    
    static LogManager* s_instance;
    QList<LogEntry> m_entries;
    int m_maxEntries;
    mutable QMutex m_mutex;
};

#endif // LOGMANAGER_H
