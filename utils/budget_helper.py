def build_budget_query(category=None):
    query = """
        SELECT 
            p.id, p.name, c.name AS category_name, p.subcategory, p.brand,
            p.price, p.discount, p.stock, p.image, p.description,
            p.delivery_type, p.rating, p.is_student_pick, p.refill_days
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE (p.price - p.discount) <= %s
    """
    params = []

    if category:
        query += " AND c.name = %s"
        params.append(category)

    query += " ORDER BY (p.price - p.discount) ASC"
    return query, params