/**
 * Basic usage examples for Triggers API client
 */

const TriggersAPIClient = require('../src/client');

// Initialize client
// For local development:
const client = new TriggersAPIClient({
    apiKey: 'test-api-key-12345',
    baseUrl: 'http://localhost:8080'
});

// For production:
// const client = new TriggersAPIClient({
//     apiKey: 'your-production-api-key',
//     baseUrl: 'https://your-api-url.com'
// });

async function main() {
    console.log('=== Creating an Event ===');
    // Create an event
    const event = await client.createEvent({
        source: 'my-app',
        eventType: 'user.created',
        payload: { userId: '123', name: 'John Doe', email: 'john@example.com' }
    });
    console.log(`Event created: ${event.event_id}`);
    console.log(`Status: ${event.status}`);
    console.log(`Created at: ${event.created_at}`);

    console.log('\n=== Getting Event Details ===');
    // Get event details
    const eventDetails = await client.getEvent(event.event_id);
    console.log(`Event ID: ${eventDetails.event_id}`);
    console.log(`Source: ${eventDetails.source}`);
    console.log(`Event Type: ${eventDetails.event_type}`);
    console.log(`Payload:`, JSON.stringify(eventDetails.payload, null, 2));
    console.log(`Status: ${eventDetails.status}`);

    console.log('\n=== Getting Inbox ===');
    // Get pending events
    const inbox = await client.getInbox({ limit: 10 });
    console.log(`Found ${inbox.events.length} pending events`);
    for (const event of inbox.events) {
        console.log(`  - ${event.event_id}: ${event.source}/${event.event_type}`);
    }

    console.log('\n=== Acknowledging an Event ===');
    // Acknowledge the event we created
    if (inbox.events.length > 0) {
        const firstEventId = inbox.events[0].event_id;
        const ack = await client.acknowledgeEvent(firstEventId);
        console.log(`Event ${ack.event_id} acknowledged`);
        console.log(`Acknowledged at: ${ack.acknowledged_at}`);
    }

    console.log('\n=== Deleting an Event ===');
    // Delete an event
    if (inbox.events.length > 0) {
        const eventToDelete = inbox.events[0].event_id;
        const result = await client.deleteEvent(eventToDelete);
        console.log(`Event ${result.event_id} deleted: ${result.message}`);
    }

    console.log('\n=== Example Complete ===');
}

main().catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
});

