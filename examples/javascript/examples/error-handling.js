/**
 * Error handling examples for Triggers API client
 */

const TriggersAPIClient = require('../src/client');
const {
    TriggersAPIError,
    ValidationError,
    UnauthorizedError,
    NotFoundError,
    ConflictError,
} = require('../src/errors');

// Initialize client
const client = new TriggersAPIClient({
    apiKey: 'test-api-key-12345',
    baseUrl: 'http://localhost:8080'
});

async function main() {
    console.log('=== Error Handling Examples ===\n');

    // Example 1: Handling validation errors
    console.log('1. Validation Error Example');
    try {
        // This will fail because source is empty
        await client.createEvent({
            source: '', // Invalid: empty source
            eventType: 'test.event',
            payload: { test: 'data' }
        });
    } catch (error) {
        if (error instanceof ValidationError) {
            console.log(`   ✓ Caught ValidationError: ${error.message}`);
            console.log(`   Error Code: ${error.errorCode}`);
            if (error.details && Object.keys(error.details).length > 0) {
                console.log(`   Details:`, JSON.stringify(error.details, null, 2));
            }
        } else if (error instanceof TriggersAPIError) {
            console.log(`   ✓ Caught TriggersAPIError: ${error.message}`);
        }
    }

    // Example 2: Handling not found errors
    console.log('\n2. Not Found Error Example');
    try {
        // This will fail because event doesn't exist
        await client.getEvent('00000000-0000-0000-0000-000000000000');
    } catch (error) {
        if (error instanceof NotFoundError) {
            console.log(`   ✓ Caught NotFoundError: ${error.message}`);
            console.log(`   Error Code: ${error.errorCode}`);
            if (error.details && error.details.suggestion) {
                console.log(`   Suggestion: ${error.details.suggestion}`);
            }
        } else if (error instanceof TriggersAPIError) {
            console.log(`   ✓ Caught TriggersAPIError: ${error.message}`);
        }
    }

    // Example 3: Handling conflict errors
    console.log('\n3. Conflict Error Example');
    try {
        // First, create and acknowledge an event
        const event = await client.createEvent({
            source: 'test-app',
            eventType: 'test.event',
            payload: { test: 'data' }
        });
        // Acknowledge it
        await client.acknowledgeEvent(event.event_id);
        // Try to acknowledge again (this will cause a conflict)
        await client.acknowledgeEvent(event.event_id);
    } catch (error) {
        if (error instanceof ConflictError) {
            console.log(`   ✓ Caught ConflictError: ${error.message}`);
            console.log(`   Error Code: ${error.errorCode}`);
            if (error.details && error.details.current_status) {
                console.log(`   Current Status: ${error.details.current_status}`);
            }
        } else if (error instanceof TriggersAPIError) {
            console.log(`   ✓ Caught TriggersAPIError: ${error.message}`);
        }
    }

    // Example 4: Handling unauthorized errors
    console.log('\n4. Unauthorized Error Example');
    try {
        // Create a client with invalid API key
        const invalidClient = new TriggersAPIClient({
            apiKey: 'invalid-key',
            baseUrl: 'http://localhost:8080'
        });
        await invalidClient.getInbox();
    } catch (error) {
        if (error instanceof UnauthorizedError) {
            console.log(`   ✓ Caught UnauthorizedError: ${error.message}`);
            console.log(`   Error Code: ${error.errorCode}`);
        } else if (error instanceof TriggersAPIError) {
            console.log(`   ✓ Caught TriggersAPIError: ${error.message}`);
        }
    }

    // Example 5: Generic error handling
    console.log('\n5. Generic Error Handling Example');
    try {
        // Try to create an event with invalid data
        await client.createEvent({
            source: 'test',
            eventType: 'test',
            payload: {} // Invalid: empty payload
        });
    } catch (error) {
        if (error instanceof ValidationError) {
            console.log(`   ✓ Validation error: ${error.message}`);
        } else if (error instanceof TriggersAPIError) {
            // Catch-all for any API error
            console.log(`   ✓ API error: ${error.message}`);
            console.log(`   Status Code: ${error.statusCode}`);
            console.log(`   Error Code: ${error.errorCode}`);
            if (error.requestId) {
                console.log(`   Request ID: ${error.requestId}`);
            }
        }
    }

    // Example 6: Error handling with request ID tracking
    console.log('\n6. Error Handling with Request ID');
    try {
        await client.createEvent({
            source: '', // Invalid
            eventType: 'test',
            payload: { test: 'data' },
            requestId: 'my-custom-request-id-123'
        });
    } catch (error) {
        if (error instanceof ValidationError) {
            console.log(`   ✓ Error: ${error.message}`);
            if (error.requestId) {
                console.log(`   Request ID: ${error.requestId}`);
                console.log(`   You can use this request ID for support/debugging`);
            }
        }
    }

    console.log('\n=== Error Handling Examples Complete ===');
}

main().catch(error => {
    console.error('Unexpected error:', error);
    process.exit(1);
});

