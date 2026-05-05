import { createClient } from "@supabase/supabase-js";
import { Hono } from 'hono'
import { env } from 'hono/adapter'
import { Database } from "../database.types";


import { z } from 'zod';
import { zValidator } from '@hono/zod-validator';

const schema = z.object({
  id: z.string(),
  amount: z.coerce.number(),
});

const saleSchema = z.object({
  card_id: z.string(),
  product_ids: z.array(z.string()).min(1),
});

const app = new Hono();

app.get("/:id/subtract/:amount", zValidator('param', schema), async (c) => {
    const { id, amount } = c.req.valid('param');

    const { SUPABASE_KEY, SUPABASE_URL } = env<{ SUPABASE_URL: string, SUPABASE_KEY: string }>(c)

    const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);

    const { data: account, error: fetchError } = await supabase.from("accounts").select("*").eq("card_id", id).maybeSingle();

    if (fetchError) throw fetchError;

    if (!account) return c.json({ error: "Account not found" }, 404);

    if (account.balance! < amount) {
        return c.json({
            error: `Insufficient balance`
        }, 422);
    }

    const { error } = await supabase.rpc("update_balance", {
        p_card_id: id,
        amount: -amount
    });

    if (error) throw error;

    const { data, error: refetchError } = await supabase.from("accounts").select("*").eq("card_id", id).maybeSingle();

    if (refetchError) throw refetchError;

    return c.json({
        type: "account",
        name: data!.name,
        balance: data!.balance
    });
});

app.get("/:id/add/:amount", zValidator('param', schema), async (c) => {
    const { id, amount } = c.req.valid('param');

    const { SUPABASE_KEY, SUPABASE_URL } = env<{ SUPABASE_URL: string, SUPABASE_KEY: string }>(c)

    const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);
    await supabase.rpc("update_balance", {
        p_card_id: id,
        amount: amount
    });

    const { data, error } = await supabase.from("accounts").select("*").eq("card_id", id).maybeSingle();

    if (error) throw error;

    if (data) {
        return c.json({
            type: "account",
            name: data.name,
            balance: data.balance
        });
    }

    return c.json(data);
});


app.post('/sales', zValidator('json', saleSchema), async (c) => {
    const { card_id, product_ids } = c.req.valid('json');

    const { SUPABASE_KEY, SUPABASE_URL } = env<{ SUPABASE_URL: string, SUPABASE_KEY: string }>(c);
    const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);

    const { data: account, error: accountError } = await supabase
        .from("accounts")
        .select("*")
        .eq("card_id", card_id)
        .maybeSingle();

    if (accountError) throw accountError;
    if (!account) return c.json({ error: "Account not found" }, 404);

    const { data: products, error: productsError } = await supabase
        .from("products")
        .select("product_id, price")
        .in("product_id", product_ids);

    if (productsError) throw productsError;

    const uniqueProducsIds = new Set(product_ids);

    if (products.length !== uniqueProducsIds.size) {
        const foundIds = new Set(products.map(p => p.product_id));
        const missing = product_ids.filter(id => !foundIds.has(id));
        return c.json({ error: "Products not found", missing }, 404);
    }

    const priceById = new Map(products.map(p => [p.product_id, p.price ?? 0]));
    const total = product_ids.reduce((sum, id) => sum + (priceById.get(id) ?? 0), 0);

    if ((account.balance ?? 0) < total) {
        return c.json({ error: "Insufficient balance" }, 422);
    }

    const { data: sale, error: saleError } = await supabase
        .from("sales")
        .insert({ card_id, total_price: total })
        .select("id")
        .single();

    if (saleError) throw saleError;

    const saleItems = product_ids.map(product_id => ({
        sales_id: sale.id,
        product_id,
        price_at_sale: products.find(p => p.product_id === product_id)!.price,
    }));

    const { error: itemsError } = await supabase.from("sales_products").insert(saleItems);

    if (itemsError) throw itemsError;

    const { error: balanceError } = await supabase.rpc("update_balance", {
        p_card_id: card_id,
        amount: -total,
    });

    if (balanceError) throw balanceError;

    return c.json({ sale_id: sale.id, total, items: saleItems.length }, 201);
});

app.get('/products', async (c) => {
    const { SUPABASE_KEY, SUPABASE_URL } = env<{ SUPABASE_URL: string, SUPABASE_KEY: string }>(c)

    const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);
    const { data, error } = await supabase.from("products").select("product_id, price, label");

    if (error) throw error;

    return c.json(data);
});

app.get('/cards', async (c) => {
    const { SUPABASE_KEY, SUPABASE_URL } = env<{ SUPABASE_URL: string, SUPABASE_KEY: string }>(c)

    const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);
    const adminParam = c.req.query('admin');

    let query = supabase.from("accounts").select("card_id").not("card_id", "is", null);

    if (adminParam === '1') {
        query = query.eq("admin", true);
    } else if (adminParam === '0') {
        query = query.neq("admin", true);
    }

    const { data, error } = await query;

    if (error) throw error;

    return c.json(data.map(row => row.card_id));
});

app.get('/:id', async (c) => {
    const id = c.req.param('id');

    const { SUPABASE_KEY, SUPABASE_URL } = env<{ SUPABASE_URL: string, SUPABASE_KEY: string }>(c)

    const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);
    const { data, error } = await supabase.from("accounts").select("*").eq("card_id", id).maybeSingle();

    if (error) throw error;

    if (data) {
        return c.json({
            type: "account",
            name: data.name,
            balance: data.balance
        });
    }

    return c.json(data);
})

export default app
