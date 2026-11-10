import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Get SLA config
  const { data: configs } = await supabase
    .from('sla_config').select('*').eq('is_active', true)

  if (!configs) return new Response('no config')

  // Apply SLA deadlines to new tickets without deadlines
  for (const config of configs) {
    const deadline = new Date(
      Date.now() + config.resolution_time_minutes * 60000
    ).toISOString()

    await supabase.from('tickets')
      .update({ sla_deadline: deadline })
      .eq('issue_type', config.issue_type)
      .is('sla_deadline', null)
      .eq('status', 'open')
  }

  return new Response('SLA applied')
})