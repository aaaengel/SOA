```mermaid
erDiagram
    USER {
        UUID user_id PK
        STRING name
        TIMESTAMP created_at
        TIMESTAMP online_at
        STRING email
        STRING status
        DATE bday
    }
    
    USER_SUBS {
        UUID user_id FK
        STRING name
        UUID subscribed_to FK
        TIMESTAMP sub_at
        STRING status
    }

    ACTIVITY_LOG {
        UUID log_id PK
        UUID user_id FK
        STRING action
        TIMESTAMP action_time
        STRING details
    }

    USER ||--o{ USER_SUBS : has
    USER ||--o{ ACTIVITY_LOG : creates