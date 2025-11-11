# Triggers API Go Client

Go client library for the Zapier Triggers API.

## Installation

```bash
go get github.com/zapier/triggers-api-client
```

## Usage

```go
package main

import (
    "fmt"
    "log"
    triggersapi "github.com/zapier/triggers-api-client"
)

func main() {
    client, err := triggersapi.NewClient(triggersapi.ClientOptions{
        APIKey: "your-api-key",
        BaseURL: "https://api.example.com",
        SigningSecret: "your-signing-secret", // Optional
    })
    if err != nil {
        log.Fatal(err)
    }

    // Create an event
    event, err := client.CreateEvent(triggersapi.CreateEventOptions{
        Source: "my-app",
        EventType: "user.created",
        Payload: map[string]interface{}{
            "user_id": "123",
            "name": "John Doe",
        },
    })
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Created event: %s\n", event.EventID)
}
```

## Features

- Full API coverage
- Request signing (HMAC) support
- Type-safe request/response types
- Error handling

## Documentation

See [API Documentation](../../docs/API.md) for complete API reference.

