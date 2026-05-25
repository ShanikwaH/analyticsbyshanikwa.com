import NewsletterForm from '@/components/NewsletterForm'
import ContactForm from '@/components/ContactForm'

export default function Home() {
  return (
    <main className="flex flex-col">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center gap-6 px-6 py-24 text-center">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
          Analytics By Shanikwa
        </h1>
        <p className="max-w-xl text-lg text-zinc-600 dark:text-zinc-400">
          Data analytics, accounting insights, and faith-driven community — helping
          you make sense of your numbers and your purpose.
        </p>
      </section>

      {/* Newsletter */}
      <section className="border-t border-zinc-200 dark:border-zinc-800 px-6 py-16">
        <div className="mx-auto max-w-xl">
          <h2 className="mb-2 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Join the Sunday newsletter
          </h2>
          <p className="mb-6 text-sm text-zinc-500 dark:text-zinc-400">
            Weekly insights on data, finances, and faith. No spam, unsubscribe any time.
          </p>
          <NewsletterForm source="homepage" />
        </div>
      </section>

      {/* Contact */}
      <section className="border-t border-zinc-200 dark:border-zinc-800 px-6 py-16">
        <div className="mx-auto max-w-xl">
          <h2 className="mb-2 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Get in touch
          </h2>
          <p className="mb-6 text-sm text-zinc-500 dark:text-zinc-400">
            Have a question, collaboration idea, or just want to say hello? I read
            every message.
          </p>
          <ContactForm />
        </div>
      </section>
    </main>
  )
}
