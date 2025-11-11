/**
 * Complete event lifecycle example
 */

const TriggersAPIClient = require('../src/client');
const { TriggersAPIError } = require('../src/errors');

// Initialize client
const client = new TriggersAPIClient({
    apiKey: 'test-api-key-12345',
    baseUrl: 'http://localhost:8080'
});

async function main() {
    console.log('=== Complete Event Lifecycle Example ===\n');

    try {
        // Step 1: Create an event
        console.log('1. Creating event...');
        const event = await client.createEvent({
            source: 'workflow-app',
            eventType: 'task.completed',
            payload: {
                taskId: 'task-123',
                userId: 'user-456',
                completedAt: '2025-11-10T12:00:00Z'
            },
            metadata: {
                priority: 'high',
                correlation_id: 'workflow-789',
                idempotency_key: 'task-123-completed'
            }
        });
        console.log(`   ✓ Event created: ${event.event_id}`);
        console.log(`   Status: ${event.status}`);
        
        // Step 2: Get inbox to see the event
        console.log('\n2. Checking inbox...');
        const inbox = await client.getInbox({ limit: 50, source: 'workflow-app' });
        console.log(`   ✓ Found ${inbox.events.length} pending events from workflow-app`);
        
        // Step 3: Get full event details
        console.log('\n3. Getting event details...');
        const eventDetails = await client.getEvent(event.event_id);
        console.log(`   ✓ Event details retrieved`);
        console.log(`   Source: ${eventDetails.source}`);
        console.log(`   Type: ${eventDetails.event_type}`);
        console.log(`   Payload:`, JSON.stringify(eventDetails.payload, null, 2));
        console.log(`   Metadata:`, JSON.stringify(eventDetails.metadata, null, 2));
        
        // Step 4: Process the event (simulate processing)
        console.log('\n4. Processing event...');
        // In a real application, you would process the event here
        console.log(`   ✓ Processing event ${event.event_id}`);
        console.log(`   Task ID: ${eventDetails.payload.taskId}`);
        
        // Step 5: Acknowledge the event
        console.log('\n5. Acknowledging event...');
        const ack = await client.acknowledgeEvent(event.event_id);
        console.log(`   ✓ Event acknowledged`);
        console.log(`   Acknowledged at: ${ack.acknowledged_at}`);
        
        // Step 6: Verify event is acknowledged
        console.log('\n6. Verifying acknowledgment...');
        const updatedEvent = await client.getEvent(event.event_id);
        console.log(`   ✓ Event status: ${updatedEvent.status}`);
        console.log(`   Acknowledged at: ${updatedEvent.acknowledged_at}`);
        
        // Step 7: Clean up - delete the event
        console.log('\n7. Cleaning up...');
        const result = await client.deleteEvent(event.event_id);
        console.log(`   ✓ Event deleted: ${result.message}`);
        
        console.log('\n=== Event Lifecycle Complete ===');
        
    } catch (error) {
        if (error instanceof TriggersAPIError) {
            console.log(`\n✗ API Error: ${error.message}`);
            console.log(`   Error Code: ${error.errorCode}`);
            console.log(`   Status Code: ${error.statusCode}`);
            if (error.requestId) {
                console.log(`   Request ID: ${error.requestId}`);
            }
            if (error.details && Object.keys(error.details).length > 0) {
                console.log(`   Details:`, JSON.stringify(error.details, null, 2));
            }
        } else {
            console.error('Unexpected error:', error);
        }
        process.exit(1);
    }
}

main();

