import EventKit
import Foundation

struct CalendarEvent: Codable {
    let id: String
    let calendar: String
    let title: String
    let start: String
    let end: String
    let location: String?
    let all_day: Bool
    let source: String
}

struct CalendarBridgeOutput: Codable {
    let events: [CalendarEvent]
}

let dayCount = max(1, Int(CommandLine.arguments.dropFirst().first ?? "2") ?? 2)
let store = EKEventStore()
let semaphore = DispatchSemaphore(value: 0)
var granted = false
var authError: Error?

if #available(macOS 14.0, *) {
    store.requestFullAccessToEvents { ok, error in
        granted = ok
        authError = error
        semaphore.signal()
    }
} else {
    store.requestAccess(to: .event) { ok, error in
        granted = ok
        authError = error
        semaphore.signal()
    }
}

semaphore.wait()

if !granted {
    let message = authError?.localizedDescription ?? "Calendar access was not granted."
    FileHandle.standardError.write(message.data(using: .utf8)!)
    exit(2)
}

let calendar = Calendar.current
let now = Date()
let start = calendar.startOfDay(for: now)
guard let end = calendar.date(byAdding: .day, value: dayCount, to: start) else {
    FileHandle.standardError.write("Could not build date range.".data(using: .utf8)!)
    exit(3)
}

let predicate = store.predicateForEvents(withStart: start, end: end, calendars: nil)
let formatter = ISO8601DateFormatter()
formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

let events = store.events(matching: predicate)
    .sorted { $0.startDate < $1.startDate }
    .map { event in
        CalendarEvent(
            id: event.eventIdentifier ?? UUID().uuidString,
            calendar: event.calendar.title,
            title: event.title ?? "(untitled)",
            start: formatter.string(from: event.startDate),
            end: formatter.string(from: event.endDate),
            location: event.location?.isEmpty == false ? event.location : nil,
            all_day: event.isAllDay,
            source: "apple_calendar_eventkit"
        )
    }

let output = CalendarBridgeOutput(events: events)
let data = try JSONEncoder().encode(output)
FileHandle.standardOutput.write(data)
