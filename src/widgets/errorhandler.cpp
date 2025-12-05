#include "widgets/errorhandler.h"
#include <QHBoxLayout>
#include <QGraphicsDropShadowEffect>

ErrorHandler::ErrorHandler(QWidget* parent)
    : QWidget(parent)
{
    setupUI();
    
    m_autoHideTimer = new QTimer(this);
    m_autoHideTimer->setSingleShot(true);
    connect(m_autoHideTimer, &QTimer::timeout, this, &ErrorHandler::onAutoHide);
    
    QWidget::hide();
}

void ErrorHandler::setupUI() {
    setFixedHeight(48);
    setStyleSheet(R"(
        ErrorHandler {
            background-color: #fdecea;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
        }
    )");
    
    // Add shadow effect
    QGraphicsDropShadowEffect* shadow = new QGraphicsDropShadowEffect(this);
    shadow->setBlurRadius(10);
    shadow->setColor(QColor(0, 0, 0, 30));
    shadow->setOffset(0, 2);
    setGraphicsEffect(shadow);
    
    QHBoxLayout* layout = new QHBoxLayout(this);
    layout->setContentsMargins(16, 8, 16, 8);
    layout->setSpacing(12);
    
    // Error icon
    QLabel* iconLabel = new QLabel("⚠", this);
    iconLabel->setStyleSheet("color: #d32f2f; font-size: 18px;");
    layout->addWidget(iconLabel);
    
    // Message
    m_messageLabel = new QLabel(this);
    m_messageLabel->setStyleSheet("color: #721c24;");
    m_messageLabel->setWordWrap(true);
    layout->addWidget(m_messageLabel, 1);
    
    // Dismiss button
    m_dismissBtn = new QPushButton("×", this);
    m_dismissBtn->setFixedSize(24, 24);
    m_dismissBtn->setStyleSheet(R"(
        QPushButton {
            background-color: transparent;
            border: none;
            color: #721c24;
            font-size: 18px;
            font-weight: bold;
        }
        QPushButton:hover {
            color: #d32f2f;
        }
    )");
    connect(m_dismissBtn, &QPushButton::clicked, this, &ErrorHandler::onDismissClicked);
    layout->addWidget(m_dismissBtn);
}

void ErrorHandler::showError(const QString& message, int autoHideMs) {
    m_messageLabel->setText(message);
    QWidget::show();
    
    if (autoHideMs > 0) {
        m_autoHideTimer->start(autoHideMs);
    }
}

void ErrorHandler::showError(const ApiError& error, int autoHideMs) {
    showError(formatErrorMessage(error), autoHideMs);
}

void ErrorHandler::hide() {
    m_autoHideTimer->stop();
    QWidget::hide();
}

void ErrorHandler::onDismissClicked() {
    hide();
    emit dismissed();
}

void ErrorHandler::onAutoHide() {
    hide();
}

QString ErrorHandler::formatErrorMessage(const ApiError& error) const {
    if (!error.message.isEmpty()) {
        return error.message;
    }
    return QString("错误代码: %1").arg(error.code);
}
