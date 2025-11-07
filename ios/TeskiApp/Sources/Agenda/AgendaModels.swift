import Foundation

struct AgendaPayload {
    let reviews: [AgendaReview]
    let blocks: [AgendaBlock]
}

struct AgendaReview: Identifiable, Codable {
    let id: UUID
    let memoryID: UUID
    let concept: String
    let dueAt: Date
}

struct AgendaBlock: Identifiable, Codable {
    enum Kind: String, Codable {
        case learn, review, drill, mock

        var localizedTitle: String {
            switch self {
            case .learn: return "Learn"
            case .review: return "Review"
            case .drill: return "Drill"
            case .mock: return "Mock"
            }
        }
    }

    let id: UUID
    let planID: UUID
    let topicID: UUID?
    let topic: String
    let minutes: Int
    let kind: Kind
    let status: String
}
