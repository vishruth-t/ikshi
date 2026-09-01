import pytest
from attendance.temporal_confirmation import TemporalConfirmationTracker
from database.models import RecognitionResult

def test_temporal_tracker_multi_candidate_tracking():
    tracker = TemporalConfirmationTracker(required_frames=3)

    # Frame 1: Both Student 1 (Darshan) and Student 2 (Alice) detected
    r1_s1 = tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.9))
    r1_s2 = tracker.process_result(RecognitionResult(student_id=2, name="Alice", similarity=0.88))
    assert r1_s1.confirmed is False
    assert r1_s2.confirmed is False

    # Frame 2: Both detected again
    r2_s1 = tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.91))
    r2_s2 = tracker.process_result(RecognitionResult(student_id=2, name="Alice", similarity=0.89))
    assert r2_s1.confirmed is False
    assert r2_s2.confirmed is False

    # Frame 3: Both reach 3 consecutive frames -> Confirmed!
    r3_s1 = tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.92))
    r3_s2 = tracker.process_result(RecognitionResult(student_id=2, name="Alice", similarity=0.90))
    assert r3_s1.confirmed is True
    assert r3_s2.confirmed is True

def test_temporal_tracker_decay_missing():
    tracker = TemporalConfirmationTracker(required_frames=3)

    # Student 1 seen twice
    tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.9))
    tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.9))
    assert tracker.candidate_counts[1] == 2

    # Frame where only Student 2 is present -> Student 1 decayed/removed
    tracker.process_result(RecognitionResult(student_id=2, name="Alice", similarity=0.9))
    tracker.decay_missing(active_ids={2})

    assert 1 not in tracker.candidate_counts
    assert tracker.candidate_counts[2] == 1

def test_temporal_tracker_reset_student():
    tracker = TemporalConfirmationTracker(required_frames=3)

    tracker.process_result(RecognitionResult(student_id=1, name="Darshan", similarity=0.9))
    tracker.process_result(RecognitionResult(student_id=2, name="Alice", similarity=0.9))

    tracker.reset_student(1)
    assert 1 not in tracker.candidate_counts
    assert 2 in tracker.candidate_counts
