import pytest
from attendance.temporal_confirmation import TemporalConfirmationTracker
from database.models import RecognitionResult

def test_temporal_confirmation_tracker():
    tracker = TemporalConfirmationTracker(required_frames=3)

    # Frame 1: Candidate Darshan (id=1) -> Unconfirmed
    res1 = RecognitionResult(student_id=1, name="Darshan", similarity=0.85)
    out1 = tracker.process_result(res1)
    assert out1.confirmed is False

    # Frame 2: Candidate Darshan (id=1) -> Unconfirmed
    res2 = RecognitionResult(student_id=1, name="Darshan", similarity=0.86)
    out2 = tracker.process_result(res2)
    assert out2.confirmed is False

    # Frame 3: Candidate Darshan (id=1) -> Confirmed (3 consecutive frames)
    res3 = RecognitionResult(student_id=1, name="Darshan", similarity=0.87)
    out3 = tracker.process_result(res3)
    assert out3.confirmed is True

def test_temporal_confirmation_reset_on_identity_change():
    tracker = TemporalConfirmationTracker(required_frames=3)

    tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.85))
    tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.85))
    
    # Identity changes to Alice (id=2)
    res_diff = RecognitionResult(student_id=2, name="Alice", similarity=0.88)
    out_diff = tracker.process_result(res_diff)
    assert out_diff.confirmed is False
    assert tracker.consecutive_count == 1

def test_temporal_confirmation_reset_on_unknown():
    tracker = TemporalConfirmationTracker(required_frames=3)

    tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.85))
    
    # Unknown face -> Reset
    res_unknown = RecognitionResult(student_id=None, name="Unknown", similarity=0.40)
    out_unk = tracker.process_result(res_unknown)
    assert out_unk.confirmed is False
    assert tracker.consecutive_count == 0
