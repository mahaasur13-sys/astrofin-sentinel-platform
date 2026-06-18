${message}

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}

Revision: ${repr(up_revision)}
Downgrade: ${repr(down_revision)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
