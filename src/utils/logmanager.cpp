#include "utils/logmanager.h"
#include <QFile>
#include <QTextStream>
#include <QMutexLocker>

LogManager* LogManager::s_instance = nullptr;

LogManager* LogManager::instance() {
    if (!s_instance) {
        s_instance = new LogManager();
    }
    return s_instance;
}

LogManager::LogManager(QObject* parent)
    : QObject(parent)
    , m_maxEntries(1000)
{
}

LogManager::~LogManager() = default;

void LogManager::log(const QString& message, LogLevel level) {
    QMutexLocker locker(&m_mutex);
    
    LogEntry entry;
    entry.timestamp = QDateTime::currentDateTime();
    entry.level = level;
    entry.message = message;
    
    m_entries.append(entry);
    
    // Trim old entries if exceeding max
    while (m_entries.size() > m_maxEntries) {
        m_entries.removeFirst();
    }
    
    locker.unlock();
    emit logAdded(entry);
}

void LogManager::clear() {
    QMutexLocker locker(&m_mutex);
    m_entries.clear();
    locker.unlock();
    emit logsCleared();
}

QList<LogEntry> LogManager::entries() const {
    QMutexLocker locker(&m_mutex);
    return m_entries;
}

QString LogManager::exportToString() const {
    QMutexLocker locker(&m_mutex);
    
    QString result;
    QTextStream stream(&result);
    
    for (const LogEntry& entry : m_entries) {
        stream << entry.timestamp.toString(Qt::ISODate) << " "
               << "[" << logLevelToString(entry.level) << "] "
               << entry.message << "\n";
    }
    
    return result;
}

bool LogManager::exportToFile(const QString& filePath) {
    QFile file(filePath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return false;
    }
    
    QTextStream stream(&file);
    stream << exportToString();
    file.close();
    
    return true;
}

void LogManager::setMaxEntries(int max) {
    QMutexLocker locker(&m_mutex);
    m_maxEntries = max;
    
    while (m_entries.size() > m_maxEntries) {
        m_entries.removeFirst();
    }
}

int LogManager::maxEntries() const {
    return m_maxEntries;
}
