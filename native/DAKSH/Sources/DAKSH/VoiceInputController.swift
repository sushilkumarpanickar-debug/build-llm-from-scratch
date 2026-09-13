import AVFoundation
import Speech

@MainActor
final class VoiceInputController: NSObject, ObservableObject {
    enum State {
        case idle
        case requestingPermission
        case listening
        case unavailable
    }

    @Published private(set) var state: State = .idle
    @Published var transcript = ""
    @Published var errorMessage: String?

    private let recognizer = SFSpeechRecognizer()
    private let audioEngine = AVAudioEngine()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?

    var isListening: Bool {
        state == .listening
    }

    func toggle() {
        if isListening {
            stop()
        } else {
            start()
        }
    }

    func start() {
        guard recognizer?.isAvailable == true else {
            state = .unavailable
            errorMessage = "Speech recognition is unavailable on this device."
            return
        }

        state = .requestingPermission
        errorMessage = nil
        transcript = ""
        SFSpeechRecognizer.requestAuthorization { [weak self] status in
            Task { @MainActor in
                guard let self else { return }
                guard status == .authorized else {
                    self.state = .unavailable
                    self.errorMessage = "Allow Speech Recognition in Settings to use voice input."
                    return
                }
                self.requestMicrophonePermission()
            }
        }
    }

    func stop() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        recognitionRequest = nil
        recognitionTask = nil
        state = .idle
    }

    private func requestMicrophonePermission() {
        #if os(iOS)
        AVAudioApplication.requestRecordPermission { [weak self] granted in
            Task { @MainActor in
                guard let self else { return }
                guard granted else {
                    self.state = .unavailable
                    self.errorMessage = "Allow Microphone access in Settings to use voice input."
                    return
                }
                self.beginRecognition()
            }
        }
        #else
        AVCaptureDevice.requestAccess(for: .audio) { [weak self] granted in
            Task { @MainActor in
                guard let self else { return }
                guard granted else {
                    self.state = .unavailable
                    self.errorMessage = "Allow Microphone access in Settings to use voice input."
                    return
                }
                self.beginRecognition()
            }
        }
        #endif
    }

    private func beginRecognition() {
        recognitionTask?.cancel()
        recognitionTask = nil

        #if os(iOS)
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.record, mode: .measurement, options: .duckOthers)
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            state = .idle
            errorMessage = "Unable to configure microphone audio: \(error.localizedDescription)"
            return
        }
        #endif

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        recognitionRequest = request

        let inputNode = audioEngine.inputNode
        inputNode.removeTap(onBus: 0)
        let format = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak request] buffer, _ in
            request?.append(buffer)
        }

        recognitionTask = recognizer?.recognitionTask(with: request) { [weak self] result, error in
            Task { @MainActor in
                guard let self else { return }
                if let result {
                    self.transcript = result.bestTranscription.formattedString
                    if result.isFinal {
                        self.stop()
                    }
                }
                if let error {
                    self.stop()
                    self.errorMessage = "Voice input failed: \(error.localizedDescription)"
                }
            }
        }

        do {
            audioEngine.prepare()
            try audioEngine.start()
            state = .listening
        } catch {
            inputNode.removeTap(onBus: 0)
            state = .idle
            errorMessage = "Unable to start the microphone: \(error.localizedDescription)"
        }
    }
}
