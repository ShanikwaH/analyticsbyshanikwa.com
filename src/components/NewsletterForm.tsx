'use client'

import { useActionState } from 'react'
import { subscribeToNewsletter, type NewsletterResult } from '@/app/actions/newsletter'

const initialState: NewsletterResult | null = null

export default function NewsletterForm({ source = 'website' }: { source?: string }) {
  const [state, formAction, isPending] = useActionState(
    (_prev: NewsletterResult | null, formData: FormData) => subscribeToNewsletter(formData),
    initialState
  )

  if (state?.success) {
    return (
      <p className="text-sm font-medium text-green-700 dark:text-green-400">
        {state.message}
      </p>
    )
  }

  return (
    <form action={formAction} className="flex flex-col gap-3 sm:flex-row sm:items-start">
      <input type="hidden" name="source" value={source} />
      <div className="flex flex-col gap-1 flex-1">
        <input
          type="email"
          name="email"
          placeholder="your@email.com"
          required
          className="h-11 rounded-lg border border-zinc-300 bg-white px-4 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-300"
        />
        {state?.success === false && (
          <p className="text-xs text-red-600 dark:text-red-400">{state.error}</p>
        )}
      </div>
      <button
        type="submit"
        disabled={isPending}
        className="h-11 rounded-lg bg-zinc-900 px-5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-60 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {isPending ? 'Subscribing…' : 'Subscribe'}
      </button>
    </form>
  )
}
