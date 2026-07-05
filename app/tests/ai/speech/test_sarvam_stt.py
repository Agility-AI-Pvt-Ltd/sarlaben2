import pytest

from app.ai.speech.stt.sarvam_stt import SarvamSTT


@pytest.mark.parametrize(
    ("audio", "expected"),
    [
        (b"RIFF\x00\x00\x00\x00WAVE", ("utterance.wav", "audio/wav")),
        (b"\x1aE\xdf\xa3webm", ("utterance.webm", "audio/webm")),
        (b"OggSopus", ("utterance.ogg", "audio/ogg")),
        (b"\x00\x00\x00\x18ftypM4A ", ("utterance.m4a", "audio/mp4")),
        (b"ID3audio", ("utterance.mp3", "audio/mpeg")),
    ],
)
def test_audio_metadata_detects_supported_containers(
    audio: bytes, expected: tuple[str, str]
):
    assert SarvamSTT._audio_metadata(audio) == expected


def test_multipart_body_labels_wav_audio() -> None:
    body = SarvamSTT()._multipart_body("boundary", {}, b"RIFF\x00\x00\x00\x00WAVE")

    assert b'filename="utterance.wav"' in body
