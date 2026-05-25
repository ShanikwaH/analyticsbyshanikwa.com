'use server'

import { createClient } from '@/lib/supabase/server'

export type NewsletterResult =
  | { success: true; message: string }
  | { success: false; error: string }

export async function subscribeToNewsletter(
  formData: FormData
): Promise<NewsletterResult> {
  const email = (formData.get('email') as string | null)?.trim().toLowerCase()

  if (!email || !email.includes('@')) {
    return { success: false, error: 'Please enter a valid email address.' }
  }

  const supabase = await createClient()

  const source = (formData.get('source') as string | null) ?? 'website'

  const { error } = await supabase
    .from('newsletter_subscribers')
    .insert({ email, source })

  if (error) {
    // Unique-constraint violation — already subscribed
    if (error.code === '23505') {
      return { success: true, message: "You're already on the list!" }
    }
    console.error('[newsletter] insert error:', error.message)
    return { success: false, error: 'Something went wrong. Please try again.' }
  }

  return { success: true, message: "You're on the list! See you Sunday." }
}
