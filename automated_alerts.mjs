import webpush from 'web-push';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);

webpush.setVapidDetails(
  process.env.VAPID_SUBJECT || 'mailto:admin@tryit.com',
  process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY
);

async function sendAutomatedAlerts() {
  console.log('Checking for un-notified critical events...');

  // 1. Fetch events that haven't been notified yet
  const { data: events, error: eventError } = await supabase
    .from('system_events')
    .select('*')
    .in('severity', ['critical', 'warning'])
    .eq('notified', false);

  if (eventError || !events || events.length === 0) {
    console.log('✅ No new critical events to notify.');
    return;
  }

  console.log(`🚨 Found ${events.length} new critical events!`);

  // 2. Fetch all subscribed devices
  const { data: subscriptions, error: subError } = await supabase.from('push_subscriptions').select('*');
  
  if (subError || !subscriptions || subscriptions.length === 0) {
    console.log('❌ No devices are subscribed to push notifications.');
    return;
  }

  // 3. Send the push notification
  for (const event of events) {
    const payload = JSON.stringify({ 
      title: `🚨 TryIT Alert: ${event.title}`, 
      body: event.description 
    });

    const promises = subscriptions.map(sub => {
      const pushSubscription = {
        endpoint: sub.endpoint,
        keys: { p256dh: sub.p256dh, auth: sub.auth }
      };

      return webpush.sendNotification(pushSubscription, payload).catch(err => {
        if (err.statusCode === 410 || err.statusCode === 404) {
          // Delete dead subscriptions
          return supabase.from('push_subscriptions').delete().eq('id', sub.id);
        }
        console.error('Error sending push:', err);
      });
    });

    await Promise.all(promises);

    // 4. Mark the event as notified
    await supabase.from('system_events').update({ notified: true }).eq('id', event.id);
  }

  console.log(`✅ Successfully sent notifications for ${events.length} events!`);
}

sendAutomatedAlerts();
