"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema for GTFS-RT Analytics."""
    # Create rt_feed_raw table
    op.create_table(
        'rt_feed_raw',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('feed_type', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.LargeBinary(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rt_feed_raw_fetched_at', 'rt_feed_raw', ['fetched_at'])
    op.create_index('ix_rt_feed_raw_feed_type', 'rt_feed_raw', ['feed_type'])
    op.create_index('ix_rt_feed_raw_source', 'rt_feed_raw', ['source'])
    op.create_index('ix_rt_feed_raw_fetched_source', 'rt_feed_raw', ['fetched_at', 'source'])

    # Create trip_update_events table
    op.create_table(
        'trip_update_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('trip_id', sa.String(length=255), nullable=False),
        sa.Column('route_id', sa.String(length=255), nullable=True),
        sa.Column('direction_id', sa.Integer(), nullable=True),
        sa.Column('stop_id', sa.String(length=255), nullable=False),
        sa.Column('stop_sequence', sa.Integer(), nullable=False),
        sa.Column('arrival_delay', sa.Integer(), nullable=True),
        sa.Column('departure_delay', sa.Integer(), nullable=True),
        sa.Column('arrival_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('departure_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trip_update_events_fetched_at', 'trip_update_events', ['fetched_at'])
    op.create_index('ix_trip_update_events_trip_id', 'trip_update_events', ['trip_id'])
    op.create_index('ix_trip_update_events_route_id', 'trip_update_events', ['route_id'])
    op.create_index('ix_trip_update_events_stop_id', 'trip_update_events', ['stop_id'])
    op.create_index('ix_trip_update_events_fetched_route', 'trip_update_events', ['fetched_at', 'route_id'])
    op.create_index('ix_trip_update_events_fetched_stop', 'trip_update_events', ['fetched_at', 'stop_id'])
    op.create_index('ix_trip_update_events_trip_stop', 'trip_update_events', ['trip_id', 'stop_id'])

    # Create vehicle_positions table
    op.create_table(
        'vehicle_positions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('vehicle_id', sa.String(length=255), nullable=False),
        sa.Column('trip_id', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('bearing', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vehicle_positions_fetched_at', 'vehicle_positions', ['fetched_at'])
    op.create_index('ix_vehicle_positions_vehicle_id', 'vehicle_positions', ['vehicle_id'])
    op.create_index('ix_vehicle_positions_trip_id', 'vehicle_positions', ['trip_id'])
    op.create_index('ix_vehicle_positions_fetched_vehicle', 'vehicle_positions', ['fetched_at', 'vehicle_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('vehicle_positions')
    op.drop_table('trip_update_events')
    op.drop_table('rt_feed_raw')
