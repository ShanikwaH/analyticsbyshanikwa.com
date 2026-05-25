'use server'

import { createClient } from '@/lib/supabase/server'

export type ContactResult =
  | { success: true; message: string }
  | { success: false; error: string }

export async function submitContactForm(
  formData: FormData
): Promise<ContactResult> {
  const name    = (formData.get('name')    as string | null)?.trim()
  const email   = (formData.get('email')   as string | null)?.trim().toLowerCase()
  const subject = (formData.get('subject') as string | null)?.trim() || null
  const message = (formData.get('message') as string | null)?.trim()

  if (!name)              return { success: false, error: 'Name is required.' }
  if (!email?.includes('@')) return { success: false, error: 'Please enter a valid email.' }
  if (!message)           return { success: false, error: 'Message is required.' }

  const supabase = await createClient()

  const { error } = await supabase
    .from('contact_messages')
    .insert({ name, email, subject, message })

  if (error) {
    console.error('[contact] insert error:', error.message)
    return { success: false, error: 'Something went wrong. Please try again.' }
  }

  return {
    success: true,
    message: "Message received! I'll reply within 48 hours.",
  }
}
