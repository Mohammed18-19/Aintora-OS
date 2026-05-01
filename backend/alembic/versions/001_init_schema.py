"""init schema

Revision ID: 271e0242632e
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '271e0242632e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(10), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('plan', sa.String(50), nullable=True),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_tenants_id', 'tenants', ['id'])
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])

    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_email_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('whatsapp_number', sa.String(30), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('preferred_language', sa.String(10), nullable=True),
        sa.Column('total_bookings', sa.Integer(), nullable=True),
        sa.Column('cancelled_bookings', sa.Integer(), nullable=True),
        sa.Column('conversation_state', sa.String(50), nullable=True),
        sa.Column('conversation_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_id', 'customers', ['id'])
    op.create_index('ix_customers_tenant_id', 'customers', ['tenant_id'])
    op.create_index('ix_customers_whatsapp_number', 'customers', ['whatsapp_number'])

    op.create_table('services',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(5), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('name_translations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('nlp_aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('requires_staff', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_services_id', 'services', ['id'])
    op.create_index('ix_services_tenant_id', 'services', ['tenant_id'])

    op.create_table('staff',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('service_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_staff_id', 'staff', ['id'])
    op.create_index('ix_staff_tenant_id', 'staff', ['tenant_id'])

    op.create_table('business_hours',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('is_open', sa.Boolean(), nullable=True),
        sa.Column('opens_at', sa.Time(), nullable=True),
        sa.Column('closes_at', sa.Time(), nullable=True),
        sa.Column('break_starts_at', sa.Time(), nullable=True),
        sa.Column('break_ends_at', sa.Time(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_hours_id', 'business_hours', ['id'])
    op.create_index('ix_business_hours_tenant_id', 'business_hours', ['tenant_id'])

    op.create_table('whatsapp_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number_id', sa.String(100), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('app_id', sa.String(100), nullable=True),
        sa.Column('waba_id', sa.String(100), nullable=True),
        sa.Column('owner_whatsapp', sa.String(30), nullable=True),
        sa.Column('verify_token', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('away_message', sa.Text(), nullable=True),
        sa.Column('custom_templates', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )
    op.create_index('ix_whatsapp_configs_id', 'whatsapp_configs', ['id'])
    op.create_index('ix_whatsapp_configs_tenant_id', 'whatsapp_configs', ['tenant_id'])

    op.create_table('bookings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('booking_ref', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.String(10), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customer_notes', sa.Text(), nullable=True),
        sa.Column('owner_notes', sa.Text(), nullable=True),
        sa.Column('raw_message', sa.Text(), nullable=True),
        sa.Column('original_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reschedule_count', sa.String(5), nullable=True),
        sa.Column('confirmation_sent', sa.Boolean(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_ref')
    )
    op.create_index('ix_bookings_id', 'bookings', ['id'])
    op.create_index('ix_bookings_booking_ref', 'bookings', ['booking_ref'])
    op.create_index('ix_bookings_scheduled_at', 'bookings', ['scheduled_at'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])
    op.create_index('ix_bookings_tenant_id', 'bookings', ['tenant_id'])

    op.create_table('notification_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('recipient_number', sa.String(30), nullable=False),
        sa.Column('message_body', sa.Text(), nullable=True),
        sa.Column('whatsapp_message_id', sa.String(100), nullable=True),
        sa.Column('meta_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notification_logs_id', 'notification_logs', ['id'])
    op.create_index('ix_notification_logs_tenant_id', 'notification_logs', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('notification_logs')
    op.drop_table('bookings')
    op.drop_table('whatsapp_configs')
    op.drop_table('business_hours')
    op.drop_table('staff')
    op.drop_table('services')
    op.drop_table('customers')
    op.drop_table('users')
    op.drop_table('tenants')