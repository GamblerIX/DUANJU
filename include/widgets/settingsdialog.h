#ifndef SETTINGSDIALOG_H
#define SETTINGSDIALOG_H

#include <QDialog>
#include <QSpinBox>
#include <QComboBox>
#include <QRadioButton>
#include <QButtonGroup>
#include "models/datamodels.h"

class SettingsDialog : public QDialog {
    Q_OBJECT

public:
    explicit SettingsDialog(QWidget* parent = nullptr);
    
    void loadSettings();
    void saveSettings();

private slots:
    void onApplyClicked();
    void onOkClicked();

private:
    void setupUI();
    
    QSpinBox* m_timeoutSpinBox;
    QComboBox* m_qualityCombo;
    QButtonGroup* m_themeGroup;
    QRadioButton* m_lightRadio;
    QRadioButton* m_darkRadio;
    QRadioButton* m_autoRadio;
};

#endif // SETTINGSDIALOG_H
