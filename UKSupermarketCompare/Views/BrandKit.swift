import SwiftUI

enum BrandPalette {
    static let red = Color(red: 0.82, green: 0.12, blue: 0.20)
    static let blue = Color(red: 0.10, green: 0.34, blue: 0.74)
    static let navy = Color(red: 0.08, green: 0.16, blue: 0.31)
    static let sky = Color(red: 0.90, green: 0.94, blue: 1.0)
    static let cloud = Color(red: 0.97, green: 0.98, blue: 1.0)
    static let textPrimary = Color(red: 0.13, green: 0.16, blue: 0.23)
    static let textSecondary = Color(red: 0.37, green: 0.43, blue: 0.53)
    static let success = Color(red: 0.10, green: 0.58, blue: 0.33)
    static let warning = Color(red: 0.93, green: 0.57, blue: 0.12)
}

enum BrandTypography {
    static let hero = Font.system(.largeTitle, design: .rounded).weight(.bold)
    static let title = Font.system(.title3, design: .rounded).weight(.semibold)
    static let section = Font.system(.headline, design: .rounded).weight(.semibold)
    static let body = Font.system(.body, design: .rounded)
    static let caption = Font.system(.caption, design: .rounded)
}

struct BrandLogoView: View {
    var title: String = "UKSupermarketCompare"
    var subtitle: String = "Smart grocery savings"

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [BrandPalette.red, BrandPalette.blue],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 52, height: 52)

                Image(systemName: "basket.fill")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundStyle(.white)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(BrandTypography.title)
                    .foregroundStyle(BrandPalette.navy)
                Text(subtitle)
                    .font(BrandTypography.caption)
                    .foregroundStyle(BrandPalette.textSecondary)
            }
        }
    }
}

struct BrandPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(BrandTypography.section)
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [BrandPalette.red, BrandPalette.blue],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
            )
            .opacity(configuration.isPressed ? 0.9 : 1)
            .scaleEffect(configuration.isPressed ? 0.99 : 1)
    }
}

struct BrandSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(BrandTypography.section)
            .foregroundStyle(BrandPalette.blue)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(BrandPalette.blue.opacity(0.35), lineWidth: 1.5)
                    .background(
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .fill(.white)
                    )
            )
            .opacity(configuration.isPressed ? 0.9 : 1)
    }
}

struct BrandCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(.white)
                    .shadow(color: BrandPalette.blue.opacity(0.08), radius: 12, x: 0, y: 6)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(BrandPalette.blue.opacity(0.08), lineWidth: 1)
            )
    }
}

struct BrandBadge: View {
    let text: String
    var tint: Color = BrandPalette.blue

    var body: some View {
        Text(text)
            .font(BrandTypography.caption.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .foregroundStyle(tint)
            .background(tint.opacity(0.12))
            .clipShape(Capsule())
    }
}

struct BrandScreenBackground: ViewModifier {
    func body(content: Content) -> some View {
        content
            .scrollContentBackground(.hidden)
            .background(
                LinearGradient(
                    colors: [BrandPalette.cloud, BrandPalette.sky.opacity(0.7)],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
            )
    }
}

extension View {
    func brandScreenBackground() -> some View {
        modifier(BrandScreenBackground())
    }
}
