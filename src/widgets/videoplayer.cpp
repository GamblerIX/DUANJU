#include "widgets/videoplayer.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QMediaPlayer>
#include <QVideoWidget>
#include <QAudioOutput>
#include <QUrl>

VideoPlayer::VideoPlayer(QWidget* parent)
    : QWidget(parent)
    , m_state(PlaybackState::Stopped)
    , m_currentQuality("1080p")
    , m_duration(0)
    , m_position(0)
{
    setupUI();
    setupPlayer();
}

VideoPlayer::~VideoPlayer() {
#ifndef USE_MPV
    if (m_mediaPlayer) {
        m_mediaPlayer->stop();
    }
#endif
}

void VideoPlayer::setupUI() {
    QVBoxLayout* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(8);
    
    // Video container
    m_videoContainer = new QWidget(this);
    m_videoContainer->setMinimumSize(640, 360);
    m_videoContainer->setStyleSheet("background-color: black;");
    mainLayout->addWidget(m_videoContainer, 1);
    
    // Controls
    QWidget* controlsWidget = new QWidget(this);
    QVBoxLayout* controlsLayout = new QVBoxLayout(controlsWidget);
    controlsLayout->setContentsMargins(8, 4, 8, 8);
    controlsLayout->setSpacing(4);
    
    // Progress slider
    m_progressSlider = new QSlider(Qt::Horizontal, this);
    m_progressSlider->setRange(0, 100);
    connect(m_progressSlider, &QSlider::sliderMoved, this, &VideoPlayer::onSliderMoved);
    controlsLayout->addWidget(m_progressSlider);
    
    // Button row
    QHBoxLayout* buttonLayout = new QHBoxLayout();
    buttonLayout->setSpacing(8);
    
    m_playPauseBtn = new QPushButton("▶", this);
    m_playPauseBtn->setFixedSize(40, 32);
    connect(m_playPauseBtn, &QPushButton::clicked, this, &VideoPlayer::onPlayPauseClicked);
    
    m_stopBtn = new QPushButton("■", this);
    m_stopBtn->setFixedSize(40, 32);
    connect(m_stopBtn, &QPushButton::clicked, this, &VideoPlayer::onStopClicked);
    
    m_timeLabel = new QLabel("00:00 / 00:00", this);
    m_timeLabel->setMinimumWidth(100);
    
    m_volumeSlider = new QSlider(Qt::Horizontal, this);
    m_volumeSlider->setRange(0, 100);
    m_volumeSlider->setValue(100);
    m_volumeSlider->setMaximumWidth(100);
    connect(m_volumeSlider, &QSlider::valueChanged, this, &VideoPlayer::onVolumeChanged);
    
    m_qualityCombo = new QComboBox(this);
    m_qualityCombo->addItems({"360p", "480p", "720p", "1080p", "2160p"});
    m_qualityCombo->setCurrentText("1080p");
    connect(m_qualityCombo, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &VideoPlayer::onQualityChanged);
    
    buttonLayout->addWidget(m_playPauseBtn);
    buttonLayout->addWidget(m_stopBtn);
    buttonLayout->addWidget(m_timeLabel);
    buttonLayout->addStretch();
    buttonLayout->addWidget(new QLabel("音量:", this));
    buttonLayout->addWidget(m_volumeSlider);
    buttonLayout->addWidget(new QLabel("清晰度:", this));
    buttonLayout->addWidget(m_qualityCombo);
    
    controlsLayout->addLayout(buttonLayout);
    mainLayout->addWidget(controlsWidget);
}

void VideoPlayer::setupPlayer() {
#ifndef USE_MPV
    m_videoWidget = new QVideoWidget(m_videoContainer);
    QVBoxLayout* videoLayout = new QVBoxLayout(m_videoContainer);
    videoLayout->setContentsMargins(0, 0, 0, 0);
    videoLayout->addWidget(m_videoWidget);
    
    m_mediaPlayer = new QMediaPlayer(this);
    m_audioOutput = new QAudioOutput(this);
    m_mediaPlayer->setAudioOutput(m_audioOutput);
    m_mediaPlayer->setVideoOutput(m_videoWidget);
    
    connect(m_mediaPlayer, &QMediaPlayer::positionChanged, this, &VideoPlayer::updatePosition);
    connect(m_mediaPlayer, &QMediaPlayer::durationChanged, this, &VideoPlayer::updateDuration);
    connect(m_mediaPlayer, &QMediaPlayer::errorOccurred, this, &VideoPlayer::handleMediaError);
    connect(m_mediaPlayer, &QMediaPlayer::playbackStateChanged, this, [this](QMediaPlayer::PlaybackState state) {
        switch (state) {
            case QMediaPlayer::StoppedState:
                m_state = PlaybackState::Stopped;
                m_playPauseBtn->setText("▶");
                break;
            case QMediaPlayer::PlayingState:
                m_state = PlaybackState::Playing;
                m_playPauseBtn->setText("⏸");
                break;
            case QMediaPlayer::PausedState:
                m_state = PlaybackState::Paused;
                m_playPauseBtn->setText("▶");
                break;
        }
        emit stateChanged(m_state);
    });
#endif
}

void VideoPlayer::play(const QString& url) {
#ifndef USE_MPV
    m_mediaPlayer->setSource(QUrl(url));
    m_mediaPlayer->play();
#endif
    m_state = PlaybackState::Playing;
    m_playPauseBtn->setText("⏸");
    emit stateChanged(m_state);
}

void VideoPlayer::pause() {
#ifndef USE_MPV
    m_mediaPlayer->pause();
#endif
    m_state = PlaybackState::Paused;
    m_playPauseBtn->setText("▶");
    emit stateChanged(m_state);
}

void VideoPlayer::resume() {
#ifndef USE_MPV
    m_mediaPlayer->play();
#endif
    m_state = PlaybackState::Playing;
    m_playPauseBtn->setText("⏸");
    emit stateChanged(m_state);
}

void VideoPlayer::stop() {
#ifndef USE_MPV
    m_mediaPlayer->stop();
#endif
    m_state = PlaybackState::Stopped;
    m_playPauseBtn->setText("▶");
    m_progressSlider->setValue(0);
    m_timeLabel->setText("00:00 / 00:00");
    emit stateChanged(m_state);
}

void VideoPlayer::seek(qint64 position) {
#ifndef USE_MPV
    m_mediaPlayer->setPosition(position);
#endif
}

void VideoPlayer::setVolume(int volume) {
#ifndef USE_MPV
    m_audioOutput->setVolume(volume / 100.0f);
#endif
    m_volumeSlider->setValue(volume);
}

void VideoPlayer::setQuality(const QString& quality) {
    m_currentQuality = quality;
    m_qualityCombo->setCurrentText(quality);
}

qint64 VideoPlayer::duration() const {
    return m_duration;
}

qint64 VideoPlayer::position() const {
    return m_position;
}

bool VideoPlayer::isPlaying() const {
    return m_state == PlaybackState::Playing;
}

QString VideoPlayer::currentQuality() const {
    return m_currentQuality;
}

void VideoPlayer::onPlayPauseClicked() {
    if (m_state == PlaybackState::Playing) {
        pause();
    } else {
        resume();
    }
}

void VideoPlayer::onStopClicked() {
    stop();
}

void VideoPlayer::onSliderMoved(int position) {
    qint64 newPos = (m_duration * position) / 100;
    seek(newPos);
}

void VideoPlayer::onVolumeChanged(int volume) {
#ifndef USE_MPV
    m_audioOutput->setVolume(volume / 100.0f);
#endif
}

void VideoPlayer::onQualityChanged(int index) {
    QString quality = m_qualityCombo->currentText();
    if (quality != m_currentQuality) {
        m_currentQuality = quality;
        emit qualityChangeRequested(quality);
    }
}

void VideoPlayer::updatePosition() {
#ifndef USE_MPV
    m_position = m_mediaPlayer->position();
    if (m_duration > 0) {
        m_progressSlider->setValue((m_position * 100) / m_duration);
    }
    m_timeLabel->setText(QString("%1 / %2").arg(formatTime(m_position)).arg(formatTime(m_duration)));
    emit positionChanged(m_position);
#endif
}

void VideoPlayer::updateDuration() {
#ifndef USE_MPV
    m_duration = m_mediaPlayer->duration();
    emit durationChanged(m_duration);
#endif
}

void VideoPlayer::handleMediaError() {
#ifndef USE_MPV
    m_state = PlaybackState::Error;
    emit stateChanged(m_state);
    emit errorOccurred(m_mediaPlayer->errorString());
#endif
}

QString VideoPlayer::formatTime(qint64 ms) const {
    int seconds = ms / 1000;
    int minutes = seconds / 60;
    seconds = seconds % 60;
    return QString("%1:%2").arg(minutes, 2, 10, QChar('0')).arg(seconds, 2, 10, QChar('0'));
}
