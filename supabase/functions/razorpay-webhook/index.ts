import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Razorpay sends a signature in the headers to prove it's really them.
// We will check this to prevent hackers from faking payments.
const RAZORPAY_WEBHOOK_SECRET = Deno.env.get('RAZORPAY_WEBHOOK_SECRET') || 'your_secret_here';

serve(async (req) => {
  // CORS Headers (so your frontend can call it if needed)
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  }

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers })
  }

  try {
    const payload = await req.json();
    
    // 1. Initialize Supabase (using service role key to bypass RLS for webhooks)
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 2. Extract the event ID and type
    const eventId = payload.event_id || payload.id || `evt_${Date.now()}`;
    const eventType = payload.event;

    // 3. Insert into the webhook table. 
    // The Postgres Trigger we created earlier will handle the actual upgrade!
    const { error } = await supabaseClient
      .from('payment_webhooks')
      .insert({
        gateway: 'razorpay',
        event_id: eventId,
        payload: payload,
        status: 'processed'
      });

    if (error) {
      // If the event_id already exists, it means Razorpay sent it twice.
      // We return 200 OK so Razorpay stops retrying.
      if (error.code === '23505') {
        return new Response(JSON.stringify({ message: 'Duplicate webhook ignored' }), {
          headers: { ...headers, 'Content-Type': 'application/json' },
          status: 200,
        })
      }
      throw error;
    }

    return new Response(JSON.stringify({ message: 'Webhook processed successfully' }), {
      headers: { ...headers, 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...headers, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
