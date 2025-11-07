import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appModel: AppModel

    var body: some View {
        switch appModel.state {
        case .loading:
            ProgressView("Loading Teski…")
                .progressViewStyle(.circular)
        case .unauthenticated:
            SignInView()
        case .authenticated(let session):
            MainTabView(session: session)
        }
    }
}
