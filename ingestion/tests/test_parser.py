"""Tests for GTFS-Realtime parser."""
from datetime import datetime, timezone

import pytest
from google.transit import gtfs_realtime_pb2

from parser import GtfsRealtimeParser


@pytest.fixture
def parser():
    """Create a parser instance for testing."""
    return GtfsRealtimeParser()


@pytest.fixture
def sample_trip_update_feed():
    """Create a sample GTFS-RT feed with trip updates."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.timestamp = int(datetime.now(timezone.utc).timestamp())

    entity = feed.entity.add()
    entity.id = "trip_1"

    trip_update = entity.trip_update
    trip_update.trip.trip_id = "TRIP_001"
    trip_update.trip.route_id = "ROUTE_A"
    trip_update.trip.direction_id = 0

    # Add stop time update with delay
    stu = trip_update.stop_time_update.add()
    stu.stop_id = "STOP_123"
    stu.stop_sequence = 5
    stu.arrival.delay = 120  # 2 minutes late
    stu.departure.delay = 150  # 2.5 minutes late

    return feed.SerializeToString()


@pytest.fixture
def sample_vehicle_position_feed():
    """Create a sample GTFS-RT feed with vehicle positions."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.timestamp = int(datetime.now(timezone.utc).timestamp())

    entity = feed.entity.add()
    entity.id = "vehicle_1"

    vehicle = entity.vehicle
    vehicle.vehicle.id = "BUS_001"
    vehicle.trip.trip_id = "TRIP_001"
    vehicle.position.latitude = 40.7128
    vehicle.position.longitude = -74.0060
    vehicle.position.bearing = 180.0
    vehicle.position.speed = 15.5

    return feed.SerializeToString()


def test_parse_valid_feed(parser, sample_trip_update_feed):
    """Test parsing a valid GTFS-RT feed."""
    feed = parser.parse_feed(sample_trip_update_feed)

    assert feed is not None
    assert feed.header.gtfs_realtime_version == "2.0"
    assert len(feed.entity) == 1


def test_parse_invalid_feed(parser):
    """Test parsing invalid protobuf data."""
    invalid_data = b"not a valid protobuf"
    feed = parser.parse_feed(invalid_data)

    assert feed is None


def test_extract_trip_updates(parser, sample_trip_update_feed):
    """Test extracting trip update events."""
    feed = parser.parse_feed(sample_trip_update_feed)
    fetched_at = datetime.now(timezone.utc)
    events = parser.extract_trip_updates(feed, fetched_at)

    assert len(events) == 1
    event = events[0]

    assert event["trip_id"] == "TRIP_001"
    assert event["route_id"] == "ROUTE_A"
    assert event["direction_id"] == 0
    assert event["stop_id"] == "STOP_123"
    assert event["stop_sequence"] == 5
    assert event["arrival_delay"] == 120
    assert event["departure_delay"] == 150
    assert event["fetched_at"] == fetched_at


def test_extract_trip_updates_missing_trip_id(parser):
    """Test handling of trip updates without trip_id."""
    feed = gtfs_realtime_pb2.FeedMessage()
    entity = feed.entity.add()
    entity.id = "trip_1"
    entity.trip_update.stop_time_update.add().stop_id = "STOP_123"

    fetched_at = datetime.now(timezone.utc)
    events = parser.extract_trip_updates(feed, fetched_at)

    assert len(events) == 0


def test_extract_vehicle_positions(parser, sample_vehicle_position_feed):
    """Test extracting vehicle position data."""
    feed = parser.parse_feed(sample_vehicle_position_feed)
    fetched_at = datetime.now(timezone.utc)
    positions = parser.extract_vehicle_positions(feed, fetched_at)

    assert len(positions) == 1
    position = positions[0]

    assert position["vehicle_id"] == "BUS_001"
    assert position["trip_id"] == "TRIP_001"
    assert position["latitude"] == 40.7128
    assert position["longitude"] == -74.0060
    assert position["bearing"] == 180.0
    assert position["speed"] == 15.5
    assert position["fetched_at"] == fetched_at


def test_extract_vehicle_positions_missing_vehicle_id(parser):
    """Test handling of vehicle positions without vehicle_id."""
    feed = gtfs_realtime_pb2.FeedMessage()
    entity = feed.entity.add()
    entity.id = "vehicle_1"
    entity.vehicle.position.latitude = 40.0
    entity.vehicle.position.longitude = -74.0

    fetched_at = datetime.now(timezone.utc)
    positions = parser.extract_vehicle_positions(feed, fetched_at)

    assert len(positions) == 0


def test_extract_vehicle_positions_missing_coordinates(parser):
    """Test handling of vehicle positions without coordinates."""
    feed = gtfs_realtime_pb2.FeedMessage()
    entity = feed.entity.add()
    entity.id = "vehicle_1"
    entity.vehicle.vehicle.id = "BUS_001"

    fetched_at = datetime.now(timezone.utc)
    positions = parser.extract_vehicle_positions(feed, fetched_at)

    assert len(positions) == 0
