"""
test_events.py
==============
Production-grade test suite to verify the EduSim reactive event architecture,
wildcard routing, stateful collision tracks, tutor cooldown engines, 
analytics metrics, and chronological replay recorders.
"""

import sys
import os
import time

# Ensure the root of the app is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.src.modules.sandbox.events import (
    EventBus,
    EventContext,
    CollisionTracker,
    TutorTriggerManager,
    ReplayRecorderSubscriber,
    AnalyticsSubscriber,
    LoggingSubscriber,
    TutorSubscriber,
    RuntimeEvents,
    CollisionEvents,
    ObservableEvents,
    InteractionEvents,
    TutorEvents,
    emit_simulation_started,
    emit_observable_updated,
    emit_threshold_exceeded,
    emit_control_changed,
    emit_object_dragged
)


def test_event_bus_routing_and_priorities():
    print("Testing Event Bus Wildcard Routing & Priority Ordering...")
    bus = EventBus()

    # Track callback execution sequence
    execution_order = []

    # Subscriber A: High priority (priority=5) matching prefix wildcard
    def high_priority_listener(context: EventContext):
        execution_order.append("A_high")
        # Check propagation cancellation option
        if context.metadata.get("should_cancel", False):
            bus.cancel_propagation(context)

    # Subscriber B: Low priority (priority=1) matching exact signature
    def low_priority_listener(context: EventContext):
        execution_order.append("B_low")

    # Subscriber C: Medium priority (priority=3) matching general catch-all wildcard '*'
    def catch_all_listener(context: EventContext):
        execution_order.append("C_medium")

    # Subscribe in mixed order
    bus.subscribe("collision.*", high_priority_listener, priority=5)
    bus.subscribe("collision.start", low_priority_listener, priority=1)
    bus.subscribe("*", catch_all_listener, priority=3)

    # Emit standard collision start
    context = EventContext.create(
        event_type="collision.start",
        metadata={"should_cancel": False}
    )
    bus.emit(context)

    # Verify execution order matches priority descending: A (5) -> C (3) -> B (1)
    assert execution_order == ["A_high", "C_medium", "B_low"]
    print("   Priority execution verified successfully: A(5) -> C(3) -> B(1)")

    # Test Propagation Cancellation
    execution_order.clear()
    cancel_context = EventContext.create(
        event_type="collision.start",
        metadata={"should_cancel": True}
    )
    bus.emit(cancel_context)

    # High priority listener A (5) cancels propagation immediately, so C and B must be skipped!
    assert execution_order == ["A_high"]
    print("   Propagation cancellation verified successfully (subsequent subscribers skipped).")

    # Test safe exception shielding: a failing listener must not crash subsequent listeners
    execution_order.clear()
    def failing_listener(context: EventContext):
        raise RuntimeError("Imposed test failure")

    bus.subscribe("collision.*", failing_listener, priority=4) # runs between A (5) and C (3)
    
    safe_context = EventContext.create(
        event_type="collision.start",
        metadata={"should_cancel": False}
    )
    # This must complete without throwing errors
    bus.emit(safe_context)
    
    assert "A_high" in execution_order
    assert "C_medium" in execution_order
    print("✅ Safe exception shielding verified successfully (bus did not crash).")


def test_stateful_collision_tracking():
    print("\nTesting Stateful Collision Tracker...")
    bus = EventBus()
    tracker = CollisionTracker()

    events_received = []
    def collision_callback(context: EventContext):
        events_received.append(context)

    bus.subscribe("collision.*", collision_callback)

    # Frame 1: contact start between body_2 and body_1 (unsorted order)
    frame_1_contacts = [
        {"body_a": "body_2", "body_b": "body_1", "normal": {"x": 1.0, "y": 0.0}, "impulse": 50.0}
    ]
    tracker.process_collisions(bus, frame_count=1, current_collisions=frame_1_contacts)

    # Check COLLISION_START event generated with sorted keys (body_1, body_2)
    assert len(events_received) == 1
    assert events_received[0].event_type == CollisionEvents.COLLISION_START.value
    assert events_received[0].affected_objects == ["body_1", "body_2"]
    assert events_received[0].metadata["impulse"] == 50.0
    print("   COLLISION_START generated successfully.")

    # Frame 2: contact continues (persist)
    events_received.clear()
    tracker.process_collisions(bus, frame_count=2, current_collisions=frame_1_contacts)
    assert len(events_received) == 1
    assert events_received[0].event_type == CollisionEvents.COLLISION_PERSIST.value
    print("   COLLISION_PERSIST generated successfully.")

    # Frame 3: contact separation (exit)
    events_received.clear()
    tracker.process_collisions(bus, frame_count=3, current_collisions=[])
    assert len(events_received) == 1
    assert events_received[0].event_type == CollisionEvents.COLLISION_END.value
    print("   COLLISION_END generated successfully.")
    print("✅ Stateful collision enter/persist/exit streams verified successfully.")


def test_tutor_cooldowns_and_priorities():
    print("\nTesting Socratic Tutor Priority and Cooldown Locks...")
    bus = EventBus()
    manager = TutorTriggerManager()

    hints_dispatched = []
    bus.subscribe("tutor.hint_triggered", lambda ctx: hints_dispatched.append(ctx))

    # Emit Socratic hint: Key concept conservation of energy, high priority
    success = manager.emit_tutor_hint(
        event_bus=bus,
        frame_count=10,
        hint_id="energy_conservation_cue",
        message="Notice how total energy stays constant?",
        concept="mechanical_energy",
        priority_score=5,
        cooldown_seconds=2.0 # 2 seconds cooldown
    )
    assert success is True
    assert len(hints_dispatched) == 1
    assert hints_dispatched[0].priority == 5
    assert hints_dispatched[0].metadata["concept"] == "mechanical_energy"
    print("   High-priority Socratic hint dispatched successfully.")

    # Attempt to dispatch identical hint immediately (must fail due to cooldown lock)
    success_dup = manager.emit_tutor_hint(
        event_bus=bus,
        frame_count=11,
        hint_id="energy_conservation_cue",
        message="Notice how total energy stays constant?",
        concept="mechanical_energy",
        priority_score=5,
        cooldown_seconds=2.0
    )
    assert success_dup is False
    assert len(hints_dispatched) == 1
    print("   Repetitive Socratic hint blocked successfully by cooldown lock.")

    # Simulate waiting 2.5 seconds to expire the cooldown
    time.sleep(2.1)
    
    success_after = manager.emit_tutor_hint(
        event_bus=bus,
        frame_count=15,
        hint_id="energy_conservation_cue",
        message="Notice how total energy stays constant?",
        concept="mechanical_energy",
        priority_score=5,
        cooldown_seconds=2.0
    )
    assert success_after is True
    assert len(hints_dispatched) == 2
    print("   Socratic hint dispatched successfully after cooldown expiration.")
    print("✅ Socratic tutor priority and cooldown mechanics verified successfully.")


def test_recorder_timeline_and_analytics():
    print("\nTesting Replay Recorder & Analytics Subscriber...")
    bus = EventBus()

    # Replay recorder and Analytics trackers
    recorder = ReplayRecorderSubscriber()
    analytics = AnalyticsSubscriber()

    bus.subscribe("*", recorder.on_event)
    bus.subscribe("*", analytics.on_event)

    # Construct mock store to bypass attribute error in emit_simulation_started
    class MockSimulation:
        frame_count = 0
        simulation_time = 0.0
        playback_speed = 1.0
        tick_rate = 60
    class MockStore:
        simulation = MockSimulation()
        
    emit_simulation_started(bus, store=MockStore())
    emit_control_changed(bus, frame_count=1, control_id="mass_slider", value=12.0)
    emit_observable_updated(bus, frame_count=2, observable_id="speed", value=18.5)
    emit_threshold_exceeded(bus, frame_count=3, observable_id="speed", value=18.5, threshold_limit=15.0, comparison_operator=">")
    emit_object_dragged(bus, frame_count=4, object_id="bob", x=450.0, y=300.0)

    # 1. Verify timeline recorded history has 5 events
    history = recorder.export_history()
    assert len(history) == 5
    assert history[0]["event_type"] == RuntimeEvents.SIMULATION_STARTED.value
    assert history[1]["event_type"] == InteractionEvents.CONTROL_CHANGED.value
    assert history[2]["event_type"] == ObservableEvents.OBSERVABLE_UPDATED.value
    assert history[3]["event_type"] == ObservableEvents.THRESHOLD_EXCEEDED.value
    print(f"   Chronological history export verified successfully (Events: {len(history)}).")

    # 2. Verify Analytics aggregated totals
    report = analytics.get_report()
    assert report["total_events"] == 5
    assert report["drags"] == 1
    print(f"   Analytics aggregated report verified successfully: {report}")
    print("✅ Replay timelines and metric logs verified successfully.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING REACTIVE EVENT SYSTEM ARCHITECTURE TESTS")
    print("=" * 60)
    try:
        test_event_bus_routing_and_priorities()
        test_stateful_collision_tracking()
        test_tutor_cooldowns_and_priorities()
        test_recorder_timeline_and_analytics()
        print("\n🎉 ALL REACTIVE EVENT ARCHITECTURE TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ EVENT ARCHITECTURE TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
