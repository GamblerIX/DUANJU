#ifndef ERRORHANDLER_H
#define ERRORHANDLER_H

#include <QWidget>
#include <QLabel>
#include <QPushButton>
#include <QTimer>
#include "models/datamodels.h"

class ErrorHandler : public QWidget {
    Q_OBJECT

public:
    explicit ErrorHandler(QWidget* parent = nullptr);
    
    void showError(const QString& message, int autoHideMs = 5000);
    void showError(const ApiError& error, int autoHideMs = 5000);
    void hide();

signals:
    void dismissed();

private slots:
    void onDismissClicked();
    void onAutoHide();

private:
    void setupUI();
    QString formatErrorMessage(const ApiError& error) const;
    
    QLabel* m_messageLabel;
    QPushButton* m_dismissBtn;
    QTimer* m_autoHideTimer;
};

#endif // ERRORHANDLER_H
