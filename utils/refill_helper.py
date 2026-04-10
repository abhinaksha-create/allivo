def build_refill_query():
    query = """
        SELECT 
            p.id,
            p.name,
            c.name AS category_name,
            p.brand,
            p.price,
            p.discount,
            p.image,
            p.refill_days
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.refill_days IS NOT NULL
        ORDER BY p.refill_days ASC, p.id DESC
    """
    return query