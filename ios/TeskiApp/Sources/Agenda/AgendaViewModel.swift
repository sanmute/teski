import Foundation

@MainActor
final class AgendaViewModel: ObservableObject {
    @Published private(set) var reviews: [AgendaReview] = []
    @Published private(set) var blocks: [AgendaBlock] = []

    private let agendaService: AgendaServiceProtocol

    init(agendaService: AgendaServiceProtocol = AgendaService()) {
        self.agendaService = agendaService
    }

    func loadAgenda(force: Bool = false) async {
        do {
            let data = try await agendaService.fetchAgenda(force: force)
            reviews = data.reviews
            blocks = data.blocks
        } catch {
            // TODO: surface error state
        }
    }
}
