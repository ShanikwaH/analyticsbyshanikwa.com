'use client'

import { useActionState } from 'react'
import { submitContactForm, type ContactResult } from '@/app/actions/contact'

const initialState: ContactResult | null = null

export default function ContactForm() {
  const [state, formAction, isPending] = useActionState(
    (_prev: ContactResult | null, formData: FormData) => submitContactForm(formData),
    initialState
  )

  if (state?.success) {
    return (
      <p className="rounded-lg bg-green-50 px-4 py-3 text-sm font-medium text-green-700 dark:bg-green-900/20 dark:text-green-400">
        {state.message}
      </p>
    )
  }

  return (
    <form action={formAction} className="flex flex-col gap-4">
      {state?.success === false && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
          {state.error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <label htmlFor="contact-name" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Name <span aria-hidden>*</span>
          </label>
          <input
            id="contact-name"
            type="text"
            name="name"
            required
            className="h-11 rounded-lg border border-zinc-300 bg-white px-4 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-300"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="contact-email" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Email <span aria-hidden>*</span>
          </label>
          <input
            id="contact-email"
            type="email"
            name="email"
            required
            className="h-11 rounded-lg border border-zinc-300 bg-white px-4 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-300"
          />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="contact-subject" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Subject
        </label>
        <input
          id="contact-subject"
          type="text"
          name="subject"
          className="h-11 rounded-lg border border-zinc-300 bg-white px-4 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-300"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="contact-message" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Message <span aria-hidden>*</span>
        </label>
        <textarea
          id="contact-message"
          name="message"
          rows={5}
          required
          className="rounded-lg border border-zinc-300 bg-white px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-300"
        />
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="h-11 self-start rounded-lg bg-zinc-900 px-6 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:opacity-60 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {isPending ? 'Sending…' : 'Send message'}
      </button>
    </form>
  )
}
