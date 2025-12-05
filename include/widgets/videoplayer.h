#ifndef VIDEOPLAYER_H
#define VIDEOPLAYER_H

#include <QWidget>
#include <QSlider>
#include <QPushButton>
#include <QLabel>
#include <QComboBox>
#include "models/datamodels.h"

#ifdef USE_MPV
struct mpv_handle;
#endif

class QMediaPlayer;
class QVideoWidget;
class QAudioOutput;

class VideoPlayer : public QWidget {
    Q_OBJECT

public:
    explicit VideoPlayer(QWidget* parent = nullptr);
    ~VideoPlayer();
    
    void play(const QString& url);
    void pause();
    void resume();
    void stop();
    void seek(qint64 position);
    void setVolume(int volume);
    void setQuality(const QString& quality);
    
    qint64 duration() const;
    qint64 position() const;
    bool isPlaying() const;
    QString currentQuality() const;

signals:
    void positionChanged(qint64 position);
    void durationChanged(qint64 duration);
    void stateChanged(PlaybackState state);
    void errorOccurred(const QString& error);
    void qualityChangeRequested(const QString& quality);

private slots:
    void onPlayPauseClicked();
    void onStopClicked();
    void onSliderMoved(int position);
    void onVolumeChanged(int volume);
    void onQualityChanged(int index);
    void updatePosition();
    void updateDuration();
    void handleMediaError();

private:
    void setupUI();
    void setupPlayer();
    QString formatTime(qint64 ms) const;
    
    QWidget* m_videoContainer;
    QSlider* m_progressSlider;
    QSlider* m_volumeSlider;
    QPushButton* m_playPauseBtn;
    QPushButton* m_stopBtn;
    QLabel* m_timeLabel;
    QComboBox* m_qualityCombo;
    
    PlaybackState m_state;
    QString m_currentQuality;
    qint64 m_duration;
    qint64 m_position;
    
#ifdef USE_MPV
    mpv_handle* m_mpv;
#else
    QMediaPlayer* m_mediaPlayer;
    QVideoWidget* m_videoWidget;
    QAudioOutput* m_audioOutput;
#endif
};

#endif // VIDEOPLAYER_H
