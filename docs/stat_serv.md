```mermaid
erDiagram
    USER_STATS {
        UUID user_id PK
        INT posts_amount
        TIMESTAMP registered_at
        INT likes_provide
        INT time_spent
        INT likes_received
        INT comment_received
        INT subs_received
        TIMESTAMP subs_at
    }

    COMMENT_STATS {
        TIMESTAMP commented_at
        UUID commented_post_id FK
        INT likes_received
        UUID commenter_id FK
        STRING commenter_name
    }

    POSTS_STATS {
        UUID post_id FK
        INT likes_received
        INT views_received
        UUID poster_id FK
        TIMESTAMP created_at
        INT comments_received
    }

    LIKE_STATS {
        UUID post_id PK
        TIMESTAMP liked_at
        UUID liker_id FK
        UUID poster_id FK
        TIMESTAMP created_at
        BOOL subscriber
    }

    POSTS_STATS ||--o{ COMMENT_STATS : related
    USER_STATS ||--o{ POSTS_STATS : related
    POSTS_STATS ||--o{ LIKE_STATS : related