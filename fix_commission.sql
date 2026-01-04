    SELECT c.*, u.username as referrer_name
    FROM commissions c
    LEFT JOIN users u ON c.referrer_id = u.id
    ORDER BY c.created_at DESC
