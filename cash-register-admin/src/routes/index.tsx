import { createFileRoute } from '@tanstack/react-router'
import { supabase } from '../utils/supabase'

export const Route = createFileRoute('/')({
  loader: async () => {
    const { data: products } = await supabase.from('products').select();
    
    return { products }
  },
  component: App,
})

function App() {
  const { products } = Route.useLoaderData()

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-bold">Products</h1>
      {products && products.length > 0 ? (
        <ul className="space-y-2">
          {products.map((product) => (
            <li key={product.product_id} className="rounded border border-gray-200 px-4 py-3 text-sm">
              {JSON.stringify(product)}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-500">No products found.</p>
      )}
    </main>
  )
}
