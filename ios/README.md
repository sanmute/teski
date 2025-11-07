# Teski iOS App

This directory hosts the SwiftUI client for Teski. The project is organised as a Swift Package that can be opened in Xcode (`File → Open Package…`). We use SwiftUI, Swift Concurrency, and a modular folder structure to support rapid feature growth.

## Project Structure

```
ios/
 ├─ TeskiApp/
 │   ├─ Package.swift
 │   ├─ Sources/
 │   │   ├─ App/          # App entry point, session management, settings
 │   │   ├─ Agenda/       # Today agenda feature
 │   │   ├─ Planner/      # Exam planner feature stubs
 │   │   ├─ Memory/       # Memory review feature stubs
 │   │   ├─ Networking/   # API client abstractions
 │   │   └─ DesignSystem/ # Shared styling tokens
 │   └─ Tests/
 └─ README.md
```

## Getting Started

1. Open `ios/TeskiApp` in Xcode 15 or newer (`File → Open Package…`).
2. Select the **TeskiApp** scheme and run on an iOS 16+ simulator.
3. Configure the API base URL by updating `APIClient` when pointing at staging/production.
4. Replace the placeholder services (Keychain storage, stub planner/memory views) as backend endpoints become available.

## Next Steps

- Implement secure Keychain-backed `SessionStorage`.
- Flesh out agenda, planner, and memory view models with real networking + persistence.
- Add push notifications, background refresh, and widgets.
- Integrate fastlane for TestFlight deployment.

Happy shipping!
