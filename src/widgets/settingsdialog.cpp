#include "widgets/settingsdialog.h"
#include "utils/configmanager.h"
#include "utils/thememanager.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QGroupBox>
#include <QPushButton>
#include <QLabel>

SettingsDialog::SettingsDialog(QWidget* parent)
    : QDialog(parent)
{
    setupUI();
    setWindowTitle("设置");
    resize(400, 300);
    loadSettings();
}

void SettingsDialog::setupUI() {
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(16, 16, 16, 16);
    mainLayout->setSpacing(16);
    
    // API Settings
    QGroupBox* apiGroup = new QGroupBox("API 设置", this);
    QFormLayout* apiLayout = new QFormLayout(apiGroup);
    
    m_timeoutSpinBox = new QSpinBox(this);
    m_timeoutSpinBox->setRange(1000, 60000);
    m_timeoutSpinBox->setSingleStep(1000);
    m_timeoutSpinBox->setSuffix(" ms");
    apiLayout->addRow("请求超时:", m_timeoutSpinBox);
    
    mainLayout->addWidget(apiGroup);
    
    // Video Settings
    QGroupBox* videoGroup = new QGroupBox("视频设置", this);
    QFormLayout* videoLayout = new QFormLayout(videoGroup);
    
    m_qualityCombo = new QComboBox(this);
    m_qualityCombo->addItems({"360p", "480p", "720p", "1080p", "2160p"});
    videoLayout->addRow("默认清晰度:", m_qualityCombo);
    
    mainLayout->addWidget(videoGroup);
    
    // Theme Settings
    QGroupBox* themeGroup = new QGroupBox("主题设置", this);
    QVBoxLayout* themeLayout = new QVBoxLayout(themeGroup);
    
    m_themeGroup = new QButtonGroup(this);
    
    m_lightRadio = new QRadioButton("浅色模式", this);
    m_darkRadio = new QRadioButton("深色模式", this);
    m_autoRadio = new QRadioButton("跟随系统", this);
    
    m_themeGroup->addButton(m_lightRadio, static_cast<int>(ThemeMode::Light));
    m_themeGroup->addButton(m_darkRadio, static_cast<int>(ThemeMode::Dark));
    m_themeGroup->addButton(m_autoRadio, static_cast<int>(ThemeMode::Auto));
    
    themeLayout->addWidget(m_lightRadio);
    themeLayout->addWidget(m_darkRadio);
    themeLayout->addWidget(m_autoRadio);
    
    mainLayout->addWidget(themeGroup);
    
    mainLayout->addStretch();
    
    // Buttons
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    buttonLayout->setSpacing(8);
    
    QPushButton* applyBtn = new QPushButton("应用", this);
    connect(applyBtn, &QPushButton::clicked, this, &SettingsDialog::onApplyClicked);
    
    QPushButton* okBtn = new QPushButton("确定", this);
    connect(okBtn, &QPushButton::clicked, this, &SettingsDialog::onOkClicked);
    
    QPushButton* cancelBtn = new QPushButton("取消", this);
    connect(cancelBtn, &QPushButton::clicked, this, &QDialog::reject);
    
    buttonLayout->addStretch();
    buttonLayout->addWidget(applyBtn);
    buttonLayout->addWidget(okBtn);
    buttonLayout->addWidget(cancelBtn);
    mainLayout->addLayout(buttonLayout);
}

void SettingsDialog::loadSettings() {
    ConfigManager* config = ConfigManager::instance();
    
    m_timeoutSpinBox->setValue(config->apiTimeout());
    m_qualityCombo->setCurrentText(config->defaultQuality());
    
    switch (config->themeMode()) {
        case ThemeMode::Light:
            m_lightRadio->setChecked(true);
            break;
        case ThemeMode::Dark:
            m_darkRadio->setChecked(true);
            break;
        case ThemeMode::Auto:
        default:
            m_autoRadio->setChecked(true);
            break;
    }
}

void SettingsDialog::saveSettings() {
    ConfigManager* config = ConfigManager::instance();
    
    config->setApiTimeout(m_timeoutSpinBox->value());
    config->setDefaultQuality(m_qualityCombo->currentText());
    
    ThemeMode mode = static_cast<ThemeMode>(m_themeGroup->checkedId());
    config->setThemeMode(mode);
    
    config->save();
    
    // Apply theme immediately
    ThemeManager::instance()->setThemeMode(mode);
}

void SettingsDialog::onApplyClicked() {
    saveSettings();
}

void SettingsDialog::onOkClicked() {
    saveSettings();
    accept();
}
