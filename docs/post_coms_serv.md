```mermaid
erDiagram
    POSTS {
        UUID post_id PK
        UUID user_id FK
        STRING type
        STRING description
        TIMESTAMP posted_at
        TIMESTAMP changed_at
    }

    PHOTO {
        UUID post_id PK, FK
        STRING url
        STRING place
        INT file_size
        INT width
        INT height
    }

    COMMENTS {
        UUID post_id FK
        UUID user_post_id FK
        UUID user_comm_id FK
        INT likes_amount
        TIMESTAMP commented_at
    }

    POSTS ||--o{ PHOTO : has
    POSTS ||--o{ COMMENTS : has