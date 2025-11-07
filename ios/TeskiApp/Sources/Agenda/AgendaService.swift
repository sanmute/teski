import Foundation

protocol AgendaServiceProtocol {
    func fetchAgenda(force: Bool) async throws -> AgendaPayload
}

struct AgendaService: AgendaServiceProtocol {
    private let api: APIClientProtocol

    init(api: APIClientProtocol = APIClient.shared) {
        self.api = api
    }

    func fetchAgenda(force: Bool) async throws -> AgendaPayload {
        let response: AgendaResponseDTO = try await api.get(path: "/exam/agenda/today", queryItems: [])
        return response.toModel()
    }
}

private struct AgendaResponseDTO: Decodable {
    let reviews: [AgendaReviewDTO]
    let blocks: [AgendaBlockDTO]

    func toModel() -> AgendaPayload {
        AgendaPayload(
            reviews: reviews.map { $0.toModel() },
            blocks: blocks.map { $0.toModel() }
        )
    }
}

private struct AgendaReviewDTO: Decodable {
    let id: UUID
    let memory_id: UUID
    let concept: String
    let due_at: Date

    func toModel() -> AgendaReview {
        AgendaReview(id: id, memoryID: memory_id, concept: concept, dueAt: due_at)
    }
}

private struct AgendaBlockDTO: Decodable {
    let id: UUID
    let plan_id: UUID
    let topic_id: UUID?
    let topic: String
    let minutes: Int
    let kind: AgendaBlock.Kind
    let status: String

    func toModel() -> AgendaBlock {
        AgendaBlock(id: id, planID: plan_id, topicID: topic_id, topic: topic, minutes: minutes, kind: kind, status: status)
    }
}
