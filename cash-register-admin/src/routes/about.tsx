import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: About,
})

function About() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="mb-4 text-2xl font-bold">About</h1>
      <p className="text-gray-600">
        TanStack Start admin panel for the cash register project.
      </p>
    </main>
  )
}
